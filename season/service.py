"""ESPN ingestion, immutable draft history and deterministic lineup scenarios."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import sqlite3
import ssl
import urllib.request
import zoneinfo
from collections import Counter
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
# A starter left in one of these before kickoff is an action. QUESTIONABLE is
# only a check against the final injury report.
ACT_STATUSES = UNAVAILABLE | {'DOUBTFUL'}
STATUS_LABELS = {'ACTIVE': 'Active', 'QUESTIONABLE': 'Questionable', 'DOUBTFUL': 'Doubtful', 'OUT': 'Out',
                 'INJURY_RESERVE': 'Injured reserve', 'SUSPENSION': 'Suspended', 'SUSPENDED': 'Suspended',
                 'PUP': 'PUP list', 'DAY_TO_DAY': 'Day to day'}
# ESPN nudges projections by a point or so between syncs; a move this large is
# worth reporting as a change.
PROJECTION_MOVE = 2.0
# Projected gain, in league points, before a lineup difference is named at all
# (below it the optimizer is splitting near-ties), and before it is called an
# action rather than a lean worth checking.
LINEUP_GAIN = 0.5
LINEUP_ACT = 3.0

# ESPN schedules waiver processing on its own clock, not the league's.
ESPN_TZ = zoneinfo.ZoneInfo('America/New_York')
WEEKDAYS = {'MONDAY': 0, 'TUESDAY': 1, 'WEDNESDAY': 2, 'THURSDAY': 3,
            'FRIDAY': 4, 'SATURDAY': 5, 'SUNDAY': 6}

# The observable end state a briefing decision claims. Every value is a list of
# player ids, so a recommendation can be checked against the roster instead of
# read.
EXPECTATIONS = ('start', 'bench', 'roster', 'drop')

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


def waiver_window(acquisition, last_execution, at=None):
    """When ESPN next processes waivers, anchored to a run it actually performed.

    ESPN reports `waiverProcessDays` and a `waiverProcessHour`, but the hour did
    not match the run this league actually observed (`waiverProcessHour` 11 for a
    run at 03:02 ET), so the hour is taken from `waiverLastExecutionDate` and the
    configured days only have to agree with it. Both sources are required: one
    alone would be an assumption about a deadline, which is the thing this field
    exists to avoid.

    Floored to the hour, because a claim deadline that is slightly early is
    useful and one that is slightly late is worse than none at all.
    """
    at = dt.datetime.fromisoformat(at) if isinstance(at, str) else (at or dt.datetime.now(dt.timezone.utc))
    days = {WEEKDAYS[d] for d in (acquisition.get('waiverProcessDays') or []) if d in WEEKDAYS}
    anchor = (dt.datetime.fromtimestamp(last_execution / 1000, dt.timezone.utc).astimezone(ESPN_TZ)
              if last_execution else None)
    if not days or anchor is None or anchor.weekday() not in days:
        return {'at': None, 'verified': False,
                'detail': 'ESPN did not report a waiver schedule and an observed run that agree. '
                          'Confirm the processing time in the league settings before relying on it.'}
    named = ', '.join(name.title() for name, index in sorted(WEEKDAYS.items(), key=lambda kv: kv[1]) if index in days)
    detail = (f'Runs {named} in the {anchor.hour}:00 ET hour, anchored to the last observed ESPN run '
              f'({anchor.strftime("%a %Y-%m-%d %H:%M")} ET). Claims must be in before it. '
              'A single observed run fixes the hour, not the minute.')
    local = at.astimezone(ESPN_TZ)
    for ahead in range(9):
        day = local.date() + dt.timedelta(days=ahead)
        if day.weekday() not in days:
            continue
        # Constructed per date rather than by adding days to a datetime, so the
        # hour stays put across a DST change instead of sliding an hour.
        run = dt.datetime(day.year, day.month, day.day, anchor.hour, tzinfo=ESPN_TZ)
        if run > local:
            return {'at': run.astimezone(dt.timezone.utc).isoformat(), 'verified': True, 'detail': detail}
    return {'at': None, 'verified': False, 'detail': detail}


def reconcile_decision(expects, starters, owned, names=None):
    """Did the roster end up where a briefing decision said it should?

    Only a structured `expects` block is checked. A recommendation written in
    prose alone reports as uncheckable rather than being parsed for intent: a
    wrong "done" badge on a lineup call is worse than no badge at all.
    """
    names = names or {}
    label = lambda pid: names.get(pid, f'Player {pid}')
    checks = []
    for key in EXPECTATIONS:
        for pid in (expects or {}).get(key) or []:
            pid = int(pid)
            if key == 'start':
                checks.append((pid, pid in starters, 'starting'))
            elif key == 'bench':
                checks.append((pid, pid in owned and pid not in starters, 'benched'))
            elif key == 'roster':
                checks.append((pid, pid in owned, 'on the roster'))
            else:
                checks.append((pid, pid not in owned, 'off the roster'))
    if not checks:
        return {'state': 'not checkable',
                'detail': 'This decision records no structured end state, so execution cannot be '
                          'confirmed from the roster.'}
    met = [c for c in checks if c[1]]
    if len(met) == len(checks):
        return {'state': 'executed',
                'detail': 'Roster matches: ' + ', '.join(f'{label(pid)} {word}' for pid, _, word in checks) + '.'}
    outstanding = '; '.join(f'{label(pid)} is not {word}' for pid, ok, word in checks if not ok)
    state = 'partly executed' if met else 'not executed'
    return {'state': state, 'detail': 'Outstanding: ' + outstanding + '.'}


def decision_states(snapshot, decisions):
    """Attach a derived `execution` to each decision, in place."""
    my_id = snapshot.get('league', {}).get('my_team_id')
    team = next((t for t in snapshot.get('teams', []) if t['id'] == my_id), None)
    if team is None:
        return decisions
    # Bench and IR are the only non-starting slots, which is the same rule
    # enrich() uses to build the submitted lineup.
    starters = {p['id'] for p in team['roster'] if p['slot_id'] not in (20, 21)}
    owned = {p['id'] for p in team['roster']}
    names = {p['id']: p['name'] for other in snapshot['teams'] for p in other['roster']}
    names.update({p['id']: p['name'] for p in snapshot.get('free_agents', [])})
    for decision in decisions:
        decision['execution'] = reconcile_decision(decision.get('expects'), starters, owned, names)
    return decisions


def status_label(status):
    return STATUS_LABELS.get(status) or (status or 'Unknown').replace('_', ' ').title()


def team_changes(snapshots, team_id):
    """What changed on one fantasy team across consecutive stored syncs.

    `snapshots` are raw stored payloads, oldest first. A refresh cannot say when
    something happened, only that it happened between two syncs, so each change
    carries the first sync that saw it and the sync before that. Projections are
    compared only inside one scoring week: at a week boundary every projection
    moves, and none of that is news.
    """
    events = []
    for before, after in zip(snapshots, snapshots[1:]):
        old = next((t for t in before.get('teams', []) if t['id'] == team_id), None)
        new = next((t for t in after.get('teams', []) if t['id'] == team_id), None)
        if old is None or new is None:
            continue
        previous = {p['id']: p for p in old['roster']}
        current = {p['id']: p for p in new['roster']}
        found = []
        for pid in sorted(current.keys() - previous.keys()):
            p = current[pid]
            found.append(('added', p, None, p['slot'], f"Added to the roster at {p['slot']}."))
        for pid in sorted(previous.keys() - current.keys()):
            p = previous[pid]
            found.append(('dropped', p, p['slot'], None, f"No longer on the roster (was at {p['slot']})."))
        for pid in sorted(previous.keys() & current.keys(), key=lambda i: (current[i]['slot_id'], i)):
            p, q = previous[pid], current[pid]
            if p.get('status') != q.get('status'):
                found.append(('status', q, p.get('status'), q.get('status'),
                              f"{status_label(p.get('status'))} → {status_label(q.get('status'))}."))
            # With no game, nfl_team falls back to the draft-time team, which would
            # read as a trade every bye week. Only scheduled teams are compared.
            if p.get('kickoff') and q.get('kickoff') and p.get('nfl_team') != q.get('nfl_team'):
                found.append(('nfl_team', q, p.get('nfl_team'), q.get('nfl_team'),
                              f"NFL team {p.get('nfl_team')} → {q.get('nfl_team')}."))
            if p.get('slot') != q.get('slot'):
                found.append(('slot', q, p.get('slot'), q.get('slot'), f"Moved from {p.get('slot')} to {q.get('slot')}."))
            if (before.get('week') == after.get('week') and p.get('projection') is not None
                    and q.get('projection') is not None and abs(q['projection'] - p['projection']) >= PROJECTION_MOVE):
                found.append(('projection', q, round(p['projection'], 1), round(q['projection'], 1),
                              f"ESPN projection {p['projection']:.1f} → {q['projection']:.1f} "
                              f"({q['projection'] - p['projection']:+.1f})."))
        for kind, p, old_value, new_value, detail in found:
            events.append({'id': f"{after['snapshot_id']}-{kind}-{p['id']}", 'kind': kind, 'player_id': p['id'],
                           'name': p['name'], 'pos': p.get('pos'), 'from': old_value, 'to': new_value,
                           'detail': detail, 'week': after.get('week'), 'observed_at': after['data_as_of'],
                           'previous_observed_at': before['data_as_of']})
    # Newest sync first; the sort is stable, so each sync keeps roster order.
    events.sort(key=lambda e: e['observed_at'], reverse=True)
    return events


def roster_alerts(snapshot, team_id):
    """Lineup problems read straight off one enriched snapshot.

    No research and no forecast beyond ESPN's own numbers: an empty starting
    slot, a starter with no game, a starter ESPN lists as unable or unlikely to
    play, an injured-reserve player holding a roster spot, and the gap between
    the submitted lineup and ESPN's strongest legal one. Locked starters are
    skipped, because nothing can change them this week.
    """
    team = next((t for t in snapshot.get('teams', []) if t['id'] == team_id), None)
    if team is None:
        return []
    roster = team['roster']
    by_id = {p['id']: p for p in roster}
    starters = [p for p in roster if p['slot_id'] not in (20, 21)]
    alerts = []

    def alert(key, severity, title, detail, players, act_by=None):
        alerts.append({'id': key, 'severity': severity, 'title': title, 'detail': detail,
                       'player_ids': [p['id'] for p in players], 'act_by': act_by})

    filled = Counter(p['slot_id'] for p in starters)
    missing = [s['label'] for s in snapshot['rules']['lineup_slots']
               for _ in range(max(0, s['count'] - filled.get(s['id'], 0)))]
    if missing:
        alert('empty-slot', 'act', 'Empty starting slot', f"Nothing is starting at {', '.join(missing)}.", [])

    scheduled = any(p.get('kickoff') for p in roster)
    for p in starters:
        if p['locked']:
            continue
        status = p.get('status')
        if status in ACT_STATUSES:
            alert(f"starter-status-{p['id']}", 'act', f"{p['name']} is listed {status_label(status).lower()}",
                  f"Starting at {p['slot']}. Replace before kickoff unless reports confirm availability.",
                  [p], p.get('kickoff'))
        elif status == 'QUESTIONABLE':
            alert(f"starter-status-{p['id']}", 'check', f"{p['name']} is questionable",
                  f"Starting at {p['slot']}. Check the final injury report before kickoff.", [p], p.get('kickoff'))
        # Kickoffs loaded for teammates but not for this player: no game this week.
        if scheduled and not p.get('kickoff'):
            alert(f"no-game-{p['id']}", 'act', f"{p['name']} has no game this week",
                  f"Starting at {p['slot']} with no scheduled NFL game, usually a bye. Start someone who plays.", [p])

    ir_slots = snapshot['rules'].get('ir_slots')
    on_ir = sum(1 for p in roster if p['slot_id'] == 21)
    final = "ESPN's own eligibility check is final."
    for p in roster:
        if p.get('status') != 'INJURY_RESERVE' or p['slot_id'] == 21:
            continue
        if ir_slots is None:
            capacity, room = 'Check how many IR slots are open in ESPN.', True
        elif on_ir >= ir_slots:
            capacity, room = (f'All {ir_slots} IR slots are in use.' if ir_slots else 'This league has no IR slots.'), False
        else:
            capacity, room = f'{ir_slots - on_ir} of {ir_slots} IR slots open.', True
        if not room:
            alert(f"ir-{p['id']}", 'check', f"No open IR slot for {p['name']}",
                  f"ESPN lists injured reserve. {capacity} The player is holding a roster spot at {p['slot']}.", [p])
        elif p['locked']:
            alert(f"ir-{p['id']}", 'later', f"Move {p['name']} to IR once the lineup unlocks",
                  f"ESPN lists injured reserve. The {p['slot']} slot is locked for this week. {capacity} "
                  f"Moving frees a roster spot; {final}", [p])
        else:
            alert(f"ir-{p['id']}", 'act', f"Move {p['name']} to IR",
                  f"ESPN lists injured reserve and the player is at {p['slot']}. {capacity} "
                  f"Moving frees a roster spot; {final}", [p])

    submitted, best = team.get('submitted') or {}, team.get('recommended') or {}
    if submitted.get('remaining_projection') is not None and best.get('remaining_projection') is not None:
        gain = best['remaining_projection'] - submitted['remaining_projection']
        chosen = {a['player_id'] for a in submitted.get('assignments', [])}
        preferred = {a['player_id'] for a in best.get('assignments', [])}
        ranked = lambda ids: sorted((by_id[i] for i in ids if i in by_id), key=lambda p: -(p['projection'] or 0))
        ins, outs = ranked(preferred - chosen), ranked(chosen - preferred)
        if gain >= LINEUP_GAIN and ins:
            names = lambda players: ' and '.join(p['name'] for p in players)
            lean = gain < LINEUP_ACT
            alert('lineup-gap', 'check' if lean else 'act',
                  f"Start {names(ins)} over {names(outs)}" if outs else f"Start {names(ins)}",
                  f"ESPN projects +{gain:.1f} points for its strongest legal lineup. This is ESPN's baseline, "
                  "not researched advice" + ("; a gain this small is a lean, so check news before switching." if lean else "."),
                  ins + outs, min((p['kickoff'] for p in ins + outs if p.get('kickoff')), default=None))

    rank = {'act': 0, 'check': 1, 'later': 2}
    alerts.sort(key=lambda a: (rank[a['severity']], a['act_by'] or '9999'))
    return alerts


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
    waivers = waiver_window(settings.get('acquisitionSettings', {}), data.get('status', {}).get('waiverLastExecutionDate'), observed)
    ir_slots = settings['rosterSettings']['lineupSlotCounts'].get('21')
    rules = {'lineup_slots': slots, 'ir_slots': int(ir_slots) if ir_slots is not None else None,
             'waiver_priority': next(t['waiver_priority'] for t in teams if t['id'] == my_id),
             'waiver_hours': settings.get('acquisitionSettings', {}).get('waiverHours'),
             'waiver_timing_verified': waivers['verified'],
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
    deadlines = [{'id': 'waivers', 'label': 'Waiver review', 'at': waivers['at'], 'verified': waivers['verified'],
                  'detail': waivers['detail'] + f" Waiver period is {rules['waiver_hours']}h; an individual player's clearance can be later than the next run."}]
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
        # Each briefed week is reconciled against its OWN latest snapshot, so a
        # call made in week 3 is judged by week 3's roster rather than today's.
        week_rosters = {w: conn.execute('SELECT payload FROM snapshots WHERE season=? AND week=? ORDER BY created DESC LIMIT 1',
                                        (season, w)).fetchone() for w, _, _ in archive}
        # This week's syncs plus the last one before the week, so a change made
        # between weeks is still reported once.
        synced = conn.execute('SELECT payload FROM snapshots WHERE season=? AND week=? ORDER BY created', (season, week)).fetchall()
        before = conn.execute('SELECT payload FROM snapshots WHERE season=? AND week<? ORDER BY week DESC, created DESC LIMIT 1',
                              (season, week)).fetchone()
    result = enrich(json.loads(row[0]))
    # Both are derived on every read and never stored: they are ESPN's data
    # restated, not research.
    my_id = result.get('league', {}).get('my_team_id')
    syncs = [json.loads(r[0]) for r in ([before] if before else []) + synced]
    result['team_changes'] = {'team_id': my_id, 'since': syncs[0]['data_as_of'], 'until': result['data_as_of'],
                              'syncs_compared': len(syncs), 'events': team_changes(syncs, my_id)}
    result['attention'] = roster_alerts(result, my_id)
    result['generated_at'] = now()
    result['stale'] = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(result['data_as_of'])).total_seconds() > 900
    if error and error[0] > result['data_as_of']:
        result['stale'] = True
        result['warnings'].append('Latest refresh failed; displaying the last successful snapshot. ' + error[1])
    history = []
    for w, created, payload in archive:
        decisions = json.loads(payload).get('decisions', [])
        stored = week_rosters.get(w)
        if stored:
            decision_states(json.loads(stored[0]), decisions)
        history.append({'week': w, 'generated_at': created, 'current_week': w == week,
                        'decisions': [{k: d.get(k) for k in ('id', 'title', 'recommendation', 'status', 'flip_condition', 'execution')}
                                      for d in decisions]})
    result['decision_history'] = history
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
        # Derived at read time, never written back: the stored briefing stays the
        # research as written, and the badge always reflects the current roster.
        decision_states(result, result['briefing'].get('decisions', []))
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
    for decision in payload['decisions']:
        # An `expects` block is optional, but a malformed one must fail here:
        # silently ignored, it would read as "cannot be checked" forever.
        expects = decision.get('expects')
        if expects is None:
            continue
        if not isinstance(expects, dict) or not set(expects) <= set(EXPECTATIONS):
            raise ValueError(f"Decision '{decision.get('id')}' expects must be an object using only: " + ', '.join(EXPECTATIONS))
        for key, ids in expects.items():
            if not isinstance(ids, list) or not all(isinstance(pid, int) for pid in ids):
                raise ValueError(f"Decision '{decision.get('id')}' expects.{key} must be a list of player ids")
    instant(payload['generated_at'])
    with connect() as conn:
        conn.execute('INSERT OR REPLACE INTO briefings VALUES (?,?,?,?)', (payload['season'], payload['week'], payload['generated_at'], json.dumps(payload)))
    return payload
