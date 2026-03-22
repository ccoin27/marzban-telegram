from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx


class MarzbanError(Exception):
    def __init__(self, message: str, status: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.body = body


class MarzbanClient:
    def __init__(self, base_url: str, username: str, password: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._token: Optional[str] = None
        self._lock = asyncio.Lock()

    async def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, verify=False)

    async def close(self) -> None:
        pass

    async def _fetch_token(self) -> str:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, verify=False) as c:
            r = await c.post(
                "/api/admin/token",
                data={"username": self.username, "password": self.password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if r.status_code >= 400:
            raise MarzbanError("auth failed", r.status_code, r.text)
        data = r.json()
        tok = data.get("access_token")
        if not tok:
            raise MarzbanError("no access_token in response", r.status_code, r.text)
        return str(tok)

    async def token(self) -> str:
        async with self._lock:
            if not self._token:
                self._token = await self._fetch_token()
            return self._token

    async def invalidate_token(self) -> None:
        async with self._lock:
            self._token = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: Any = None,
        retry_auth: bool = True,
    ) -> httpx.Response:
        tok = await self.token()
        headers = {"Authorization": f"Bearer {tok}"}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, verify=False) as c:
            r = await c.request(method, path, params=params, json=json, headers=headers)
        if r.status_code == 401 and retry_auth:
            await self.invalidate_token()
            tok = await self.token()
            headers = {"Authorization": f"Bearer {tok}"}
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout, verify=False) as c:
                r = await c.request(method, path, params=params, json=json, headers=headers)
        return r

    async def get_json(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        r = await self._request("GET", path, params=params)
        if r.status_code >= 400:
            raise MarzbanError(r.text or "request failed", r.status_code, r.text)
        if not r.content:
            return None
        return r.json()

    async def post_json(self, path: str, json: Any = None) -> Any:
        r = await self._request("POST", path, json=json)
        if r.status_code >= 400:
            raise MarzbanError(r.text or "request failed", r.status_code, r.text)
        if not r.content:
            return {}
        return r.json()

    async def put_json(self, path: str, json: Any = None) -> Any:
        r = await self._request("PUT", path, json=json)
        if r.status_code >= 400:
            raise MarzbanError(r.text or "request failed", r.status_code, r.text)
        if not r.content:
            return {}
        return r.json()

    async def delete(self, path: str) -> Any:
        r = await self._request("DELETE", path)
        if r.status_code >= 400:
            raise MarzbanError(r.text or "request failed", r.status_code, r.text)
        if not r.content:
            return {}
        return r.json()

    async def system_stats(self) -> dict[str, Any]:
        return await self.get_json("/api/system")

    async def inbounds(self) -> dict[str, Any]:
        return await self.get_json("/api/inbounds")

    async def users(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"offset": offset, "limit": limit}
        if search:
            params["search"] = search
        if status:
            params["status"] = status
        return await self.get_json("/api/users", params=params)

    async def fetch_all_users(
        self,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
        batch_size: int = 300,
    ) -> list[dict[str, Any]]:
        first = await self.users(offset=0, limit=batch_size, search=search, status=status)
        total = int(first.get("total") or 0)
        acc: list[dict[str, Any]] = list(first.get("users") or [])
        while len(acc) < total:
            chunk = await self.users(
                offset=len(acc),
                limit=batch_size,
                search=search,
                status=status,
            )
            part = list(chunk.get("users") or [])
            if not part:
                break
            acc.extend(part)
        return acc

    async def user(self, username: str) -> dict[str, Any]:
        return await self.get_json(f"/api/user/{username}")

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.post_json("/api/user", json=payload)

    async def modify_user(self, username: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.put_json(f"/api/user/{username}", json=payload)

    async def delete_user(self, username: str) -> dict[str, Any]:
        return await self.delete(f"/api/user/{username}")

    async def reset_user_usage(self, username: str) -> dict[str, Any]:
        return await self.post_json(f"/api/user/{username}/reset")

    async def revoke_subscription(self, username: str) -> dict[str, Any]:
        return await self.post_json(f"/api/user/{username}/revoke_sub")

    async def admins(self, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        return await self.get_json("/api/admins", params={"offset": offset, "limit": limit})

    async def current_admin(self) -> dict[str, Any]:
        return await self.get_json("/api/admin")

    async def restart_core(self) -> Any:
        return await self.post_json("/api/core/restart")

    async def nodes(self) -> Any:
        return await self.get_json("/api/nodes")
