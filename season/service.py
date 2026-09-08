"""ESPN ingestion, immutable draft history and deterministic lineup scenarios."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import sqlite3
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / '.season'
DB = DATA / 'season.sqlite3'
POS = {1: 'QB', 2: 'RB', 3: 'WR', 4: 'TE', 5: 'K', 16: 'DST'}
SLOTS = {0: 'QB', 2: 'RB', 4: 'WR', 6: 'TE', 16: 'DST', 17: 'K', 20: 'Bench', 21: 'IR', 23: 'FLEX', 3: 'RB/WR', 5: 'WR/TE', 7: 'OP'}
UNAVAILABLE = {'OUT', 'INJURY_RESERVE', 'SUSPENSION', 'SUSPENDED', 'PUP'}

# Manager names, read off the 2026 round-one pick order (slot 1-12 = David,
# Kevin, Tristen, Casta, Kyle, Jeremy, Jonathan, Seth, Matthew, Zach, Josh,
# Joe). Keyed by ESPN team id, not draft slot, so it stays correct when next
# season reorders the draft. The ESPN team name is kept alongside as espn_name.
MANAGERS = {4: 'David', 11: 'Kevin', 5: 'Tristen', 12: 'Casta', 2: 'Kyle', 10: 'Jeremy',
            6: 'Jonathan', 3: 'Seth', 8: 'Matthew', 1: 'Zach', 9: 'Josh', 7: 'Joe'}


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def instant(value):
    if not value:
        return None
    if isinstance(value, (float, int)):
        return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc).isoformat()
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(dt.timezone.utc).isoformat()


def connect():
    DATA.mkdir(mode=0o700, parents=True, exist_ok=True)
    connection = sqlite3.connect(DB, timeout=30)
    connection.executescript('''
      CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, season INTEGER, week INTEGER, created TEXT, payload TEXT);
      CREATE TABLE IF NOT EXISTS drafts (season INTEGER PRIMARY KEY, payload TEXT);
      CREATE TABLE IF NOT EXISTS briefings (season INTEGER, week INTEGER, created TEXT, payload TEXT, PRIMARY KEY(season, week));
      CREATE TABLE IF NOT EXISTS refresh_errors (season INTEGER, week INTEGER, created TEXT, message TEXT);
      CREATE TABLE IF NOT EXISTS props (season INTEGER, week INTEGER, created TEXT, payload TEXT, PRIMARY KEY(season, week));
    ''')
    DB.chmod(0o600)
    return connection


def fetch_json(url, headers=None):
    request = urllib.request.Request(url, headers={'User-Agent': 'FantasySeasonCompanion/1.0', 'Accept': 'application/json', **(headers or {})})
    with urllib.request.urlopen(request, timeout=35, context=ssl.create_default_context(cafile=certifi.where())) as response:
        return json.load(response)


def stats(player, season, week, source):
    for item in player.get('stats', []):
        if (item.get('seasonId') == season and item.get('scoringPeriodId') == week
                and item.get('statSourceId') == source and item.get('statSplitTypeId') == 1):
            return item.get('appliedTotal')
    return None


def schedule_map(payload, expected_season, expected_week):
    # Refuse a wrong-week response rather than silently attach incorrect game locks.
    if payload.get('season', {}).get('year') != expected_season or payload.get('week', {}).get('number') != expected_week:
        raise ValueError('NFL schedule returned a different season/week')
    result = {}
    for event in payload.get('events', []):
        competition = event['competitions'][0]
        teams = competition.get('competitors', [])
        if len(teams) != 2:
            continue
        status = competition.get('status', event.get('status', {})).get('type', {})
        state = status.get('state', 'unknown')
        if status.get('name') in {'STATUS_POSTPONED', 'STATUS_CANCELED', 'STATUS_DELAYED'}:
            state = 'unknown'
        for team, opponent in (teams, list(reversed(teams))):
            result[int(team['team']['id'])] = {
                'kickoff': instant(competition.get('date', event.get('date'))),
                'opponent': ('vs ' if team.get('homeAway') == 'home' else '@ ') + opponent['team']['abbreviation'],
                'nfl_team': team['team']['abbreviation'], 'game_state': state,
            }
    return result


def locked(player, at=None):
    at = at or now()
    return bool(player.get('locked') or player.get('game_state') in {'in', 'post'}
                or (player.get('game_state') == 'pre' and player.get('kickoff') and player['kickoff'] <= at))


def lineup(roster, slots, assignments):
    indexed = {p['id']: p for p in roster}
    selected = [indexed[a['player_id']] for a in assignments]
    complete = len(assignments) == len(slots) and all(p.get('projection') is not None for p in selected)
    started = [p for p in selected if locked(p)]
    unstarted = [p for p in selected if not locked(p)]
    uncertain = any(p['game_state'] == 'unknown' or (locked(p) and p['game_state'] != 'post') for p in selected)
    remaining = sum(p['projection'] for p in unstarted) if all(p['projection'] is not None for p in unstarted) else None
    actual = sum(p.get('actual') or 0 for p in started)
    result = {
        'assignments': assignments, 'projection': round(sum(p['projection'] for p in selected), 2) if complete else None,
        'actual': round(actual, 2), 'remaining_projection': round(remaining, 2) if remaining is not None else None,
        'in_progress': uncertain, 'complete': complete and not uncertain,
        'note': 'ESPN projection baseline in league scoring; not independently researched. No win probability.',
    }
    if uncertain:
        result['note'] += ' Final-score outlook incomplete: game state or remaining in-game production is unknown.'
    return result


def optimize(roster, slots):
    """Maximum expected points, preserving all locked starters AND locked bench players."""
    reserved = {i for i, p in enumerate(roster) if locked(p)}
    fixed = {}
    for i in reserved:
        p = roster[i]
        if p['slot_id'] in (20, 21):
            continue
        for j, slot in enumerate(slots):
            if j not in fixed and slot['id'] == p['slot_id']:
                fixed[j] = i
                break

    @lru_cache(None)
    def solve(j, used):
        if j == len(slots):
            return (0, 0, ())
        if j in fixed:
            candidates = [fixed[j]]
        else:
            candidates = [i for i, p in enumerate(roster) if i not in reserved and not used & (1 << i)
                          and p['slot_id'] != 21 and p['status'] not in UNAVAILABLE
                          and slots[j]['id'] in p['eligible_slots']]
        best = None
        for i in candidates:
            score, flexibility, path = solve(j + 1, used | (1 << i))
            p = roster[i]
            value = round(p['projection'] * 1_000_000) if p['projection'] is not None else -10_000_000_000
            # Only break identical scoring ties: preserve later-game flexibility in FLEX.
            tie = int(dt.datetime.fromisoformat(p['kickoff']).timestamp()) if slots[j]['id'] == 23 and p.get('kickoff') else 0
            candidate = (score + value, flexibility + tie, (i,) + path)
            if best is None or candidate[:2] > best[:2]:
                best = candidate
        if best is None:
            score, flexibility, path = solve(j + 1, used)
            best = (score - 100_000_000_000, flexibility, (-1,) + path)
        return best

    assignments = [{'slot_id': slot['id'], 'slot': slot['label'], 'player_id': roster[i]['id']}
                   for slot, i in zip(slots, solve(0, 0)[2]) if i >= 0]
    return lineup(roster, slots, assignments)


def enrich(snapshot):
    snapshot = copy.deepcopy(snapshot)
    slots = [s for s in snapshot['rules']['lineup_slots'] for _ in range(s['count'])]
    for team in snapshot['teams']:
        for p in team['roster']:
            p['locked'] = locked(p)
        team['submitted'] = lineup(team['roster'], slots, [
            {'slot_id': p['slot_id'], 'slot': p['slot'], 'player_id': p['id']}
            for p in team['roster'] if p['slot_id'] not in (20, 21)])
        team['recommended'] = optimize(team['roster'], slots)
    return snapshot


def draft_baseline(season):
    # Captured pre-draft artifact is only evidence for its original season.
    if season != 2026:
        return {}
    source = (ROOT / 'out/draft_terminal.html').read_text()
    players = json.JSONDecoder().raw_decode(source.split('const PLAYERS=')[1])[0]
    return {p['id']: p for p in players}


def refresh(season=2026, week=1):
    if not 2000 <= season <= 2100 or not 1 <= week <= 18:
        raise ValueError('Invalid season or week')
    creds = json.loads((ROOT / '.espn.json').read_text())
    league_id = int(creds['league_id'])
    headers = {'Cookie': f"espn_s2={creds['espn_s2']}; SWID={creds['swid']}"}
    base = f'https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}'
    periods = list(range(week, min(week + 3, 19)))
    views = '&'.join('view=' + v for v in ['mSettings', 'mTeam', 'mRoster', 'mMatchup', 'mDraftDetail', 'mPendingTransactions'])
    filter_header = {'x-fantasy-filter': json.dumps({'players': {'limit': 1000, 'sortPercOwned': {'sortPriority': 1, 'sortAsc': False}, 'filterActive': {'value': True}}})}
    with ThreadPoolExecutor(max_workers=5) as executor:
        league_future = executor.submit(fetch_json, base + f'?scoringPeriodId={week}&' + views, headers)
        pool_futures = {w: executor.submit(fetch_json, base + f'?scoringPeriodId={w}&view=kona_player_info', {**headers, **filter_header}) for w in periods}
        schedule_futures = {w: executor.submit(fetch_json, f'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season}&seasontype=2&week={w}&limit=100') for w in periods}
        data = league_future.result()
        if data.get('seasonId') != season or data.get('id') != league_id or not data.get('teams') or not data.get('settings'):
            raise ValueError('ESPN league response is incomplete or mismatched')
        pools, schedules, warnings = {}, {}, []
        for w in periods:
            try:
                payload = pool_futures[w].result()
                if payload.get('seasonId', season) != season or 'players' not in payload:
                    raise ValueError('Invalid player response')
                pools[w] = {p['id']: p for p in payload['players']}
            except Exception:
                if w == week:
                    raise ValueError('Current player pool unavailable; snapshot was not replaced')
                pools[w] = {}
                warnings.append(f'Week {w} projections unavailable.')
            try:
                schedules[w] = schedule_map(schedule_futures[w].result(), season, w)
            except Exception:
                schedules[w] = {}
                warnings.append(f'Week {w} kickoff times unavailable. Check ESPN before acting.')
    observed = now()
    baseline = draft_baseline(season)
    owners = {entry['playerId']: t['id'] for t in data['teams'] for entry in t.get('roster', {}).get('entries', [])}
    all_players = {pid: entry['player'] for pid, entry in pools[week].items()}
    for t in data['teams']:
        for entry in t.get('roster', {}).get('entries', []):
            all_players.setdefault(entry['playerId'], entry['playerPoolEntry']['player'])

    def player_view(player, slot=20, owner=0):
        pid = player['id']
        full = pools[week].get(pid, {}).get('player', player)
        game = schedules[week].get(full.get('proTeamId'), {})
        outlook = []
        for w in periods:
            weekly = pools[w].get(pid, {}).get('player', {})
            scheduled = schedules[w].get(full.get('proTeamId'), {})
            outlook.append({'week': w, 'projection': stats(weekly, season, w, 1), 'opponent': scheduled.get('opponent'), 'kickoff': scheduled.get('kickoff')})
        return {'id': pid, 'name': full.get('fullName', f'Player {pid}'), 'pos': POS.get(full.get('defaultPositionId'), '?'),
                'nfl_team': game.get('nfl_team', baseline.get(pid, {}).get('team', '—')),
                'status': full.get('injuryStatus', 'ACTIVE'), 'slot_id': slot, 'slot': SLOTS.get(slot, str(slot)),
                'owner_id': owner, 'eligible_slots': full.get('eligibleSlots', []),
                'projection': stats(full, season, week, 1), 'actual': stats(full, season, week, 0),
                'kickoff': game.get('kickoff'), 'opponent': game.get('opponent'), 'game_state': game.get('game_state', 'unknown'),
                'locked': False, 'availability': pools[week].get(pid, {}).get('status', 'ONTEAM' if owner else 'UNKNOWN'),
                'week_outlook': outlook, 'outlook': full.get('seasonOutlook', '')}

    teams = [{'id': t['id'], 'name': MANAGERS.get(t['id']) or (t.get('name') or f"Team {t['id']}").strip(),
              'espn_name': (t.get('name') or '').strip(), 'manager': MANAGERS.get(t['id']),
              'abbrev': (t.get('abbrev') or '').strip(), 'waiver_priority': t.get('waiverRank'),
              'roster': [player_view(e['playerPoolEntry']['player'], e['lineupSlotId'], t['id']) for e in t.get('roster', {}).get('entries', [])]} for t in data['teams']]
    # Never silently import another account's league or infer a user team by name.
    my_id = int(creds.get('team_id', 5))
    if not any(t['id'] == my_id for t in teams):
        raise ValueError('Configured team is not present in this season')
    matchup = next(({'id': m['id'], 'my_team_id': my_id, 'opponent_team_id': next((m.get(side, {}).get('teamId') for side in ('home', 'away') if m.get(side, {}).get('teamId') != my_id), None)}
                    for m in data.get('schedule', []) if m.get('matchupPeriodId') == week and my_id in (m.get('home', {}).get('teamId'), m.get('away', {}).get('teamId'))), None)
    free_agents = [player_view(entry['player']) for pid, entry in pools[week].items() if not entry.get('onTeamId') and pid not in owners]
    free_agents.sort(key=lambda p: -(p['projection'] if p['projection'] is not None else -1))
    settings = data['settings']
    slots = [{'id': int(k), 'label': SLOTS.get(int(k), f'Slot {k}'), 'count': int(v)} for k, v in settings['rosterSettings']['lineupSlotCounts'].items() if v and int(k) not in (20, 21)]
    slots.sort(key=lambda s: [0, 2, 4, 6, 23, 17, 16].index(s['id']) if s['id'] in [0, 2, 4, 6, 23, 17, 16] else 99)
    rules = {'lineup_slots': slots, 'waiver_priority': next(t['waiver_priority'] for t in teams if t['id'] == my_id),
             'waiver_hours': settings.get('acquisitionSettings', {}).get('waiverHours'), 'waiver_timing_verified': False,
             'trade_review_hours': settings.get('tradeSettings', {}).get('revisionHours'),
             'trade_deadline': instant(settings.get('tradeSettings', {}).get('deadlineDate')),
             'scoring': [{'stat_id': str(s['statId']), 'points': s.get('points', 0)} for s in settings['scoringSettings']['scoringItems']]}
    pending = data.get('pendingTransactions')
    offers = []
    for tx in pending or []:
        items = tx.get('items', [])
        involved = {item.get(k) for item in items for k in ('fromTeamId', 'toTeamId')} | {tx.get('teamId')}
        if my_id not in involved or 'TRADE' not in tx.get('type', ''):
            continue
        offers.append({'id': tx.get('id'), 'type': tx.get('type'), 'status': tx.get('status', 'UNKNOWN'), 'team_id': tx.get('teamId'),
                       'items': [{'player_id': i.get('playerId'), 'name': all_players.get(i.get('playerId'), {}).get('fullName', 'Unknown player'), 'from_team_id': i.get('fromTeamId'), 'to_team_id': i.get('toTeamId')} for i in items], 'expires_at': None})
    picks = []
    for pick in data.get('draftDetail', {}).get('picks', []):
        pid = pick['playerId']
        known = all_players.get(pid, {})
        old = baseline.get(pid, {})
        picks.append({'overall': pick['overallPickNumber'], 'round': pick['roundId'], 'team_id': pick['teamId'], 'player_id': pid,
                      'name': known.get('fullName', old.get('name', f'Player {pid}')), 'pos': POS.get(known.get('defaultPositionId'), old.get('pos', '?')), 'ecr': old.get('ecr')})
    picks.sort(key=lambda p: p['overall'])
    completed = bool(data.get('draftDetail', {}).get('drafted'))
    expected = len(teams) * int(settings.get('draftSettings', {}).get('rounds', 14))
    reconciled = completed and len(picks) == expected and len({p['overall'] for p in picks}) == expected and len({p['player_id'] for p in picks}) == expected
    draft = {'status': 'frozen' if reconciled else 'unreconciled' if completed else 'in_progress', 'version': 1,
             'frozen_at': observed if reconciled else None, 'picks': picks,
             'note': 'Actual ESPN picks. ECR is the captured 2026 pre-draft reference, not a current ranking.' if baseline else 'Actual ESPN picks. Historical pre-draft ECR unavailable.'}
    deadlines = [{'id': 'waivers', 'label': 'Waiver review', 'at': None, 'verified': False, 'detail': 'Processing timezone and individual clearance times require ESPN confirmation.'}]
    my_roster = next(t['roster'] for t in teams if t['id'] == my_id)
    for kickoff in sorted({p['kickoff'] for p in my_roster if p['kickoff'] and p['kickoff'] > observed}):
        names = ', '.join(p['name'] for p in my_roster if p['kickoff'] == kickoff)
        deadlines.append({'id': 'kickoff-' + kickoff, 'label': 'Players lock at kickoff', 'at': kickoff, 'verified': True, 'detail': names + '. Review lineups at least 30 minutes beforehand.'})
    snapshot = {'schema_version': 1, 'snapshot_id': hashlib.sha256((observed + str(season) + str(week)).encode()).hexdigest()[:16],
                'generated_at': observed, 'data_as_of': observed, 'stale': False, 'warnings': warnings, 'season': season, 'week': week,
                'league': {'id': league_id, 'name': settings.get('name', 'Fantasy League'), 'my_team_id': my_id, 'timezone': 'America/Chicago'},
                'rules': rules, 'teams': teams, 'matchup': matchup, 'free_agents': free_agents, 'deadlines': deadlines, 'draft': draft,
                'trade_inbox': {'status': 'unavailable' if pending is None else 'observed' if offers else 'empty', 'last_checked': observed, 'offers': offers,
                                'capability_note': 'Pending view accessible; real offer lifecycle not yet validated. No background monitor is running.'},
                'source_health': [{'name': 'ESPN league', 'status': 'ok', 'checked_at': observed, 'detail': 'Authenticated read-only roster, matchup and availability snapshot.'},
                                  {'name': 'ESPN weekly projections', 'status': 'limited', 'checked_at': observed, 'detail': 'League-scored totals include first downs. Single quantitative forecast; no consensus claim.'},
                                  {'name': 'NFL schedule', 'status': 'ok' if schedules[week] else 'unavailable', 'checked_at': observed, 'detail': 'Kickoff times from ESPN scoreboard.'},
                                  {'name': 'Independent research', 'status': 'unavailable', 'checked_at': None, 'detail': 'Import a sourced briefing through the CLI; refreshing ESPN does not research news.'},
                                  {'name': 'Sportsbook markets', 'status': 'unavailable', 'checked_at': None, 'detail': 'Not connected. No inferred market endorsement.'}], 'briefing': None}
    with connect() as conn:
        stored = conn.execute('SELECT payload FROM drafts WHERE season=?', (season,)).fetchone()
        if stored:
            archived = json.loads(stored[0])
            keys = lambda rows: [(p['overall'], p['team_id'], p['player_id']) for p in rows]
            if keys(archived['picks']) != keys(draft['picks']):
                snapshot['warnings'].append('ESPN draft differs from frozen archive; explicit correction is required. Archive retained.')
            snapshot['draft'] = archived
        elif reconciled:
            conn.execute('INSERT INTO drafts VALUES (?,?)', (season, json.dumps(draft)))
        conn.execute('INSERT INTO snapshots VALUES (?,?,?,?,?)', (snapshot['snapshot_id'], season, week, observed, json.dumps(snapshot)))
        # Keep a bounded history per week, plus the immutable draft and research records.
        conn.execute('DELETE FROM snapshots WHERE season=? AND week=? AND id NOT IN (SELECT id FROM snapshots WHERE season=? AND week=? ORDER BY created DESC LIMIT 40)', (season, week, season, week))
    return get_overview(season, week)


def conn_props(season, week):
    """Stored market projections, or None. Kept here so get_overview never
    imports the props module and risks a circular import."""
    with connect() as conn:
        row = conn.execute('SELECT payload FROM props WHERE season=? AND week=?', (season, week)).fetchone()
    return json.loads(row[0]) if row else None


def get_overview(season=2026, week=1):
    with connect() as conn:
        row = conn.execute('SELECT payload FROM snapshots WHERE season=? AND week=? ORDER BY created DESC LIMIT 1', (season, week)).fetchone()
        if not row:
            raise LookupError('No snapshot yet. Run refresh for this season and week.')
        briefing = conn.execute('SELECT payload FROM briefings WHERE season=? AND week=?', (season, week)).fetchone()
        error = conn.execute('SELECT created,message FROM refresh_errors WHERE season=? AND week=? ORDER BY created DESC LIMIT 1', (season, week)).fetchone()
        # Every briefing imported this season, so a decision can be reviewed
        # after the week it was made rather than vanishing with the snapshot.
        archive = conn.execute('SELECT week, created, payload FROM briefings WHERE season=? ORDER BY week', (season,)).fetchall()
    result = enrich(json.loads(row[0]))
    result['generated_at'] = now()
    result['stale'] = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(result['data_as_of'])).total_seconds() > 900
    if error and error[0] > result['data_as_of']:
        result['stale'] = True
        result['warnings'].append('Latest refresh failed; displaying the last successful snapshot. ' + error[1])
    result['decision_history'] = [
        {'week': w, 'generated_at': created, 'current_week': w == week,
         'decisions': [{k: d.get(k) for k in ('id', 'title', 'recommendation', 'status', 'flip_condition')}
                       for d in json.loads(payload).get('decisions', [])]}
        for w, created, payload in archive]
    market = conn_props(season, week)
    result['market'] = None
    if market:
        # Join on player id: an independent market number sits beside the ESPN
        # projection, and never silently replaces it.
        for team in result['teams']:
            for p in team['roster']:
                entry = market['players'].get(str(p['id']))
                p['market_projection'] = entry['points'] if entry else None
        result['market'] = {k: market[k] for k in ('generated_at', 'method', 'events_priced', 'snapshot_id')}
        result['market']['stale_vs_snapshot'] = market['snapshot_id'] != result['snapshot_id']
        result['market']['players_priced'] = len(market['players'])
        health = next(s for s in result['source_health'] if s['name'] == 'Sportsbook markets')
        health.update(status='limited', checked_at=market['generated_at'], detail=market['method'])
    if briefing:
        result['briefing'] = json.loads(briefing[0])
        health = next(s for s in result['source_health'] if s['name'] == 'Independent research')
        health.update(status='limited', checked_at=result['briefing']['generated_at'], detail=result['briefing']['coverage_note'])
    return result


def safe_refresh(season, week):
    try:
        return refresh(season, week)
    except Exception as exc:
        # Never persist exception text potentially containing authentication headers.
        message = f'{type(exc).__name__}. Check ESPN authentication/network and retry.'
        with connect() as conn:
            conn.execute('INSERT INTO refresh_errors VALUES (?,?,?,?)', (season, week, now(), message))
        raise RuntimeError(message) from None


def import_briefing(path):
    payload = json.loads(Path(path).read_text())
    required = {'title', 'season', 'week', 'generated_at', 'snapshot_id', 'summary', 'coverage_note', 'decisions', 'news', 'sources', 'trade_ideas', 'watchlist'}
    if not required <= payload.keys():
        raise ValueError('Briefing is missing required fields: ' + ', '.join(sorted(required - payload.keys())))
    snapshot = get_overview(int(payload['season']), int(payload['week']))
    if payload['snapshot_id'] != snapshot['snapshot_id']:
        raise ValueError('Briefing must reference the latest snapshot. Reconcile before import.')
    source_ids = {s['id'] for s in payload['sources']}
    if len(source_ids) != len(payload['sources']):
        raise ValueError('Duplicate source IDs')
    for source in payload['sources']:
        if not source.get('url', '').startswith('https://'):
            raise ValueError('Sources require HTTPS URLs')
    for item in payload['decisions'] + payload['news']:
        if not set(item.get('source_ids', [])) <= source_ids:
            raise ValueError('Unknown evidence source')
    instant(payload['generated_at'])
    with connect() as conn:
        conn.execute('INSERT OR REPLACE INTO briefings VALUES (?,?,?,?)', (payload['season'], payload['week'], payload['generated_at'], json.dumps(payload)))
    return payload
