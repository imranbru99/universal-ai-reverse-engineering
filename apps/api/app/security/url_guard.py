"""SSRF and scope URL guards."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


PRIVATE_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Hostnames allowed for local demo / compose networking even if they resolve privately.
TRUSTED_INTERNAL_HOSTS = {
    "demo-target",
    "localhost",
    "host.docker.internal",
}


class UrlGuardError(ValueError):
    pass


def _is_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(ip in net for net in PRIVATE_NETWORKS) or ip.is_private or ip.is_loopback or ip.is_link_local


def validate_public_http_url(url: str, *, allow_trusted_internal: bool = True) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UrlGuardError("Only http/https URLs are allowed")
    if not parsed.hostname:
        raise UrlGuardError("URL must include a hostname")
    host = parsed.hostname.lower()

    if allow_trusted_internal and host in TRUSTED_INTERNAL_HOSTS:
        return url

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UrlGuardError(f"Unable to resolve host: {host}") from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if _is_private_ip(ip) and not (allow_trusted_internal and host in TRUSTED_INTERNAL_HOSTS):
            raise UrlGuardError(f"Private or link-local address blocked for host {host}")
    return url


def host_allowed(url: str, allowlist_domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    for domain in allowlist_domains:
        d = domain.lower().strip(".")
        if host == d or host.endswith("." + d):
            return True
    return False


def path_allowed(url: str, path_prefixes: list[str]) -> bool:
    if not path_prefixes:
        return True
    path = urlparse(url).path or "/"
    return any(path.startswith(prefix) for prefix in path_prefixes)


def assert_in_scope(
    url: str,
    *,
    allowlist_domains: list[str],
    path_prefixes: list[str] | None = None,
    allow_trusted_internal: bool = True,
) -> None:
    validate_public_http_url(url, allow_trusted_internal=allow_trusted_internal)
    if not host_allowed(url, allowlist_domains):
        raise UrlGuardError("URL host is outside authorization allowlist")
    if not path_allowed(url, path_prefixes or []):
        raise UrlGuardError("URL path is outside authorization path prefixes")
