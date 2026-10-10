from __future__ import annotations

import asyncio
from urllib.parse import urljoin, urlparse

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

    async def close(self) -> None:
        await self._client.aclose()

    async def logout(self) -> None:
        self._client.cookies.clear()
        self._authenticated = False

    @property
    def authenticated(self) -> bool:
        return self._authenticated

    @staticmethod
    def _login_response_is_valid(response: httpx.Response) -> bool:
        if response.status_code != 200:
            return False

        if UrjaPortalClient._is_login_redirect(response):
            return False

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return False

        try:
            payload = response.json()
        except ValueError:
            return False
        if not isinstance(payload, dict):
            return False

        return bool(response.cookies.get("__Secure-better-auth.session_token"))

    @staticmethod
    def _is_login_redirect(response: httpx.Response) -> bool:
        location = response.headers.get("location", "")
        if not location:
            return False
        try:
            base_url = str(response.request.url)
        except RuntimeError:
            base_url = "http://portal.invalid/"
        path = urlparse(urljoin(base_url, location)).path
        return path.rstrip("/") == "/login"

    async def login(self) -> None:
        username = self.settings.urja_username
        password = self.settings.urja_password
        if self.settings.demo_mode:
            self._authenticated = True
            return
        if not username or not password:
            raise PortalError("Portal credentials are not configured.", 503)
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

            if not UrjaPortalClient._login_response_is_valid(response):
                raise PortalError("The Urja portal rejected the configured credentials.", 401)

            self._authenticated = True

    async def get_html(self, path: str) -> str:
        await self.login()
        response = await self._request(path)
        return response.text

    async def get_json(self, path: str) -> dict[str, object]:
        await self.login()
        response = await self._request(path)
        if "application/json" not in response.headers.get("content-type", "").lower():
            raise PortalError("The Urja portal returned an unexpected data format.")
        try:
            payload = response.json()
        except ValueError as exc:
            raise PortalError("The Urja portal returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise PortalError("The Urja portal returned an unexpected data format.")
        return payload

    async def _request(self, path: str) -> httpx.Response:
        try:
            response = await self._client.get(path)
        except httpx.TimeoutException as exc:
            raise PortalError("The Urja portal timed out.", 504) from exc
        except httpx.HTTPError as exc:
            raise PortalError("The Urja portal could not be reached.", 502) from exc
        if response.status_code in (401, 403) or UrjaPortalClient._is_login_redirect(response):
            self._authenticated = False
            try:
                await self.login()
                response = await self._client.get(path)
            except httpx.TimeoutException as exc:
                raise PortalError("The Urja portal timed out during reauthentication.", 504) from exc
            except httpx.HTTPError as exc:
                raise PortalError("The Urja portal could not be reached during reauthentication.", 502) from exc
            if response.status_code in (401, 403) or UrjaPortalClient._is_login_redirect(response):
                self._authenticated = False
                raise PortalError("Portal authentication failed after retry.", 401)
        if response.status_code >= 400:
            raise PortalError("The Urja portal returned an upstream error.", 502)
        if 300 <= response.status_code < 400:
            raise PortalError("The Urja portal returned an unexpected redirect.", 502)
        return response

    async def request_health(self) -> bool:
        try:
            response = await self._client.get("/login")
            return response.status_code < 500
        except httpx.HTTPError:
            return False
