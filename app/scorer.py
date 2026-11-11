import re
from typing import Any, Dict, List, Optional

AI_ROBOTICS_KEYWORDS = [
    # AI & models
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "deep learning",
    "llm",
    "generative ai",
    "genai",
    "foundation model",
    "foundation models",
    "multi-modal",
    "multimodal",
    "agent",
    "agents",
    "computer vision",
    # Robotics & Embodied AI
    "robotics",
    "robot",
    "robots",
    "embodied ai",
    "humanoid",
    "amr",
    "ros",
    "ros2",
    "automation",
    "manipulation",
    "vla",
    # Infra & Devtools
    "infra",
    "infrastructure",
    "developer tools",
    "devtools",
    "gpu",
    "inference",
    # Roles
    "founder",
    "co-founder",
    "builder",
    "researcher",
    "engineer",
    "cto",
    "startup",
    # Southeast Asia countries & tech hubs
    "southeast asia",
    "sea",
    "singapore",
    "indonesia",
    "jakarta",
    "bandung",
    "vietnam",
    "hanoi",
    "ho chi minh",
    "hcmc",
    "saigon",
    "thailand",
    "bangkok",
    "malaysia",
    "kuala lumpur",
    "philippines",
    "manila",
]

AI_SUBSET = {
    "ai", "artificial intelligence", "machine learning", "ml", "deep learning",
    "llm", "generative ai", "genai", "foundation model", "foundation models",
    "multi-modal", "multimodal", "agent", "agents", "computer vision",
    "robotics", "robot", "robots", "embodied ai", "humanoid", "amr", "ros",
    "ros2", "automation", "manipulation", "vla", "infra", "infrastructure",
    "developer tools", "devtools", "gpu", "inference"
}

ROLE_SUBSET = {
    "founder", "co-founder", "builder", "researcher", "engineer", "cto", "startup"
}

SEA_SUBSET = {
    "southeast asia", "sea", "singapore", "indonesia", "jakarta", "bandung",
    "vietnam", "hanoi", "ho chi minh", "hcmc", "saigon", "thailand",
    "bangkok", "malaysia", "kuala lumpur", "philippines", "manila"
}


def score_prospect(
    bio: str,
    recent_posts: List[Dict[str, Any]],
    location: Optional[str] = None,
) -> Dict[str, Any]:
    """Điểm phù hợp theo quy tắc dựa trên bio, bài viết gần đây và địa điểm."""
    text_parts: List[str] = []
    if bio:
        text_parts.append(bio)
    if location:
        text_parts.append(f"Location: {location}")
    for p in recent_posts:
        if isinstance(p, dict) and p.get("text"):
            text_parts.append(p["text"])
    combined = " ".join(text_parts).lower()

    matches: List[str] = []
    for kw in AI_ROBOTICS_KEYWORDS:
        pattern = r"\b" + re.escape(kw.lower()) + r"\b"
        if re.search(pattern, combined):
            matches.append(kw)

    # Tiered scoring
    score = 0
    reasons: List[str] = []
    ai_matches = [m for m in matches if m in AI_SUBSET]
    role_matches = [m for m in matches if m in ROLE_SUBSET]
    sea_matches = [m for m in matches if m in SEA_SUBSET]

    score += min(len(ai_matches) * 12, 45)
    score += min(len(role_matches) * 10, 25)
    score += min(len(sea_matches) * 10, 25)
    score += min(len(matches) * 2, 10)
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
