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
        headers={"set-cookie": "__Secure-better-auth.session_token=session-token; Path=/; Secure; HttpOnly"},
        request=request,
    )
    cookie_only_response = httpx.Response(
        200,
        text="Login accepted",
        headers={"set-cookie": "__Secure-better-auth.session_token=session-token; Path=/; Secure; HttpOnly"},
        request=request,
    )
    json_only_response = httpx.Response(200, json={"token": "session-token"}, request=request)
    redirected_response = httpx.Response(
        302,
        json={"token": "session-token"},
        headers={"set-cookie": "__Secure-better-auth.session_token=session-token; Path=/; Secure; HttpOnly"},
        request=request,
    )
    alternate_cookie_response = httpx.Response(
        200,
        json={"token": "session-token"},
        headers={"set-cookie": "session_token=session-token; Path=/; HttpOnly"},
        request=request,
    )
    wrong_content_type_response = httpx.Response(
        200,
        text='{"token":"session-token"}',
        headers={
            "content-type": "text/plain",
            "set-cookie": "__Secure-better-auth.session_token=session-token; Path=/; Secure; HttpOnly",
        },
        request=request,
    )

    assert UrjaPortalClient._login_response_is_valid(valid_response) is True
    assert UrjaPortalClient._login_response_is_valid(cookie_only_response) is False
    assert UrjaPortalClient._login_response_is_valid(json_only_response) is False
    assert UrjaPortalClient._login_response_is_valid(redirected_response) is False
    assert UrjaPortalClient._login_response_is_valid(alternate_cookie_response) is False
    assert UrjaPortalClient._login_response_is_valid(wrong_content_type_response) is False


@pytest.mark.parametrize(
    "location",
    ("/login?next=/meters", "https://portal.example/login?next=/meters", "login"),
)
def test_login_redirect_detection_handles_relative_and_absolute_locations(location):
    request = httpx.Request("GET", "https://portal.example/meters")
    response = httpx.Response(302, headers={"location": location}, request=request)

    assert UrjaPortalClient._is_login_redirect(response) is True


def test_retry_login_redirect_is_reported_as_authentication_failure():
    async def exercise_retry():
        client = UrjaPortalClient(Settings(demo_mode=False))
        client._client.get = AsyncMock(
            side_effect=[
                httpx.Response(
                    302,
                    headers={"location": "/login?next=/meters"},
                    request=httpx.Request("GET", "https://portal.example/meters"),
                ),
                httpx.Response(
                    302,
                    headers={"location": "/login?next=/meters"},
                    request=httpx.Request("GET", "https://portal.example/meters"),
                ),
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


def test_unexpected_redirect_is_rejected():
    async def exercise_redirect():
        client = UrjaPortalClient(Settings(demo_mode=False))
        client._client.get = AsyncMock(
            return_value=httpx.Response(
                302,
                headers={"location": "/maintenance"},
                request=httpx.Request("GET", "https://portal.example/meters"),
            )
        )

        with pytest.raises(PortalError) as error:
            await client._request("/meters")

        assert error.value.status_code == 502
        await client.close()

    asyncio.run(exercise_redirect())


def test_reauthentication_timeout_is_reported_as_gateway_timeout():
    async def exercise_timeout():
        client = UrjaPortalClient(Settings(demo_mode=False))
        client._client.get = AsyncMock(
            side_effect=[
                httpx.Response(401, request=httpx.Request("GET", "https://portal.example/meters")),
                httpx.TimeoutException("timed out"),
            ]
        )
        client.login = AsyncMock()

        with pytest.raises(PortalError) as error:
            await client._request("/meters")

        assert error.value.status_code == 504
        await client.close()

    asyncio.run(exercise_timeout())