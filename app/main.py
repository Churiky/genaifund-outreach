from datetime import datetime
import logging
import os
import uuid
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
    MessageSent,
    MessageStatus,
    Prospect,
    ProspectStatus,
    SeedAccount,
    User,
)
from app.sender import has_already_sent, send_approved_drafts
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
# Realistic Demonstration Dataset (AI & Robotics Southeast Asia Ecosystem)
# Dùng cho chế độ thử nghiệm demo khi tài khoản X thuộc Free Tier
# ---------------------------------------------------------------------------
DEMO_CANDIDATES = [
    {
        "username": "alex_embodied",
        "name": "Alex Nguyen",
        "description": "Founding engineer @RoboticsVN. Building open-source foundation models for humanoid manipulation. Previously robotics researcher at NUS. Based in Hanoi & Singapore.",
        "location": "Hanoi / Singapore",
        "recent_posts": [
            {"text": "Excited to share our open-source vision-language-action (VLA) benchmark for robot arms in Southeast Asia!"},
            {"text": "Great to see the SEA embodied AI community gathering in Singapore next month."},
            {"text": "Fine-tuning multi-modal models for tactile feedback on low-cost hardware."}
        ]
    },
    {
        "username": "priya_devtools",
        "name": "Priya Sharma",
        "description": "Founder @DevAI_SG. Building GPU cluster orchestration and inference devtools for generative AI startups across Southeast Asia. Ex-Google Cloud.",
        "location": "Singapore",
        "recent_posts": [
            {"text": "Benchmark: running vLLM with speculative decoding on regional edge clusters drops TTFT by 45%."},
            {"text": "Southeast Asian AI builders need infrastructure that abstracts GPU scarcity away."},
            {"text": "Devtools are the highest leverage layer in generative AI right now."}
        ]
    },
    {
        "username": "budi_sea_ml",
        "name": "Budi Santoso",
        "description": "AI Researcher working on multi-modal LLMs and low-resource speech models at Bandung AI Lab. Contributor to open-source SEA AI benchmarks.",
        "location": "Bandung, Indonesia",
        "recent_posts": [
            {"text": "New pre-print: efficient tokenization strategies for Indonesian and regional dialects."},
            {"text": "Open-weights models running locally on robotics controllers will change edge automation in ASEAN."}
        ]
    },
    {
        "username": "charlotte_lim",
        "name": "Charlotte Lim",
        "description": "Co-founder & CTO at an autonomous robotics startup in Malaysia & Singapore. Developing AMR navigation and sensor fusion for automated logistics.",
        "location": "Kuala Lumpur / Singapore",
        "recent_posts": [
            {"text": "Deployed our 50th autonomous mobile robot (AMR) in regional fulfillment centers."},
            {"text": "Sensor fusion with solid-state LiDAR on ROS2: insights from 6 months of warehouse deployment."}
        ]
    },
    {
        "username": "thanh_vision_ai",
        "name": "Thanh Tran",
        "description": "Computer vision and embodied AI engineer. Building deep learning models for industrial defect inspection and robotic grasping in Vietnam.",
        "location": "Ho Chi Minh City, Vietnam",
        "recent_posts": [
            {"text": "Real-time 6D pose estimation running at 60fps on Jetson Orin Nano for robotic picking."},
            {"text": "Vietnam's AI engineering talent pool is accelerating incredibly fast."}
        ]
    }
]


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


@app.post("/campaigns/{campaign_id}/load-demo-data")
def load_demo_data(campaign_id: int, db: Session = Depends(get_db)):
    """Nạp dữ liệu mẫu ứng viên AI & Robotics Đông Nam Á chất lượng cao để chạy thử nghiệm đầy đủ."""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    from app.evidence import summarize_evidence

    # Ensure seed accounts exist
    seeds = ["0xCodila", "karpathy", "le_robot_ai"]
    for s in seeds:
        exist = db.query(SeedAccount).filter(SeedAccount.campaign_id == campaign_id, SeedAccount.username == s).first()
        if not exist:
            db.add(SeedAccount(campaign_id=campaign_id, username=s, source="demo"))
    db.commit()

    created = 0
    for c in DEMO_CANDIDATES:
        username = c["username"]
        exists = (
            db.query(Prospect)
            .filter(Prospect.campaign_id == campaign_id)
            .filter(Prospect.username == username)
            .first()
        )
        if exists:
            continue

        scored = score_prospect_logic(c["description"], c["recent_posts"])
        prospect = Prospect(
            campaign_id=campaign_id,
            username=username,
            display_name=c["name"],
            bio=c["description"],
            source_seed_username="0xCodila",
            fit_score=scored["fit_score"],
            fit_reason=scored["fit_reason"],
            status=ProspectStatus.FOUND,
        )
        db.add(prospect)
        db.flush()

        evidence_summary = summarize_evidence(None, c["description"], c["recent_posts"])
        evidence = Evidence(
            prospect_id=prospect.id,
            bio_text=c["description"],
            recent_posts_json=str(c["recent_posts"]),
            evidence_summary=evidence_summary,
        )
        db.add(evidence)
        created += 1

    db.commit()
    return {
        "created": created,
        "message": f"Đã nạp thành công {created} ứng viên AI & Robotics Đông Nam Á kèm bằng chứng thực và điểm phù hợp."
    }


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


