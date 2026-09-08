"""Freeze the companion into one self-contained HTML file.

Same shape as out/draft_terminal.html: data inlined, no server, no network.
A browser cannot fetch ESPN directly (the credentialed endpoints send no CORS
headers, and a public page could not hold the cookies anyway), so the only way
to reach this app from a phone without running the local server is to bake the
snapshot in at export time and re-export when it should change.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from . import service

STATIC = service.ROOT / 'season/static'


def embed(payload):
    """JSON safe to sit inside a <script> block."""
    return (json.dumps(payload, separators=(',', ':'))
            .replace('</', '<\\/').replace('<!--', '<\\!--'))


def build(season=2026, weeks=None, generated_at=None):
    """Return the HTML for a single-file export of the given weeks."""
    weeks = sorted(set(weeks or [])) or None
    if weeks is None:
        with service.connect() as conn:
            weeks = [r[0] for r in conn.execute(
                'SELECT DISTINCT week FROM snapshots WHERE season=? ORDER BY week', (season,))]
    if not weeks:
        raise LookupError(f'No snapshots stored for {season}. Run refresh first.')
    overviews, included = {}, []
    for week in weeks:
        try:
            view = service.get_overview(season, week)
        except LookupError:
            continue
        # The UI never renders the league id, and an export may be shared or
        # published; drop the identifier rather than ship it for no benefit.
        view['league'] = dict(view['league'], id=None)
        overviews[f'{season}-{week}'] = view
        included.append(week)
    if not overviews:
        raise LookupError('None of the requested weeks have a snapshot.')
    stamp = generated_at or service.now()
    contents = f"season {season}, week{'s' if len(included) > 1 else ''} " + ', '.join(str(w) for w in included)
    payload = {'seasons': [season], 'weeks': included, 'contents': contents,
               'exported_at': stamp, 'overviews': overviews}

    html = (STATIC / 'index.html').read_text()
    css = (STATIC / 'style.css').read_text()
    js = (STATIC / 'app.js').read_text()
    html = html.replace('<link rel="stylesheet" href="/style.css">',
                        '<style>\n' + css + '\n</style>')
    banner = ('<script>window.__SEASON_BUNDLE__=' + embed(payload) + ';</script>')
    html = html.replace('<script src="/app.js" defer></script>',
                        banner + '\n<script>\n' + js + '\n</script>')
    # A saved file has no server to refresh against.
    html = html.replace('id="refresh-button" data-testid="refresh-button" type="button">Refresh',
                        'id="refresh-button" data-testid="refresh-button" type="button" title="Saved export; re-run the export to update">Saved')
    stamped = dt.datetime.fromisoformat(stamp).astimezone(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    html = html.replace('<title>Season Companion</title>',
                        f'<title>Season Companion · {contents}</title>\n'
                        f'<!-- Static export generated {stamped}. Data is frozen at that moment. -->')
    if re.search(r'src="/|href="/', html):
        raise AssertionError('Export still references server paths')
    return html


def write(path, season=2026, weeks=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = build(season, weeks)
    path.write_text(html)
    return {'path': str(path), 'bytes': len(html.encode())}
