from datetime import datetime
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("app.main")

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import models
from app.auth import (
    authenticate_user,
    create_access_token,
    ensure_default_user,
)
from app.config import settings
from app.db import SessionLocal, init_db
from app.drafter import draft_dm
from app.models import (
    Campaign,
    Draft,
    DraftStatus,
    Evidence,
    Interaction,
    MessageStatus,
    Prospect,
    ProspectStatus,
    SeedAccount,
    User,
)
from app.sender import send_approved_drafts
from app.tracker import (
    get_dashboard_stats,
    get_prospects_with_status,
    get_unanswered_replies,
    sync_inbound_replies,
)
from app.x_client import XClient, XAPIError

# DB init on startup
init_db()
ensure_default_user()

app = FastAPI(title="GenAIFund X Outreach Prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Auth & Credentials endpoints
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


class CredentialsUpdate(BaseModel):
    x_bearer_token: Optional[str] = None
    x_user_access_token: Optional[str] = None
    anthropic_api_key: Optional[str] = None


@app.post("/config/credentials")
def update_credentials(body: CredentialsUpdate):
    """Cập nhật credentials trong phiên chạy để không cần can thiệp file .env."""
    if body.x_bearer_token and body.x_bearer_token.strip():
        settings.x_bearer_token = body.x_bearer_token.strip()
    if body.x_user_access_token and body.x_user_access_token.strip():
        settings.x_user_access_token = body.x_user_access_token.strip()
    if body.anthropic_api_key and body.anthropic_api_key.strip():
        settings.anthropic_api_key = body.anthropic_api_key.strip()
    return {
        "status": "ok",
        "message": "Credentials updated successfully for current runtime.",
        "x_bearer_token_set": bool(settings.x_bearer_token),
        "x_user_access_token_set": bool(settings.x_user_access_token),
        "anthropic_api_key_set": bool(settings.anthropic_api_key),
    }


@app.get("/config/credentials/status")
def get_credentials_status():
    return {
        "x_bearer_token_set": bool(settings.x_bearer_token),
        "x_user_access_token_set": bool(settings.x_user_access_token),
        "anthropic_api_key_set": bool(settings.anthropic_api_key),
    }


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------
class CampaignCreate(BaseModel):
    name: str
    segment_description: Optional[str] = None
    max_sends_per_run: int = 25
    max_sends_per_day: int = 100
    cooldown_seconds: int = 90


@app.post("/campaigns")
def create_campaign(
    body: CampaignCreate, db: Session = Depends(get_db)
):
    campaign = Campaign(
        name=body.name,
        segment_description=body.segment_description,
        max_sends_per_run=body.max_sends_per_run,
        max_sends_per_day=body.max_sends_per_day,
        cooldown_seconds=body.cooldown_seconds,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@app.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    return db.query(Campaign).all()


# ---------------------------------------------------------------------------
# Seeds
# ---------------------------------------------------------------------------
class SeedCreate(BaseModel):
    username: str


@app.post("/campaigns/{campaign_id}/seeds")
def add_seed(
    campaign_id: int,
    body: SeedCreate,
    db: Session = Depends(get_db),
):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    seed = SeedAccount(
        campaign_id=campaign_id,
        username=body.username.strip().lstrip("@"),
        source="manual",
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    return seed


# ---------------------------------------------------------------------------
# Prospects / find
# ---------------------------------------------------------------------------
@app.post("/campaigns/{campaign_id}/find")
async def find_prospects(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    x_client = XClient()
    seeds = db.query(SeedAccount).filter(SeedAccount.campaign_id == campaign_id).all()
    if not seeds:
        return {"created": 0, "message": "No seed accounts found. Please add seeds first."}

    created = 0
    errors: List[str] = []

    for seed in seeds:
        try:
            user = await x_client.lookup_user_by_username(seed.username)
            if not user or not user.get("id"):
                errors.append(f"Could not resolve user @{seed.username}")
                continue
            seed_user_id = user.get("id")

            # Gather followers + following as candidate pool
            candidates: List[Dict[str, Any]] = []
            if seed_user_id:
                try:
                    candidates += await x_client.get_followers(seed_user_id)
                except Exception as exc:
                    logger.warning("Followers fetch error for @%s: %s", seed.username, exc)
                try:
                    candidates += await x_client.get_following(seed_user_id)
                except Exception as exc:
                    logger.warning("Following fetch error for @%s: %s", seed.username, exc)

            seen_usernames = set()
            for c in candidates:
                username = c.get("username")
                if not username or username in seen_usernames:
                    continue
                seen_usernames.add(username)

                # Skip if already a prospect in this campaign
                exists = (
                    db.query(Prospect)
                    .filter(Prospect.campaign_id == campaign_id)
                    .filter(Prospect.username == username)
                    .first()
                )
                if exists:
                    continue

                # Evidence + scoring
                evidence_result = await collect_evidence_for_prospect_fast(x_client, c)
                scored = score_prospect_logic(
                    evidence_result.get("bio", "") or "",
                    evidence_result.get("recent_posts", []),
                )

                prospect = Prospect(
                    campaign_id=campaign_id,
                    username=username,
                    display_name=c.get("name"),
                    bio=evidence_result.get("bio"),
                    source_seed_username=seed.username,
                    fit_score=scored["fit_score"],
                    fit_reason=scored["fit_reason"],
                    status=ProspectStatus.FOUND,
                )
                db.add(prospect)
                db.flush()

                evidence = Evidence(
                    prospect_id=prospect.id,
                    bio_text=evidence_result.get("bio"),
                    recent_posts_json=str(evidence_result.get("recent_posts", [])),
                    evidence_summary=evidence_result.get("evidence_summary"),
                )
                db.add(evidence)
                created += 1

        except XAPIError as exc:
            logger.warning("X API error for seed %s: %s", seed.username, exc)
            errors.append(f"X API error for @{seed.username}: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected error for seed %s: %s", seed.username, exc)
            errors.append(f"Error for @{seed.username}: {exc}")
            continue

    db.commit()
    return {"created": created, "errors": errors}


async def collect_evidence_for_prospect_fast(
    x_client: XClient, candidate: Dict[str, Any]
) -> Dict[str, Any]:
    username = candidate.get("username")
    user_id = candidate.get("id")
    recent_posts = []
    if user_id:
        try:
            recent_posts = await x_client.get_user_tweets(user_id, max_results=5)
        except Exception:
            recent_posts = []
    from app.evidence import summarize_evidence

    return {
        "user_id": user_id,
        "name": candidate.get("name"),
        "username": username,
        "bio": candidate.get("description"),
        "location": candidate.get("location"),
        "profile_image_url": candidate.get("profile_image_url"),
        "public_metrics": candidate.get("public_metrics"),
        "recent_posts": recent_posts,
        "evidence_summary": summarize_evidence(
            None, candidate.get("description") or "", recent_posts
        ),
    }


def score_prospect_logic(bio: str, recent_posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    from app.scorer import score_prospect

    return score_prospect(bio, recent_posts)


# ---------------------------------------------------------------------------
# Prospects list
# ---------------------------------------------------------------------------
@app.get("/campaigns/{campaign_id}/prospects")
def list_prospects(campaign_id: int, db: Session = Depends(get_db)):
    return get_prospects_with_status(db, campaign_id)


# ---------------------------------------------------------------------------
# Drafts
# ---------------------------------------------------------------------------
class DraftUpdate(BaseModel):
    dm_text: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None


@app.patch("/drafts/{draft_id}")
def update_draft(draft_id: int, body: DraftUpdate, db: Session = Depends(get_db)):
    """Cập nhật nội dung nháp hoặc trạng thái nháp."""
    draft = db.query(Draft).get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if body.dm_text is not None:
        draft.dm_text = body.dm_text.strip()

    if body.status is not None:
        new_status = body.status.lower()
        if new_status in ("approved", DraftStatus.APPROVED):
            draft.status = DraftStatus.APPROVED
            draft.approved_by = body.approved_by or "admin"
            draft.approved_at = datetime.utcnow()
            prospect = db.query(Prospect).get(draft.prospect_id)
            if prospect:
                prospect.status = ProspectStatus.APPROVED
                db.add(prospect)
        elif new_status in ("rejected", "failed", DraftStatus.FAILED):
            draft.status = DraftStatus.FAILED
            prospect = db.query(Prospect).get(draft.prospect_id)
            if prospect:
                prospect.status = ProspectStatus.REJECTED
                db.add(prospect)
        elif new_status in ("draft", DraftStatus.DRAFT):
            draft.status = DraftStatus.DRAFT

    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@app.post("/drafts/{draft_id}/generate")
def generate_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(Draft).get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    prospect = db.query(Prospect).get(draft.prospect_id)
    evidence = prospect.evidence if prospect else None
    evidence_summary = evidence.evidence_summary if evidence else ""
    result = draft_dm(evidence_summary, prospect.display_name or prospect.username)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    draft.dm_text = result["dm_text"]
    draft.evidence_used = evidence_summary
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@app.post("/prospects/{prospect_id}/draft")
def create_draft_for_prospect(prospect_id: int, db: Session = Depends(get_db)):
    prospect = db.query(Prospect).get(prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    evidence = prospect.evidence
    evidence_summary = evidence.evidence_summary if evidence else ""
    result = draft_dm(evidence_summary, prospect.display_name or prospect.username)

    # Check if a draft already exists for this prospect
    draft = db.query(Draft).filter(Draft.prospect_id == prospect.id).first()
    if draft:
        draft.dm_text = result["dm_text"]
        draft.evidence_used = evidence_summary
        draft.status = DraftStatus.DRAFT
    else:
        draft = Draft(
            prospect_id=prospect.id,
            campaign_id=prospect.campaign_id,
            dm_text=result["dm_text"],
            evidence_used=evidence_summary,
            status=DraftStatus.DRAFT,
        )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@app.post("/campaigns/{campaign_id}/draft-all")
def draft_all_for_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Tạo nháp DM hàng loạt cho tất cả các ứng viên trong chiến dịch chưa có nháp."""
    prospects = (
        db.query(Prospect)
        .filter(Prospect.campaign_id == campaign_id)
        .all()
    )
    count = 0
    for prospect in prospects:
        existing_draft = db.query(Draft).filter(Draft.prospect_id == prospect.id).first()
        if not existing_draft:
            evidence = prospect.evidence
            evidence_summary = evidence.evidence_summary if evidence else ""
            result = draft_dm(evidence_summary, prospect.display_name or prospect.username)
            draft = Draft(
                prospect_id=prospect.id,
                campaign_id=campaign_id,
                dm_text=result["dm_text"],
                evidence_used=evidence_summary,
                status=DraftStatus.DRAFT,
            )
            db.add(draft)
            count += 1
    db.commit()
    return {"created_drafts": count, "total_prospects": len(prospects)}


@app.patch("/drafts/{draft_id}/approve")
def approve_draft(draft_id: int, approved_by: str = "admin", db: Session = Depends(get_db)):
    draft = db.query(Draft).get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft.status = DraftStatus.APPROVED
    draft.approved_by = approved_by
    draft.approved_at = datetime.utcnow()
    prospect = db.query(Prospect).get(draft.prospect_id)
    if prospect:
        prospect.status = ProspectStatus.APPROVED
        db.add(prospect)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@app.patch("/drafts/{draft_id}/reject")
def reject_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(Draft).get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft.status = DraftStatus.FAILED
    prospect = db.query(Prospect).get(draft.prospect_id)
    if prospect:
        prospect.status = ProspectStatus.REJECTED
        db.add(prospect)
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------
@app.post("/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    x_client = XClient()
    return await send_approved_drafts(db, x_client, campaign_id)


# ---------------------------------------------------------------------------
# Stats / tracking / replies
# ---------------------------------------------------------------------------
@app.get("/campaigns/{campaign_id}/stats")
def stats(campaign_id: int, db: Session = Depends(get_db)):
    return get_dashboard_stats(db, campaign_id)


@app.get("/campaigns/{campaign_id}/replies")
def replies(campaign_id: int, db: Session = Depends(get_db)):
    return get_unanswered_replies(db, campaign_id)


@app.post("/campaigns/{campaign_id}/sync-replies")
async def sync_replies(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    x_client = XClient()
    return await sync_inbound_replies(db, x_client, campaign_id)


# ---------------------------------------------------------------------------
# Serve React static build (if present)
# ---------------------------------------------------------------------------
ui_dist = os.path.join(os.path.dirname(__file__), "..", "ui", "dist")
if os.path.isdir(ui_dist):
    app.mount("/", StaticFiles(directory=ui_dist, html=True), name="ui")