@app.post("/campaigns/{campaign_id}/simulate-send")
def simulate_send_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Mô phỏng gửi tin nhắn đã duyệt an toàn (dành cho chế độ Demo / X API Free tier)."""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    drafts = (
        db.query(Draft)
        .filter(Draft.campaign_id == campaign_id)
        .filter(Draft.status == DraftStatus.APPROVED)
        .order_by(Draft.created_at.asc())
        .limit(campaign.max_sends_per_run)
        .all()
    )

    results = []
    for draft in drafts:
        prospect = db.query(Prospect).get(draft.prospect_id)
        if not prospect:
            continue

        if has_already_sent(db, prospect.id, prospect.username):
            results.append({
                "draft_id": draft.id,
                "prospect_id": prospect.id,
                "username": prospect.username,
                "status": "blocked",
                "reason": "already_sent_duplicate_prevention",
            })
            continue

        mock_dm_id = f"mock_dm_{uuid.uuid4().hex[:10]}"
        msg = MessageSent(
            prospect_id=prospect.id,
            campaign_id=campaign_id,
            dm_text=draft.dm_text,
            x_dm_id=mock_dm_id,
            status=MessageStatus.SENT,
        )
        db.add(msg)

        draft.status = DraftStatus.SENT
        draft.sent_at = datetime.utcnow()
        prospect.status = ProspectStatus.SENT

        db.add(
            Interaction(
                prospect_id=prospect.id,
                campaign_id=campaign_id,
                type="sent",
                direction="outbound",
                content_snippet=draft.dm_text[:120],
                needs_attention=False,
            )
        )
        results.append({
            "draft_id": draft.id,
            "prospect_id": prospect.id,
            "username": prospect.username,
            "status": "sent",
            "x_dm_id": mock_dm_id,
            "note": "Demo simulated send (X Free tier mode)",
        })

    db.commit()
    return results


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


@app.post("/campaigns/{campaign_id}/simulate-replies")
def simulate_replies(campaign_id: int, db: Session = Depends(get_db)):
    """Mô phỏng tin nhắn phản hồi thực tế từ các ứng viên đã gửi để kiểm thử Hộp thư phản hồi."""
    campaign = db.query(Campaign).get(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    sent_prospects = (
        db.query(Prospect)
        .filter(Prospect.campaign_id == campaign_id)
        .all()
    )
    if not sent_prospects:
        return {"synced_count": 0, "message": "Chưa có ứng viên nào trong chiến dịch để mô phỏng phản hồi."}

    sample_replies = [
        "Hey! Thanks so much for reaching out. We are actually raising our seed round for our embodied AI pipeline in Singapore. Would love to hop on a quick call next Tuesday!",
        "Hi there! Saw what GenAI Fund has been doing across SEA. We just open-sourced our robotics devtools benchmark. Happy to connect and share more details.",
        "Thanks for the note! Always excited to connect with regional AI ecosystems. What stage does GenAI Fund typically look at?",
    ]

    synced = 0
    for i, prospect in enumerate(sent_prospects[:3]):
        text = sample_replies[i % len(sample_replies)]
        existing = (
            db.query(Interaction)
            .filter(Interaction.prospect_id == prospect.id)
            .filter(Interaction.type == "replied")
            .first()
        )
        if existing:
            continue

        interaction = Interaction(
            prospect_id=prospect.id,
            campaign_id=campaign_id,
            type="replied",
            direction="inbound",
            content_snippet=text,
            needs_attention=True,
            occurred_at=datetime.utcnow(),
        )
        db.add(interaction)
        prospect.status = ProspectStatus.RESPONDED
        synced += 1

    db.commit()
    return {
        "synced_count": synced,
        "message": f"Đã mô phỏng thành công {synced} phản hồi thực tế với nhãn 'Cần trả lời'."
    }


# ---------------------------------------------------------------------------
# Serve React static build (if present)
# ---------------------------------------------------------------------------
ui_dist = os.path.join(os.path.dirname(__file__), "..", "ui", "dist")
if os.path.isdir(ui_dist):
    app.mount("/", StaticFiles(directory=ui_dist, html=True), name="ui")
