import re
from typing import Any, Dict, List

AI_ROBOTICS_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "deep learning",
    "llm",
    "generative ai",
    "robotics",
    "robot",
    "embodied ai",
    "automation",
    "founder",
    "builder",
    "researcher",
    "engineer",
    "infra",
    "infrastructure",
    "developer tools",
    "devtools",
    "startup",
    "southeast asia",
    "singapore",
    "indonesia",
    "vietnam",
    "thailand",
    "malaysia",
    "philippines",
    "sea",
]


def score_prospect(
    bio: str, recent_posts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Điểm phù hợp theo quy tắc dựa trên bio và bài viết gần đây. Không là guess."""
    text_parts: List[str] = []
    if bio:
        text_parts.append(bio)
    for p in recent_posts:
        if p.get("text"):
            text_parts.append(p["text"])
    combined = " ".join(text_parts).lower()

    matches: List[str] = []
    for kw in AI_ROBOTICS_KEYWORDS:
        if re.search(r"\b" + re.escape(kw.lower()) + r"\b", combined):
            matches.append(kw)

    # Tiered scoring: keyword presence + SEA indicator + founder/builder role
    score = 0
    reasons: List[str] = []
    ai_matches = [m for m in matches if m in ("ai", "artificial intelligence", "machine learning", "ml", "deep learning", "llm", "generative ai", "robotics", "robot", "embodied ai", "automation")]
    role_matches = [m for m in matches if m in ("founder", "builder", "researcher", "engineer", "startup")]
    sea_matches = [m for m in matches if m in ("southeast asia", "singapore", "indonesia", "vietnam", "thailand", "malaysia", "philippines", "sea")]

    score += min(len(ai_matches) * 10, 40)
    score += min(len(role_matches) * 8, 24)
    score += min(len(sea_matches) * 6, 18)
    score += min(len(matches) * 2, 18)
    score = min(score, 100)

    if ai_matches:
        reasons.append(f"AI/robotics keywords: {', '.join(ai_matches[:3])}")
    if role_matches:
        reasons.append(f"Role: {', '.join(role_matches[:3])}")
    if sea_matches:
        reasons.append(f"SEA signal: {', '.join(sea_matches[:3])}")
    if not reasons:
        reasons.append("No strong keyword match in public profile text.")

    return {
        "fit_score": score,
        "fit_reason": ". ".join(reasons),
        "matched_keywords": matches,
    }
