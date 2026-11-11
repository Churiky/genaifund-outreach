import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("app.x_client")

BASE_URL = "https://api.twitter.com/2"


class XAPIError(Exception):
    pass


class XClient:
    def __init__(
        self,
        bearer_token: Optional[str] = None,
        user_access_token: Optional[str] = None,
    ):
        self.bearer_token = bearer_token or settings.x_bearer_token
        self.user_access_token = user_access_token or settings.x_user_access_token

    def _headers(self, user_token: bool = False) -> Dict[str, str]:
        if user_token and self.user_access_token:
            return {"Authorization": f"Bearer {self.user_access_token}"}
        return {"Authorization": f"Bearer {self.bearer_token}"}

    async def _get(self, path: str, params: Optional[Dict] = None, user_token: bool = False) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(
                    f"{BASE_URL}{path}",
                    headers=self._headers(user_token=user_token),
                    params=params,
                )
            except httpx.RequestError as exc:
                logger.error("X API request error: %s", exc)
                raise XAPIError(str(exc))
        if resp.status_code >= 400:
            logger.error("X API error %s: %s", resp.status_code, resp.text)
            raise XAPIError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()

    async def _post(
        self, path: str, json: Optional[Dict] = None, user_token: bool = True
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{BASE_URL}{path}",
                    headers=self._headers(user_token=user_token),
                    json=json,
                )
            except httpx.RequestError as exc:
                logger.error("X API request error: %s", exc)
                raise XAPIError(str(exc))
        if resp.status_code >= 400:
            logger.error("X API error %s: %s", resp.status_code, resp.text)
            raise XAPIError(f"HTTP {resp.status_code}: {resp.text}")
        return resp.json()

    async def me(self) -> Dict[str, Any]:
        data = await self._get(
            "/users/me",
            params={"user.fields": "username,name,description,profile_image_url,public_metrics,location"},
            user_token=True,
        )
        return data.get("data", {})

    async def lookup_user_by_username(self, username: str) -> Dict[str, Any]:
        clean_user = username.strip().lstrip("@")
        data = await self._get(
            f"/users/by/username/{clean_user}",
            params={"user.fields": "username,name,description,profile_image_url,public_metrics,location"},
            user_token=True,
        )
        return data.get("data", {})

    async def lookup_user_by_id(self, user_id: str) -> Dict[str, Any]:
        data = await self._get(
            f"/users/{user_id}",
            params={"user.fields": "username,name,description,profile_image_url,public_metrics,location"},
            user_token=True,
        )
        return data.get("data", {})

    async def get_followers(self, user_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        data = await self._get(
            f"/users/{user_id}/followers",
            params={"max_results": min(max_results, 100), "user.fields": "username,name,description,profile_image_url,public_metrics,location"},
            user_token=True,
        )
        return data.get("data", [])

    async def get_following(self, user_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        data = await self._get(
            f"/users/{user_id}/following",
            params={"max_results": min(max_results, 100), "user.fields": "username,name,description,profile_image_url,public_metrics,location"},
            user_token=True,
        )
        return data.get("data", [])

    async def get_user_tweets(
        self, user_id: str, max_results: int = 10
    ) -> List[Dict[str, Any]]:
        data = await self._get(
            f"/users/{user_id}/tweets",
            params={
                "max_results": min(max_results, 10),
                "tweet.fields": "created_at,text,public_metrics",
            },
            user_token=True,
        )
        return data.get("data", [])

    async def send_dm(self, recipient_id: str, text: str) -> Dict[str, Any]:
        payload = {"text": text}
        data = await self._post(
            f"/dm_conversations/with/{recipient_id}/messages",
            json=payload,
            user_token=True,
        )
        return data.get("data", {})

    async def get_dm_events(self, max_results: int = 100) -> List[Dict[str, Any]]:
        data = await self._get(
            "/dm_events",
            params={
                "max_results": min(max_results, 100),
                "event_types": "MessageCreate",
                "dm_event.fields": "id,text,created_at,sender_id,dm_conversation_id",
            },
            user_token=True,
        )
        return data.get("data", [])
