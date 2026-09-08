import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from season import access


class LoopbackTests(unittest.TestCase):
    def test_loopback_addresses_are_recognised(self):
        for host in ('127.0.0.1', 'localhost', '::1', '[::1]', '127.0.0.5', ''):
            self.assertTrue(access.is_loopback(host), host)

    def test_routable_addresses_are_not_loopback(self):
        for host in ('0.0.0.0', '10.0.0.186', '192.168.1.5', 'mac.tail123.ts.net'):
            self.assertFalse(access.is_loopback(host), host)


class TokenTests(unittest.TestCase):
    def test_token_is_created_once_and_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'token'
            with patch.object(access, 'TOKEN_FILE', path), patch.object(access.service, 'DATA', Path(tmp)):
                first = access.ensure_token()
                self.assertEqual(access.ensure_token(), first)
                self.assertGreaterEqual(len(first), 24)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_blank_stored_token_is_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'token'
            path.write_text('   ')
            with patch.object(access, 'TOKEN_FILE', path), patch.object(access.service, 'DATA', Path(tmp)):
                self.assertTrue(access.ensure_token().strip())

    def test_only_an_exact_token_matches(self):
        self.assertTrue(access.token_matches('abc123', 'abc123'))
        self.assertFalse(access.token_matches('abc124', 'abc123'))
        self.assertFalse(access.token_matches('abc123 ', 'abc123'))

    def test_empty_or_missing_token_never_matches(self):
        for supplied, expected in ((None, 'abc'), ('', 'abc'), ('abc', None), ('', '')):
            self.assertFalse(access.token_matches(supplied, expected))


class CookieTests(unittest.TestCase):
    def test_token_cookie_is_read(self):
        self.assertEqual(access.cookie_token('season_token=xyz'), 'xyz')
        self.assertEqual(access.cookie_token('other=1; season_token=xyz; more=2'), 'xyz')

    def test_absent_or_malformed_cookie_returns_none(self):
        for header in (None, '', 'other=1', 'not a cookie'):
            self.assertIsNone(access.cookie_token(header))


class AllowedHostTests(unittest.TestCase):
    def test_loopback_bind_allows_only_loopback_names(self):
        hosts = access.allowed_hosts(8765, '127.0.0.1')
        self.assertIn('127.0.0.1:8765', hosts)
        self.assertIn('localhost:8765', hosts)
        self.assertNotIn('10.0.0.186:8765', hosts)

    def test_explicit_bind_address_is_allowed(self):
        self.assertIn('10.0.0.186:8765', access.allowed_hosts(8765, '10.0.0.186'))

    def test_extra_hosts_are_added_with_the_port(self):
        hosts = access.allowed_hosts(8765, '0.0.0.0', ['mac.tail123.ts.net'])
        self.assertIn('mac.tail123.ts.net:8765', hosts)

    def test_unlisted_host_is_never_allowed(self):
        hosts = access.allowed_hosts(8765, '0.0.0.0', ['mac.tail123.ts.net'])
        self.assertNotIn('evil.example.com:8765', hosts)


if __name__ == '__main__':
    unittest.main()
