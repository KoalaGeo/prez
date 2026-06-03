"""Regression tests for empty / missing Accept headers.

See https://github.com/RDFLib/prez/issues/380 and the v4 fix in
https://github.com/RDFLib/prez/pull/318.

Before the fix, a request with no Accept header caused
``get_requested_profile_and_mediatype`` to call ``frozenset(None)``, raising
``TypeError`` and returning HTTP 500. An empty Accept header (``Accept:``)
returned a placeholder ``(1, "")`` mediatype that matched no profile.

These are fast unit tests: they do not need a triplestore, only a minimal
stand-in for the Starlette/FastAPI ``Request`` object.
"""

import pytest

from prez.services.connegp_service import get_requested_profile_and_mediatype


class _FakeHeaders:
    def __init__(self, data):
        self._data = data

    def get(self, key, default=None):
        return self._data.get(key, default)


class _FakeRequest:
    """Minimal stand-in for starlette.requests.Request for connegp."""

    def __init__(self, headers=None, query_params=None):
        self.headers = _FakeHeaders(headers or {})
        self.query_params = query_params or {}


@pytest.mark.parametrize(
    "headers",
    [
        {},                 # no Accept header at all (was: frozenset(None) -> 500)
        {"Accept": ""},     # empty Accept header (Postman / Hopscotch)
        {"Accept": "   "},  # whitespace-only Accept header
    ],
)
def test_empty_or_missing_accept_header_returns_no_mediatypes(headers):
    _, _, requested_mediatypes = get_requested_profile_and_mediatype(
        _FakeRequest(headers=headers)
    )
    # No exception, and treated as "no mediatype requested" so conneg falls
    # back to the default profile/mediatype downstream.
    assert requested_mediatypes == frozenset()


def test_normal_accept_header_is_preserved():
    _, _, requested_mediatypes = get_requested_profile_and_mediatype(
        _FakeRequest(headers={"Accept": "text/turtle,application/json;q=0.9"})
    )
    assert requested_mediatypes == frozenset(
        {(1, "text/turtle"), (0.9, "application/json")}
    )


def test_wildcard_accept_header_is_preserved():
    _, _, requested_mediatypes = get_requested_profile_and_mediatype(
        _FakeRequest(headers={"Accept": "*/*"})
    )
    assert requested_mediatypes == frozenset({(1, "*/*")})