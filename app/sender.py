import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Draft, DraftStatus, Interaction, MessageSent, MessageStatus, Prospect, ProspectStatus
from app.x_client import XAPIError, XClient

logger = logging.getLogger("app.sender")


def has_already_sent(db: Session, prospect_id: int, username: Optional[str] = None) -> bool:
    """Kiểm tra đã từng gửi tin nhắn thành công cho prospect này hoặc username này chưa (tránh trùng lặp 100%)."""
    # 1. Check by prospect_id
    existing_id = (
        db.query(MessageSent)
        .filter(MessageSent.prospect_id == prospect_id)
        .filter(MessageSent.status == MessageStatus.SENT)
        .first()
    )
    if existing_id is not None:
        return True

    # 2. Check across all campaigns by username
    if username:
        existing_user = (
            db.query(MessageSent)
            .join(Prospect, MessageSent.prospect_id == Prospect.id)
            .filter(Prospect.username.ilike(username.strip()))
            .filter(MessageSent.status == MessageStatus.SENT)
            .first()
        )
        if existing_user is not None:
            return True

    return False


def can_send_more_today(db: Session, campaign_id: int) -> bool:
    """Kiểm tra giới hạn gửi trong ngày."""
    today_start = datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    count_today = (
        db.query(MessageSent)
        .filter(MessageSent.campaign_id == campaign_id)
        .filter(MessageSent.sent_at >= today_start)
        .filter(MessageSent.status == MessageStatus.SENT)
        .count()
    )
    return count_today < settings.max_sends_per_day


async def send_approved_drafts(
    db: Session,
    x_client: XClient,
    campaign_id: int,
    max_sends: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Gửi các nháp đã phê duyệt, hoàn toàn tránh trùng tin nhắn, tôn trọng giới hạn và cooldown."""
    max_sends = max_sends or settings.max_sends_per_run
    results: List[Dict[str, Any]] = []

    # Get approved drafts for this campaign
    drafts = (
        db.query(Draft)
        .filter(Draft.campaign_id == campaign_id)
        .filter(Draft.status == DraftStatus.APPROVED)
        .order_by(Draft.created_at.asc())
        .limit(max_sends)
        .all()
    )

    if not drafts:
        return results

    for draft in drafts:
        if not can_send_more_today(db, campaign_id):
            results.append(
                {
                    "draft_id": draft.id,
                    "prospect_id": draft.prospect_id,
                    "status": "blocked",
                    "reason": "daily_limit_reached",
                }
            )
            break

        prospect = db.query(Prospect).get(draft.prospect_id)
        if not prospect:
            continue

        # Dedup: never send twice to the same prospect or username
        if has_already_sent(db, prospect.id, prospect.username):
            draft.status = DraftStatus.SENT
            if not draft.sent_at:
                draft.sent_at = datetime.utcnow()
            prospect.status = ProspectStatus.SENT
            db.add(draft)
            db.add(prospect)
            db.commit()
            results.append(
                {
                    "draft_id": draft.id,
                    "prospect_id": prospect.id,
                    "username": prospect.username,
                    "status": "blocked",
                    "reason": "already_sent_duplicate_prevention",
                    "note": "Prospect previously received a DM; skipped to prevent duplicate sending.",
                }
            )
            continue

        if not x_client.user_access_token:
            # Clear limitation: explain that user access token is needed for automated sending
            err_msg = (
                "X_USER_ACCESS_TOKEN is missing or not provided. "
                "HR can copy-paste this approved draft to send manually from X, "
                "or connect an authorized user token with dm.write scope."
            )
            results.append(
                {
                    "draft_id": draft.id,
                    "prospect_id": prospect.id,
                    "username": prospect.username,
                    "status": "blocked",
                    "reason": "x_user_access_token_missing",
                    "manual_copy_text": draft.dm_text,
                    "message": err_msg,
                }
            )
            continue

        try:
            # Resolve recipient X user id from username
            user = await x_client.lookup_user_by_username(prospect.username)
            if not user or not user.get("id"):
                raise ValueError(f"Could not resolve X user id for @{prospect.username}")

            prospect.x_user_id = str(user.get("id"))
            if user.get("profile_image_url"):
                prospect.profile_image_url = user.get("profile_image_url")
            if user.get("location"):
                prospect.location = user.get("location")

            sent_res = await x_client.send_dm(user["id"], draft.dm_text)
            dm_id = sent_res.get("dm_event_id") or sent_res.get("id") or sent_res.get("dm_conversation_id")

            msg = MessageSent(
                prospect_id=prospect.id,
                campaign_id=campaign_id,
                dm_text=draft.dm_text,
                x_dm_id=dm_id,
                status=MessageStatus.SENT,
            )
            db.add(msg)

            draft.status = DraftStatus.SENT
            draft.sent_at = datetime.utcnow()
            db.add(draft)

            # Mark prospect as sent
            prospect.status = ProspectStatus.SENT
            db.add(prospect)

            # Log interaction
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
            db.commit()

            results.append(
                {
                    "draft_id": draft.id,
                    "prospect_id": prospect.id,
                    "username": prospect.username,
                    "status": "sent",
                    "x_dm_id": dm_id,
                }
            )

            # Cooldown between sends (avoid spam flag)
            if len(results) < len(drafts):
                await asyncio.sleep(min(settings.cooldown_seconds, 5))

        except Exception as exc:  # noqa: BLE001
            err_str = str(exc)
            logger.error("Send failed for prospect @%s: %s", prospect.username, err_str)

            # If X API Free tier restricts sending DMs (403 Forbidden), record actionable explanation
            if "403" in err_str:
                err_str = (
                    "X API tier limitation (HTTP 403): X Free/Basic tier may not permit automated DM sending. "
                    "Approved draft is preserved. HR can copy-paste and send directly via X app."
                )

            draft.status = DraftStatus.FAILED
            db.add(draft)
            msg = MessageSent(
                prospect_id=prospect.id,
                campaign_id=campaign_id,
                dm_text=draft.dm_text,
                status=MessageStatus.FAILED,
                error=err_str,
            )
            db.add(msg)
            db.commit()

            results.append(
                {
                    "draft_id": draft.id,
                    "prospect_id": prospect.id,
                    "username": prospect.username,
                    "status": "failed",
                    "error": err_str,
                    "manual_copy_text": draft.dm_text,
                }
            )

    return results
