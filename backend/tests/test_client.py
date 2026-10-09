import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from app.client import PortalError, UrjaPortalClient
from app.core.config import Settings


def test_login_response_requires_json_and_session_cookie():
    request = httpx.Request("POST", "https://portal.example/login")
    valid_response = httpx.Response(
        200,
        json={"token": "session-token"},
        headers={"set-cookie": "session_token=session-token; Path=/; HttpOnly"},
        request=request,
    )
    cookie_only_response = httpx.Response(
        200,
        text="Login accepted",
        headers={"set-cookie": "session_token=session-token; Path=/; HttpOnly"},
        request=request,
    )
    json_only_response = httpx.Response(200, json={"token": "session-token"}, request=request)
    redirected_response = httpx.Response(
        302,
        json={"token": "session-token"},
        headers={"set-cookie": "session_token=session-token; Path=/; HttpOnly"},
        request=request,
    )

    assert UrjaPortalClient._login_response_is_valid(valid_response) is True
    assert UrjaPortalClient._login_response_is_valid(cookie_only_response) is False
    assert UrjaPortalClient._login_response_is_valid(json_only_response) is False
    assert UrjaPortalClient._login_response_is_valid(redirected_response) is False


def test_retry_login_redirect_is_reported_as_authentication_failure():
    async def exercise_retry():
        client = UrjaPortalClient(Settings(demo_mode=False))
        client._client.get = AsyncMock(
            side_effect=[
                httpx.Response(302, headers={"location": "/login"}),
                httpx.Response(302, headers={"location": "/login"}),
            ]
        )

        async def authenticate():
            client._authenticated = True

        client.login = AsyncMock(side_effect=authenticate)
        with pytest.raises(PortalError) as error:
            await client._request("/meters")

        assert error.value.status_code == 401
        assert client.authenticated is False
        assert client._client.get.await_count == 2
        client.login.assert_awaited_once()
        await client.close()

    asyncio.run(exercise_retry())