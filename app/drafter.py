import logging
import re
from typing import Any, Dict, Optional

from app.config import settings

logger = logging.getLogger("app.drafter")

SYSTEM_PROMPT = (
    "You are an outreach assistant for GenAI Fund, an AI/robotics ecosystem builder in Southeast Asia. "
    "Write a short, warm, personalised X DM (under 240 characters) from our fund's account "
    "to an AI/robotics builder or researcher. Use ONLY the real evidence provided — do not invent familiarity, "
    "mutual friends, events, or praise that is not in the evidence. Keep it human, specific, and low-pressure. "
    "End with a soft, easy-to-reply ask. Output ONLY the DM text, nothing else."
)


def _generate_rule_based_draft(evidence_summary: str, prospect_name: str) -> str:
    """Fallback cá nhân hóa theo bằng chứng thực tế khi chưa có Anthropic API key."""
    # Trích xuất từ khóa chủ đề từ bằng chứng
    evidence_lower = (evidence_summary or "").lower()
    topic = "AI & robotics"
    if "robot" in evidence_lower or "embodied" in evidence_lower:
        topic = "robotics & embodied AI"
    elif "llm" in evidence_lower or "generative" in evidence_lower:
        topic = "GenAI & LLM applications"
    elif "infra" in evidence_lower or "devtools" in evidence_lower or "tools" in evidence_lower:
        topic = "AI infrastructure & devtools"
    elif "research" in evidence_lower or "model" in evidence_lower:
        topic = "AI research & models"

    # Lấy tên hiển thị sạch
    clean_name = prospect_name.split()[0] if prospect_name else "there"
    clean_name = re.sub(r"[^\w\s]", "", clean_name).strip() or "there"

    return (
        f"Hi {clean_name}, saw your work around {topic} in the region. "
        f"We're building AI ecosystems at GenAI Fund across SEA and would love to connect and follow your journey. "
        f"Open to a quick exchange sometime?"
    )


def draft_dm(
    evidence_summary: str,
    prospect_name: str,
    anthropic_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Soạn nháp DM cá nhân hóa từ bằng chứng thực. Không bịa đặt."""
    api_key = anthropic_key or settings.anthropic_api_key

    if not api_key:
        fallback_text = _generate_rule_based_draft(evidence_summary, prospect_name)
        return {
            "dm_text": fallback_text,
            "error": None,
            "model_used": "evidence-rule-based (set ANTHROPIC_API_KEY for Claude)",
        }

    user_prompt = (
        f"Prospect name: {prospect_name}\n"
        f"Real evidence: {evidence_summary}\n"
        f"Write the DM text now."
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        # Use Claude 3.5 Sonnet / Haiku
        model_name = "claude-3-5-sonnet-20241022"
        response = client.messages.create(
            model=model_name,
            max_tokens=160,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        dm_text = response.content[0].text.strip() if response.content else ""
        return {"dm_text": dm_text, "error": None, "model_used": model_name}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Anthropic drafting error (%s), using evidence fallback", exc)
        fallback_text = _generate_rule_based_draft(evidence_summary, prospect_name)
        return {
            "dm_text": fallback_text,
            "error": None,
            "model_used": f"evidence-rule-based (Claude fallback: {str(exc)[:60]})",
        }
