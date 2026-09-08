"""Sportsbook player props converted into this league's own scoring.

This is a second opinion that is deliberately independent of ESPN. ESPN
publishes a single projection in generic scoring; a betting market publishes
the components (receptions, yards, touchdowns) that this league actually pays
for, including the 0.5 receiving first-down bonus that no public projection
prices. Converting the components ourselves is the only way to get a market
number in league points.

Read-only. Fetches from The Odds API when a key is configured and never places,
prices or recommends a wager.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from statistics import NormalDist

from . import service

ROOT = service.ROOT
API = 'https://api.the-odds-api.com/v4/sports/americanfootball_nfl'

# League scoring (CLAUDE.md). Only the components a prop market can price.
SCORING = {
    'rec_yd': 0.1, 'rec': 0.5, 'rec_td': 6.0, 'refd': 0.5,
    'rush_yd': 0.1, 'rush_td': 6.0, 'rfd': 0.25,
    'pass_yd': 0.04, 'pass_td': 4.0, 'int': -2.0,
}

MARKETS = ('player_receptions', 'player_reception_yds', 'player_rush_yds',
           'player_rush_attempts', 'player_anytime_td', 'player_pass_yds',
           'player_pass_tds', 'player_pass_interceptions')

# Spread of the outcome around the posted line, used ONLY to shift the mean off
# the line when the de-vigged over price is not 50/50. Books post lines close to
# the median, so this correction is small and the exact value barely matters:
# at a 55% over price a receptions sigma of 2.2 moves the mean by 0.28 catches.
# These are order-of-magnitude assumptions, not measured values.
SIGMA = {'player_receptions': 2.2, 'player_reception_yds': 30.0,
         'player_rush_yds': 28.0, 'player_rush_attempts': 4.5,
         'player_pass_yds': 60.0, 'player_pass_tds': 1.1,
         'player_pass_interceptions': 0.8}

SUFFIX = re.compile(r'\b(jr|sr|ii|iii|iv|v)\b')


def load_first_down_rates():
    """Measured nflverse 2023-25 rates; the league pays per first down."""
    return json.loads((ROOT / 'out/first_down_rates.json').read_text())


def normalize(name):
    """Match market names to ESPN names: fold accents, drop punctuation/suffixes."""
    folded = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode().lower()
    # Apostrophes vanish (Ja'Marr -> jamarr) but hyphens and dots become spaces,
    # because sources genuinely disagree on "Amon-Ra" vs "Amon Ra".
    cleaned = re.sub(r'[^a-z ]', ' ', folded.replace("'", ''))
    return ' '.join(SUFFIX.sub('', cleaned).split())


def american_to_probability(price):
    """American odds to implied probability, vig still included."""
    price = float(price)
    if price == 0:
        raise ValueError('Zero is not a valid American price')
    return 100 / (price + 100) if price > 0 else -price / (-price + 100)


def devig(prices):
    """Normalize a complete two-sided market so the probabilities sum to 1.

    The book's margin is spread proportionally across both sides. This is the
    standard multiplicative method; it assumes the vig is symmetric, which is
    only approximately true for heavy favourites.
    """
    implied = [american_to_probability(p) for p in prices]
    total = sum(implied)
    if total <= 0:
        raise ValueError('Market has no implied probability')
    return [p / total for p in implied]


def expected_over_under(line, over_probability, sigma):
    """Mean of a stat given its posted line and de-vigged over price.

    Treats the stat as normal around an unknown mean: P(X > line) = p implies
    mean = line + sigma * Phi_inverse(p). At p = 0.5 this returns the line
    unchanged, which is the common case.
    """
    p = min(max(float(over_probability), 1e-6), 1 - 1e-6)
    return float(line) + sigma * NormalDist().inv_cdf(p)


def expected_touchdowns(yes_probability):
    """Anytime-TD probability as an expected touchdown count.

    Deliberately a slight underestimate: 'anytime' pays the same for one
    touchdown as for three, so multi-touchdown games are not counted here.
    """
    return float(yes_probability)


def project(pos, lines, rates=None):
    """Convert one player's market lines into league points.

    `lines` maps a market key to {'point': float|None, 'over': prob,
    'under': prob} (or {'yes': prob} for anytime touchdown). Returns the
    points, an itemized breakdown, and anything that could not be modeled.
    """
    rates = rates or load_first_down_rates()
    per_reception = rates['fd_per_reception'].get(pos)
    per_carry = rates['fd_per_carry'].get(pos)
    breakdown, unmodeled, total = [], [], 0.0

    def add(label, detail, points):
        nonlocal total
        total += points
        breakdown.append({'label': label, 'detail': detail, 'points': round(points, 2)})

    def mean(market):
        line = lines.get(market)
        if not line or line.get('point') is None or line.get('over') is None:
            return None
        return expected_over_under(line['point'], line['over'], SIGMA[market])

    receptions = mean('player_receptions')
    if receptions is not None:
        add('Receptions', f'{receptions:.1f} catches x {SCORING["rec"]}', receptions * SCORING['rec'])
        if per_reception is not None:
            first_downs = receptions * per_reception
            add('Receiving first downs',
                f'{receptions:.1f} x {per_reception} rate x {SCORING["refd"]}',
                first_downs * SCORING['refd'])
        else:
            unmodeled.append(f'No measured first-down rate for {pos} receptions.')

    rec_yards = mean('player_reception_yds')
    if rec_yards is not None:
        add('Receiving yards', f'{rec_yards:.1f} yds x {SCORING["rec_yd"]}', rec_yards * SCORING['rec_yd'])

    rush_yards = mean('player_rush_yds')
    if rush_yards is not None:
        add('Rushing yards', f'{rush_yards:.1f} yds x {SCORING["rush_yd"]}', rush_yards * SCORING['rush_yd'])

    carries = mean('player_rush_attempts')
    if carries is not None and per_carry is not None:
        add('Rushing first downs',
            f'{carries:.1f} carries x {per_carry} rate x {SCORING["rfd"]}',
            carries * per_carry * SCORING['rfd'])
    elif rush_yards is not None and carries is None:
        unmodeled.append('No rush-attempt line, so rushing first downs are not counted.')

    pass_yards = mean('player_pass_yds')
    if pass_yards is not None:
        add('Passing yards', f'{pass_yards:.1f} yds x {SCORING["pass_yd"]}', pass_yards * SCORING['pass_yd'])
        unmodeled.append('Passing first downs are not modeled; no completions-based rate is measured.')

    pass_tds = mean('player_pass_tds')
    if pass_tds is not None:
        add('Passing touchdowns', f'{pass_tds:.2f} x {SCORING["pass_td"]}', pass_tds * SCORING['pass_td'])

    picks = mean('player_pass_interceptions')
    if picks is not None:
        add('Interceptions', f'{picks:.2f} x {SCORING["int"]}', picks * SCORING['int'])

    td = lines.get('player_anytime_td', {}).get('yes')
    if td is not None:
        scored = expected_touchdowns(td)
        add('Touchdown', f'{scored * 100:.0f}% anytime x 6', scored * SCORING['rec_td'])
        unmodeled.append('Anytime-touchdown pricing ignores multi-touchdown games, so this is a floor.')

    return {'points': round(total, 2), 'breakdown': breakdown,
            'unmodeled': unmodeled, 'markets_used': sorted(lines)}


def parse_event(event):
    """Collapse one event's bookmaker outcomes into per-player de-vigged lines.

    Prices are averaged across books after de-vigging each book separately, so
    one stale book cannot drag a line on its own.
    """
    players = {}
    for book in event.get('bookmakers', []):
        for market in book.get('markets', []):
            key = market.get('key')
            if key not in MARKETS:
                continue
            sides = {}
            for outcome in market.get('outcomes', []):
                who = outcome.get('description')
                if not who or outcome.get('price') is None:
                    continue
                sides.setdefault((who, outcome.get('point')), {})[str(outcome.get('name', '')).lower()] = outcome['price']
            for (who, point), prices in sides.items():
                pair = ('over', 'under') if 'over' in prices else ('yes', 'no')
                if not all(side in prices for side in pair):
                    continue  # one-sided quote cannot be de-vigged
                try:
                    fair = devig([prices[pair[0]], prices[pair[1]]])
                except ValueError:
                    continue
                entry = players.setdefault(normalize(who), {}).setdefault(key, {'point': point, 'samples': []})
                entry['samples'].append(fair[0])
                entry['name'] = who
    for markets in players.values():
        for key, entry in markets.items():
            average = sum(entry['samples']) / len(entry['samples'])
            entry['books'] = len(entry.pop('samples'))
            entry['over' if key != 'player_anytime_td' else 'yes'] = average
    return players


def api_key():
    for path in (ROOT / '.odds.json',):
        if path.exists():
            key = json.loads(path.read_text()).get('api_key')
            if key:
                return key
    import os
    return os.environ.get('ODDS_API_KEY')


def fetch(path, params):
    from urllib.parse import urlencode
    return service.fetch_json(f'{API}{path}?' + urlencode(params))


def refresh_props(season=2026, week=1, regions='us', books=None):
    """Pull props for every player in the snapshot and store league-point values.

    Only fetches events that actually contain a rostered player, which keeps
    the free tier (500 credits/month) comfortably sufficient.
    """
    key = api_key()
    if not key:
        raise RuntimeError('No odds API key. Put {"api_key": "..."} in .odds.json '
                           'or set ODDS_API_KEY. Free tier: https://the-odds-api.com/')
    overview = service.get_overview(season, week)
    wanted = {}
    for team in overview['teams']:
        for player in team['roster']:
            wanted[normalize(player['name'])] = player
    rates = load_first_down_rates()
    events = fetch('/events', {'apiKey': key})
    params = {'apiKey': key, 'regions': regions, 'markets': ','.join(MARKETS), 'oddsFormat': 'american'}
    if books:
        params['bookmakers'] = books
    found, credits, errors = {}, 0, []
    for event in events:
        try:
            payload = fetch(f"/events/{event['id']}/odds", params)
        except Exception as exc:
            errors.append(f"{event.get('home_team', '?')}: {type(exc).__name__}")
            continue
        credits += 1
        for name, lines in parse_event(payload).items():
            if name in wanted:
                found[name] = {'name': lines[next(iter(lines))].get('name', name),
                               'lines': {k: {i: v for i, v in line.items() if i != 'name'}
                                         for k, line in lines.items()},
                               'commence_time': event.get('commence_time')}
    # Keyed by player id so consumers join on identity, never on name spelling.
    projections = {}
    for name, entry in found.items():
        player = wanted[name]
        result = project(player['pos'], entry['lines'], rates)
        result.update(name=player['name'], pos=player['pos'], commence_time=entry['commence_time'])
        projections[str(player['id'])] = result
    payload = {'season': season, 'week': week, 'generated_at': service.now(),
               'snapshot_id': overview['snapshot_id'], 'regions': regions,
               'events_priced': credits, 'errors': errors,
               'method': ('De-vigged consensus across books, converted with league scoring and '
                          'measured nflverse first-down rates. Market medians, not fantasy means.'),
               'players': projections}
    with service.connect() as conn:
        conn.execute('INSERT OR REPLACE INTO props VALUES (?,?,?,?)',
                     (season, week, payload['generated_at'], json.dumps(payload)))
    return payload


def get_props(season=2026, week=1):
    with service.connect() as conn:
        row = conn.execute('SELECT payload FROM props WHERE season=? AND week=?', (season, week)).fetchone()
    return json.loads(row[0]) if row else None


def compare(season=2026, week=1):
    """Every rostered player where a market number exists, ESPN vs market."""
    stored = get_props(season, week)
    if not stored:
        return None
    overview = service.get_overview(season, week)
    rows = []
    for team in overview['teams']:
        for player in team['roster']:
            entry = stored['players'].get(str(player['id']))
            if not entry:
                continue
            espn = player.get('projection')
            rows.append({'player_id': player['id'], 'name': player['name'], 'pos': player['pos'],
                         'team_id': team['id'], 'owner_is_me': team['id'] == overview['league']['my_team_id'],
                         'espn': espn, 'market': entry['points'],
                         'delta': None if espn is None else round(entry['points'] - espn, 2),
                         'breakdown': entry['breakdown'], 'unmodeled': entry['unmodeled']})
    rows.sort(key=lambda r: abs(r['delta']) if r['delta'] is not None else -1, reverse=True)
    return {'generated_at': stored['generated_at'], 'snapshot_id': stored['snapshot_id'],
            'method': stored['method'], 'stale_vs_snapshot': stored['snapshot_id'] != overview['snapshot_id'],
            'rows': rows}
