from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models import Draft, Interaction, MessageSent, Prospect, ProspectStatus
from app.x_client import XAPIError, XClient

logger = logging.getLogger("app.tracker")


def get_dashboard_stats(db: Session, campaign_id: int) -> Dict[str, Any]:
    total_prospects = (
        db.query(Prospect).filter(Prospect.campaign_id == campaign_id).count()
    )
    approved_drafts = (
        db.query(Draft)
        .filter(Draft.campaign_id == campaign_id)
        .filter(Draft.status == "approved")
        .count()
    )
    sent = (
        db.query(MessageSent)
        .filter(MessageSent.campaign_id == campaign_id)
        .filter(MessageSent.status == "sent")
        .count()
    )
    failed = (
        db.query(MessageSent)
        .filter(MessageSent.campaign_id == campaign_id)
        .filter(MessageSent.status == "failed")
        .count()
    )
    responded = (
        db.query(Interaction)
        .filter(Interaction.campaign_id == campaign_id)
        .filter(Interaction.type == "replied")
        .count()
    )
    needs_attention = (
        db.query(Interaction)
        .filter(Interaction.campaign_id == campaign_id)
        .filter(Interaction.needs_attention == True)  # noqa: E712
        .count()
    )
    return {
        "total_prospects": total_prospects,
        "approved_drafts": approved_drafts,
        "sent": sent,
        "failed": failed,
        "responded": responded,
        "needs_attention": needs_attention,
    }


def get_prospects_with_status(db: Session, campaign_id: int) -> List[Dict[str, Any]]:
    prospects = (
        db.query(Prospect).filter(Prospect.campaign_id == campaign_id).all()
    )
    rows: List[Dict[str, Any]] = []
    for p in prospects:
        draft = (
            db.query(Draft)
            .filter(Draft.prospect_id == p.id)
            .order_by(Draft.created_at.desc())
            .first()
        )
        sent = (
            db.query(MessageSent)
            .filter(MessageSent.prospect_id == p.id)
            .order_by(MessageSent.sent_at.desc())
            .first()
        )
        evidence = p.evidence
        rows.append(
            {
                "id": p.id,
                "draft_id": draft.id if draft else None,
                "username": p.username,
                "display_name": p.display_name,
                "bio": p.bio,
                "source_seed_username": p.source_seed_username,
                "fit_score": p.fit_score,
                "fit_reason": p.fit_reason,
                "status": p.status,
                "draft_status": draft.status if draft else None,
                "draft_text": draft.dm_text if draft else None,
                "evidence_used": draft.evidence_used if draft else (evidence.evidence_summary if evidence else None),
                "sent_status": sent.status if sent else None,
                "sent_error": sent.error if sent else None,
                "x_dm_id": sent.x_dm_id if sent else None,
            }
        )
    return rows


def get_unanswered_replies(db: Session, campaign_id: int) -> List[Dict[str, Any]]:
    since = datetime.utcnow() - timedelta(days=30)
    replies = (
        db.query(Interaction)
        .filter(Interaction.campaign_id == campaign_id)
        .filter(Interaction.type == "replied")
        .filter(Interaction.direction == "inbound")
        .filter(Interaction.occurred_at >= since)
        .order_by(Interaction.occurred_at.desc())
        .all()
    )
    result = []
    for r in replies:
        prospect = db.query(Prospect).get(r.prospect_id)
        result.append(
            {
                "id": r.id,
                "prospect_id": r.prospect_id,
                "username": prospect.username if prospect else "unknown",
                "display_name": prospect.display_name if prospect else "",
                "content_snippet": r.content_snippet,
                "occurred_at": r.occurred_at.strftime("%Y-%m-%d %H:%M:%S") if r.occurred_at else "",
                "needs_attention": r.needs_attention,
            }
        )
    return result


async def sync_inbound_replies(
    db: Session, x_client: XClient, campaign_id: int
) -> Dict[str, Any]:
    """Đồng bộ tin nhắn đến từ X API v2 và gắn cờ needs_attention."""
    if not x_client.user_access_token:
        return {
            "synced_count": 0,
            "message": "X_USER_ACCESS_TOKEN not set. Cannot fetch inbound DM events.",
        }

    try:
        my_user = await x_client.me()
        my_id = str(my_user.get("id") or "")

        events = await x_client.get_dm_events(max_results=50)
        synced_count = 0

        for event in events:
            sender_id = str(event.get("sender_id") or "")
            # Skip outbound messages sent by ourselves
            if my_id and sender_id == my_id:
                continue

            text = event.get("text") or ""
            created_at_str = event.get("created_at")
            event_id = event.get("id")

            # Check if this interaction was already logged
            existing = (
                db.query(Interaction)
                .filter(Interaction.campaign_id == campaign_id)
                .filter(Interaction.content_snippet == text[:150])
                .first()
            )
            if existing:
                continue

            # Find matching prospect in this campaign
            prospect = (
                db.query(Prospect)
                .filter(Prospect.campaign_id == campaign_id)
                .first()
            )
            if not prospect:
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
            db.add(prospect)
            synced_count += 1

        db.commit()
        return {
            "synced_count": synced_count,
            "message": f"Successfully synced {synced_count} inbound replies.",
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("Error syncing inbound replies: %s", exc)
        return {
            "synced_count": 0,
            "error": str(exc),
            "message": f"Failed to sync replies: {exc}",
        }
