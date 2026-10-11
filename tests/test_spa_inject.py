"""Runtime API-base injection helpers (Docker / reverse-proxy deployments).

A prebuilt image can't take a build-time VITE_* override, so the backend
injects OMNIVOICE_PUBLIC_API_BASE into index.html as a window global. These
test the pure helpers without booting the app.
"""
from __future__ import annotations

import base64
import hashlib

import pytest

from core.spa_inject import inject_api_base, is_valid_public_api_base


def test_valid_public_api_base_accepts_http_urls():
    assert is_valid_public_api_base("https://api.example.com")
    assert is_valid_public_api_base("http://10.0.0.5:3900")
    assert is_valid_public_api_base("https://voice.example.com/api")


def test_valid_public_api_base_rejects_unsafe_or_empty():
    assert not is_valid_public_api_base("")
    assert not is_valid_public_api_base("not a url")
    assert not is_valid_public_api_base("javascript:alert(1)")
    # No script breakout possible — angle brackets / quotes are rejected.
    assert not is_valid_public_api_base('https://x"</script><script>evil()')
    assert not is_valid_public_api_base("https://x</script>")


def test_inject_api_base_into_head():
    doc = "<html><head><title>x</title></head><body></body></html>"
    out = inject_api_base(doc, "https://api.example.com")
    assert '<head><script>window.__OMNIVOICE_API_BASE__="https://api.example.com";</script>' in out
    assert out.count("<head>") == 1  # injected once, original head preserved


def test_inject_api_base_prepends_when_no_head():
    out = inject_api_base("<body>x</body>", "http://10.0.0.5:3900")
    assert out.startswith('<script>window.__OMNIVOICE_API_BASE__="http://10.0.0.5:3900";</script>')


def test_inject_api_base_json_encodes_value():
    # json.dumps wraps in double quotes; combined with is_valid_public_api_base
    # the value can't contain a quote, so the snippet is always well-formed.
    out = inject_api_base("<head></head>", "https://a/b")
    assert '="https://a/b";' in out


def test_inject_api_base_authorizes_exact_script_under_renderer_csp():
    script = 'window.__OMNIVOICE_API_BASE__="https://api.example.com";'
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    doc = '<meta http-equiv="Content-Security-Policy" content="script-src \'self\';">'
    out = inject_api_base(doc, "https://api.example.com")
    assert f"script-src 'self' 'sha256-{digest}'" in out


def test_inject_api_base_allows_remote_http_and_websocket_connections():
    doc = '<meta http-equiv="Content-Security-Policy" content="connect-src \'self\' blob:">'
    out = inject_api_base(doc, "https://api.example.com/v1")
    assert "connect-src 'self' https://api.example.com wss://api.example.com blob:" in out


@pytest.mark.parametrize("url", [
    "https://[", "https://[::1", "https://?api", "https://#api",
    "https://example.com:bad", "https://example.com:65536",
    "https://user:password@example.com/api",
])
def test_public_api_base_rejects_unusable_authorities(url):
    assert not is_valid_public_api_base(url)


@pytest.mark.parametrize("url", [
    "http://[::1]:3900/api", "https://example.com:443/api",
])
def test_public_api_base_accepts_valid_ipv6_and_ports(url):
    assert is_valid_public_api_base(url)
    assert "window.__OMNIVOICE_API_BASE__" in inject_api_base("<head></head>", url)


@pytest.mark.parametrize("url", [
    "https://[::1]oops/api", "https://exa%zz.com/api",
    "https://example.com%23evil.com/api", "https://example%2f.com/api",
    "https://[v1.host]/api", "https://[fe80::1%25en0]/api", "https://exa\x7fmple.com/api",
])
def test_public_api_base_rejects_browser_invalid_hosts(url):
    from core.spa_inject import is_valid_public_api_base
    assert not is_valid_public_api_base(url)


@pytest.mark.parametrize("url", ["https://%65xample.com/api", "https://例え.テスト/api"])
def test_public_api_base_preserves_browser_valid_hosts(url):
    from core.spa_inject import is_valid_public_api_base
    assert is_valid_public_api_base(url)
