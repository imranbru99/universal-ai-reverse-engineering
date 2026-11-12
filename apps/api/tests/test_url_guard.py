import pytest

from app.security.url_guard import UrlGuardError, assert_in_scope, host_allowed, validate_public_http_url


def test_blocks_localhost_ip_literal():
    with pytest.raises(UrlGuardError):
        validate_public_http_url("http://127.0.0.1:8000", allow_trusted_internal=False)


def test_allows_trusted_demo_host():
    assert validate_public_http_url("http://demo-target:3100", allow_trusted_internal=True)


def test_allowlist_and_path_scope():
    assert host_allowed("http://demo-target:3100/catalog", ["demo-target"])
    assert_in_scope(
        "http://demo-target:3100/catalog",
        allowlist_domains=["demo-target"],
        path_prefixes=["/catalog"],
        allow_trusted_internal=True,
    )
    with pytest.raises(UrlGuardError):
        assert_in_scope(
            "http://demo-target:3100/admin",
            allowlist_domains=["demo-target"],
            path_prefixes=["/catalog"],
            allow_trusted_internal=True,
        )
