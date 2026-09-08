"""Access control for serving the companion beyond loopback.

Loopback keeps its existing behaviour exactly: no token, no ceremony. The
moment the server binds to an address someone else can reach, a token becomes
mandatory, because the snapshot contains a private league and the refresh
endpoint spends the user's own ESPN credentials.
"""
from __future__ import annotations

import hmac
import ipaddress
import secrets
import socket
from http.cookies import SimpleCookie

from . import service

TOKEN_FILE = service.DATA / 'token'
COOKIE = 'season_token'


def is_loopback(host):
    """True for addresses only this machine can reach."""
    bare = (host or '').strip().strip('[]')
    if bare in ('localhost', ''):
        return True
    try:
        return ipaddress.ip_address(bare).is_loopback
    except ValueError:
        return False


def ensure_token():
    """Read the stored token, creating one on first networked run."""
    service.DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
    if TOKEN_FILE.exists():
        existing = TOKEN_FILE.read_text().strip()
        if existing:
            return existing
    token = secrets.token_urlsafe(24)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)
    return token


def token_matches(supplied, expected):
    """Constant-time comparison; empty never matches."""
    if not supplied or not expected:
        return False
    return hmac.compare_digest(str(supplied), str(expected))


def cookie_token(header):
    if not header:
        return None
    try:
        jar = SimpleCookie()
        jar.load(header)
    except Exception:
        return None
    return jar[COOKIE].value if COOKIE in jar else None


def local_addresses():
    """Best-effort LAN addresses, so the printed URL is one a phone can use."""
    found = set()
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(('192.0.2.1', 80))  # TEST-NET-1: routed nowhere, never sends
        found.add(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.add(info[4][0])
    except OSError:
        pass
    return sorted(a for a in found if not is_loopback(a))


def allowed_hosts(port, bind, extra=()):
    """Host header values this server will answer to (DNS-rebinding defence)."""
    names = {'localhost', '127.0.0.1', '[::1]', '::1'}
    if bind and bind not in ('0.0.0.0', '::'):
        names.add(bind)
    if bind in ('0.0.0.0', '::'):
        names.update(local_addresses())
    names.update(h for h in extra if h)
    hosts = set()
    for name in names:
        hosts.add(f'{name}:{port}')
        if port in (80, 443):
            hosts.add(name)
    return hosts
