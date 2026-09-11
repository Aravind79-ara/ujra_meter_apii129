from __future__ import annotations

import asyncio

import httpx

from app.core.config import Settings


class PortalError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class UrjaPortalClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(base_url=settings.urja_base_url.rstrip("/"), timeout=settings.request_timeout, follow_redirects=False)
        self._auth_lock = asyncio.Lock()
        self._authenticated = False
        self._username = settings.urja_username
        self._password = settings.urja_password

    async def close(self) -> None:
        await self._client.aclose()

    async def logout(self) -> None:
        self._client.cookies.clear()
        self._authenticated = False
        self._username = ""
        self._password = ""

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    async def login(self, username: str | None = None, password: str | None = None) -> None:
        username = username or self._username
        password = password or self._password
        if self.settings.demo_mode:
            if not username or not password:
                raise PortalError("Username and password are required.", 400)
            self._authenticated = True
            return
        if not username or not password:
            raise PortalError("Portal credentials are not configured.", 503)
        self._username = username
        self._password = password
        async with self._auth_lock:
            if self._authenticated:
                return
            try:
                login_headers = {
                    "Origin": self.settings.urja_base_url,
                    "Referer": f"{self.settings.urja_base_url.rstrip('/')}/login",
                    "User-Agent": "Mozilla/5.0 (compatible; UrjaMeterOpsAdapter/1.0)",
                }
                await self._client.get("/login", headers={"User-Agent": login_headers["User-Agent"]})
                response = await self._client.post(
                    "/login",
                    data={"email": username, "password": password},
                    headers={**login_headers, "Content-Type": "application/x-www-form-urlencoded"},
                )
            except httpx.TimeoutException as exc:
                raise PortalError("The Urja portal timed out during login.", 504) from exc
            except httpx.HTTPError as exc:
                raise PortalError("The Urja portal could not be reached.", 502) from exc
            if response.status_code >= 400:
                raise PortalError("The Urja portal rejected the configured credentials.", 401 if response.status_code in (401, 403) else 502)
            self._authenticated = True

    async def get_html(self, path: str) -> str:
        await self.login()
        response = await self._request(path)
        return response.text

    async def _request(self, path: str) -> httpx.Response:
        try:
            response = await self._client.get(path)
        except httpx.TimeoutException as exc:
            raise PortalError("The Urja portal timed out.", 504) from exc
        except httpx.HTTPError as exc:
            raise PortalError("The Urja portal could not be reached.", 502) from exc
        if response.status_code in (401, 403) or response.headers.get("location", "").endswith("/login"):
            self._authenticated = False
            await self.login()
            response = await self._client.get(path)
        if response.status_code >= 400:
            raise PortalError("The Urja portal returned an upstream error.", 502)
        return response

    async def request_health(self) -> bool:
        try:
            response = await self._client.get("/login")
            return response.status_code < 500
        except httpx.HTTPError:
            return False
