from typing import Any, Dict, List

from app.models import Evidence, Prospect
from app.x_client import XClient


def summarize_evidence(
    prospect: Prospect, bio: str, recent_posts: List[Dict[str, Any]]
) -> str:
    parts: List[str] = []
    if bio:
        parts.append(f"Bio: {bio}")
    if recent_posts:
        posts_text = " | ".join(
            p.get("text", "") for p in recent_posts[:3] if p.get("text")
        )
        if posts_text:
            parts.append(f"Recent posts: {posts_text}")
    return " ".join(parts) or "No public profile text available."


async def collect_evidence_for_prospect(
    x_client: XClient, prospect: Prospect
) -> Dict[str, Any]:
    """Thu thập bằng chứng thực từ hồ sơ X công khai và bài viết gần đây."""
    user = await x_client.lookup_user_by_username(prospect.username)
    if not user:
        return {"error": "user_not_found"}

    user_id = user.get("id")
    prospect.display_name = user.get("name")
    prospect.bio = user.get("description")

    recent_posts: List[Dict[str, Any]] = []
    if user_id:
        recent_posts = await x_client.get_user_tweets(user_id, max_results=10)

    summary = summarize_evidence(prospect, prospect.bio or "", recent_posts)

    return {
        "user_id": user_id,
        "name": user.get("name"),
        "username": user.get("username"),
        "bio": user.get("description"),
        "location": user.get("location"),
        "profile_image_url": user.get("profile_image_url"),
        "public_metrics": user.get("public_metrics"),
        "recent_posts": recent_posts,
        "evidence_summary": summary,
    }
