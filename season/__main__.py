"""python3 -m season {refresh,refresh-props,serve,export,export-static,props,import-briefing,seasons}."""
import argparse
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

from . import access, bundle, props, service

STATIC = service.ROOT / 'season/static'
REFRESH_LOCK = threading.Lock()


def serve(port, bind='127.0.0.1', extra_hosts=()):
    # A token is required the moment the server is reachable by anyone else.
    token = None if access.is_loopback(bind) else access.ensure_token()
    allowed = access.allowed_hosts(port, bind, extra_hosts)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def send(self, code, payload, kind='application/json', headers=()):
            body = json.dumps(payload).encode() if kind == 'application/json' else payload
            self.send_response(code)
            for name, value in headers:
                self.send_header(name, value)
            self.send_header('Content-Type', kind + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            if self.headers.get('Host') not in allowed:
                return False
            origin = self.headers.get('Origin')
            if origin and origin not in {f'http://{h}' for h in allowed} | {f'https://{h}' for h in allowed}:
                return False
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                return False
            if token is None:
                return True
            return access.token_matches(access.cookie_token(self.headers.get('Cookie')), token)

        def claim_token(self, parsed):
            """Trade a ?token= link for a cookie, then drop it from the URL so the
            secret stops travelling in browser history and referrers."""
            if token is None:
                return False
            supplied = parse_qs(parsed.query).get('token', [''])[0]
            if not access.token_matches(supplied, token):
                return False
            query = {k: v for k, v in parse_qs(parsed.query).items() if k != 'token'}
            rest = urlencode({k: v[0] for k, v in query.items()})
            self.send(302, b'', 'text/plain', headers=[
                ('Set-Cookie', f'{access.COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=7776000'),
                ('Location', parsed.path + ('?' + rest if rest else ''))])
            return True

        def do_GET(self):
            parsed = urlparse(self.path)
            if self.claim_token(parsed):
                return
            if not self.authorized():
                return self.send(401 if token else 403,
                                 {'error': 'This companion needs its access link. Open the URL printed by "season serve".'
                                           if token else 'Local access only'})
            files = {'/': ('index.html', 'text/html'), '/index.html': ('index.html', 'text/html'),
                     '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
            if parsed.path in files:
                name, kind = files[parsed.path]
                try:
                    return self.send(200, (STATIC / name).read_bytes(), kind)
                except FileNotFoundError:
                    return self.send(503, {'error': 'UI files are not available'})
            try:
                query = parse_qs(parsed.query)
                season = int(query.get('season', ['2026'])[0])
                week = int(query.get('week', ['1'])[0])
                if parsed.path == '/api/v1/seasons':
                    with service.connect() as conn:
                        seasons = [r[0] for r in conn.execute('SELECT DISTINCT season FROM snapshots ORDER BY season DESC')]
                    return self.send(200, {'seasons': seasons})
                if parsed.path == '/api/v1/contract':
                    return self.send(200, (service.ROOT / 'season/CONTRACT.md').read_bytes(), 'text/plain')
                view = service.get_overview(season, week)
                routes = {'/api/v1/overview': view, '/api/v1/briefing': view['briefing'],
                          '/api/v1/waivers': view['free_agents'], '/api/v1/trade-offers': view['trade_inbox'],
                          '/api/v1/deadlines': view['deadlines'], '/api/v1/source-health': view['source_health'],
                          '/api/v1/decisions': (view['briefing'] or {}).get('decisions', [])}
                # Computed only on request: it re-reads the snapshot.
                if parsed.path == '/api/v1/market':
                    routes[parsed.path] = props.compare(season, week)
                if parsed.path in routes:
                    return self.send(200, routes[parsed.path] if parsed.path == '/api/v1/overview' else {
                        k: view[k] for k in ['schema_version', 'snapshot_id', 'generated_at', 'data_as_of', 'stale', 'warnings']
                    } | {'data': routes[parsed.path]})
                if parsed.path.startswith('/api/v1/players/'):
                    pid = int(parsed.path.rsplit('/', 1)[-1])
                    player = next((p for t in view['teams'] for p in t['roster'] if p['id'] == pid), None)
                    player = player or next((p for p in view['free_agents'] if p['id'] == pid), None)
                    if player:
                        return self.send(200, {'snapshot_id': view['snapshot_id'], 'data': player})
                return self.send(404, {'error': 'Not found'})
            except LookupError as exc:
                return self.send(404, {'error': str(exc)})
            except (ValueError, TypeError):
                return self.send(400, {'error': 'Invalid season, week or player ID'})

        def do_POST(self):
            if not self.authorized() or not self.headers.get('Origin'):
                return self.send(403, {'error': 'Same-origin requests required; agents should use the CLI'})
            if self.path != '/api/v1/refresh':
                return self.send(404, {'error': 'Not found'})
            if not self.headers.get('Content-Type', '').startswith('application/json'):
                return self.send(415, {'error': 'JSON required'})
            if not REFRESH_LOCK.acquire(blocking=False):
                return self.send(409, {'error': 'Refresh already running'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > 4096:
                    return self.send(400, {'error': 'Invalid request size'})
                body = json.loads(self.rfile.read(length))
                return self.send(200, service.safe_refresh(int(body.get('season', 2026)), int(body.get('week', 1))))
            except (ValueError, TypeError):
                return self.send(400, {'error': 'Invalid refresh parameters'})
            except RuntimeError as exc:
                return self.send(502, {'error': str(exc)})
            finally:
                REFRESH_LOCK.release()

    server = ThreadingHTTPServer((bind, port), Handler)
    if token is None:
        print(f'Season companion: http://127.0.0.1:{port} (this machine only; no background research)', flush=True)
    else:
        print('Season companion is reachable from other devices on this network.', flush=True)
        print('Open one of these once per device; the link is a password, so do not share it:', flush=True)
        seen = sorted({h for h in allowed if not access.is_loopback(h.rsplit(':', 1)[0])})
        for host in seen or [f'{bind}:{port}']:
            print(f'  http://{host}/?token={token}', flush=True)
        print(f'Token stored in {access.TOKEN_FILE}. Delete that file to revoke every device.', flush=True)
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['refresh', 'serve', 'export', 'import-briefing', 'seasons', 'refresh-props', 'props', 'export-static'])
    parser.add_argument('--season', type=int, default=2026)
    parser.add_argument('--week', type=int, default=1)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--file')
    parser.add_argument('--all-weeks', action='store_true',
                        help='export-static: include every stored week instead of just --week')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Bind address. Use 0.0.0.0 to reach it from a phone; a token is then required.')
    parser.add_argument('--allow-host', action='append', default=[],
                        help='Extra Host header to accept, e.g. a Tailscale name. Repeatable.')
    args = parser.parse_args()
    try:
        if args.command == 'serve':
            serve(args.port, args.host, args.allow_host)
            return
        if args.command == 'refresh':
            result = service.safe_refresh(args.season, args.week)
            print(json.dumps({'snapshot_id': result['snapshot_id'], 'teams': len(result['teams']), 'draft': result['draft']['status'], 'warnings': result['warnings']}))
        elif args.command == 'refresh-props':
            result = props.refresh_props(args.season, args.week)
            print(json.dumps({'players_priced': len(result['players']), 'events_priced': result['events_priced'], 'errors': result['errors']}))
        elif args.command == 'props':
            result = props.compare(args.season, args.week)
            if not result:
                raise LookupError('No market prices yet. Run refresh-props for this season and week.')
            print(json.dumps(result, indent=2))
        elif args.command == 'export-static':
            out = args.file or f'out/season_{args.season}_week{args.week}.html'
            weeks = None if args.all_weeks else [args.week]
            print(json.dumps(bundle.write(out, args.season, weeks)))
        elif args.command == 'export':
            print(json.dumps(service.get_overview(args.season, args.week), indent=2))
        elif args.command == 'import-briefing':
            if not args.file:
                parser.error('--file is required')
            result = service.import_briefing(args.file)
            print(json.dumps({'imported': result['title'], 'snapshot_id': result['snapshot_id']}))
        else:
            with service.connect() as conn:
                print(json.dumps({'seasons': [r[0] for r in conn.execute('SELECT DISTINCT season FROM snapshots ORDER BY season DESC')]}))
    except (RuntimeError, LookupError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
