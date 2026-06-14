"""
ingest_bulk.py - High-Performance Bulk Ingestion (Crash-Safe & Resumable)
   • Pre-warms caches from DB (eliminates millions of SELECT queries)
   • No transaction wrapper → partial data survives Ctrl+C
   • Uses COPY + staging table for deliveries (5-10x faster than executemany)
   • Releases DB connections during HTTP fetches
   • Batches athlete/team resolution per match
"""
import asyncio
import aiohttp
import asyncpg
import re
import os
import json
import logging
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# ── Global caches (pre-warmed at startup) ────────────────────────────────────
cached_athletes = set()
cached_teams = set()
cached_venues = set()
cache_lock = asyncio.Lock()

# ── Progress counters ────────────────────────────────────────────────────────
progress = {'done': 0, 'total': 0, 'start': 0.0}

# ── Helpers ──────────────────────────────────────────────────────────────────

def safe_int(val, default=None):
    try: return int(float(val))
    except (TypeError, ValueError): return default

def safe_float(val, default=None):
    try: return float(val)
    except (TypeError, ValueError): return default

def safe_str(val):
    if val is None: return None
    if isinstance(val, dict): return str(val.get('displayValue', val))
    return str(val)

def safe_bool(val, default=False):
    if val is None: return default
    if isinstance(val, str): return val.lower() in ('true', '1', 't', 'y', 'yes')
    return bool(val)

def safe_date(val):
    if not val: return None
    for fmt in ('%Y-%m-%dT%H:%M%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S'):
        try: return datetime.strptime(val.replace('Z', '+0000'), fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except: return None

def extract_id_from_ref(ref_dict):
    if not ref_dict: return None
    url = ref_dict.get('$ref', '') if isinstance(ref_dict, dict) else str(ref_dict)
    m = re.search(r'/(\d+)/?$', url.split('?')[0])
    if m and m.group(1) != '0': return m.group(1)
    return None

def extract_id_from_url(url):
    if not url: return None
    m = re.search(r'/(\d+)/?$', str(url).split('?')[0])
    if m and m.group(1) != '0': return m.group(1)
    return None

# ── HTTP fetch with retry ────────────────────────────────────────────────────

http_semaphore = asyncio.Semaphore(250)

async def fetch(session, url, retries=4):
    if not url: return None
    for attempt in range(retries):
        status = None
        try:
            async with http_semaphore:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    status = resp.status
                    if status == 200:
                        return await resp.json()
        except Exception as e:
            if attempt == retries - 1:
                log.warning(f"Fetch failed: {url} -> {e}")

        # Sleep OUTSIDE the semaphore so other tasks can use it
        if status in (429, 502, 503, 504) or status is None:
            await asyncio.sleep(attempt + 1)

    return None

# ── Batch ensure functions (no DB SELECT, just fetch-and-insert unknown) ─────

async def batch_ensure_athletes(pool, session, aids):
    """Fetch and insert any athlete IDs not already in cache. Returns set of valid IDs."""
    aids = {a for a in aids if a}
    unknown = aids - cached_athletes
    if not unknown:
        return aids & cached_athletes  # all known

    # Fetch all unknown athletes concurrently
    tasks = {aid: fetch(session, f"http://core.espnuk.org/v2/sports/cricket/athletes/{aid}") for aid in unknown}
    results = await asyncio.gather(*tasks.values())
    
    tuples = []
    newly_cached = set()
    for aid, a_data in zip(tasks.keys(), results):
        if not a_data: continue
        bat_s = bowl_s = None
        for s in a_data.get('styles', []):
            if s.get('type') == 'batting': bat_s = s.get('description')
            if s.get('type') == 'bowling': bowl_s = s.get('description')
        c = a_data.get('country')
        country = c.get('abbreviation', c.get('name')) if isinstance(c, dict) else (str(c) if c else None)
        tuples.append((
            aid, a_data.get('fullName'), a_data.get('shortName'), country,
            safe_date(a_data.get('dateOfBirth')), a_data.get('gender'),
            a_data.get('headshot', {}).get('href'),
            bat_s, bowl_s, a_data.get('position', {}).get('name'), safe_bool(a_data.get('active'))
        ))
        newly_cached.add(aid)
    
    if tuples:
        async with pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO cricket.athletes (id, full_name, short_name, country_code, date_of_birth, gender, image_url,
                    batting_style, bowling_style, position, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET full_name=EXCLUDED.full_name, country_code=EXCLUDED.country_code,
                    date_of_birth=EXCLUDED.date_of_birth, gender=EXCLUDED.gender, image_url=EXCLUDED.image_url,
                    batting_style=EXCLUDED.batting_style, bowling_style=EXCLUDED.bowling_style
            """, tuples)
    
    async with cache_lock:
        cached_athletes.update(newly_cached)
    
    return (aids & cached_athletes) | newly_cached


async def ensure_single_athlete(pool, session, aid):
    """For one-off athlete lookups (e.g. POTM). Returns aid if valid, else None."""
    if not aid: return None
    if aid in cached_athletes: return aid
    result = await batch_ensure_athletes(pool, session, {aid})
    return aid if aid in result else None


async def ensure_venue(pool, session, venue_id, venue_ref):
    if not venue_id: return None
    if venue_id in cached_venues: return venue_id
    try:
        v_data = await fetch(session, venue_ref)
        if v_data:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO cricket.venues (id, full_name, short_name, city, state, country, capacity, grass, indoor, address_summary)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO UPDATE SET full_name=EXCLUDED.full_name, city=EXCLUDED.city, state=EXCLUDED.state, country=EXCLUDED.country, capacity=EXCLUDED.capacity, grass=EXCLUDED.grass, indoor=EXCLUDED.indoor, address_summary=EXCLUDED.address_summary
                """, str(v_data['id']), v_data.get('fullName'), v_data.get('shortName'),
                     v_data.get('address', {}).get('city'), v_data.get('address', {}).get('state'),
                     v_data.get('address', {}).get('country'),
                     safe_int(v_data.get('capacity')), safe_bool(v_data.get('grass')), safe_bool(v_data.get('indoor')),
                     v_data.get('address', {}).get('summary'))
            async with cache_lock:
                cached_venues.add(venue_id)
            return venue_id
    except Exception as e:
        log.error(f"Failed ensuring venue {venue_id}: {e}")
    return None


async def ensure_team(pool, session, team_id, team_ref):
    if not team_id: return None
    if team_id in cached_teams: return team_id
    try:
        t_data = await fetch(session, team_ref)
        if t_data:
            async with pool.acquire() as conn:
                logo_url = t_data.get('logos', [{}])[0].get('href') if t_data.get('logos') else None
                await conn.execute("""
                    INSERT INTO cricket.teams (id, name, short_display_name, abbreviation, is_national,
                        display_name, location, nickname, color, is_active, slug, country_code, logo_url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, display_name=EXCLUDED.display_name,
                        country_code=EXCLUDED.country_code, logo_url=EXCLUDED.logo_url
                """, str(t_data['id']), t_data.get('name'),
                     t_data.get('shortDisplayName', t_data.get('shortName')),
                     t_data.get('abbreviation'), safe_bool(t_data.get('isNational')),
                     t_data.get('displayName'), t_data.get('location'),
                     t_data.get('nickname'), t_data.get('color'),
                     safe_bool(t_data.get('isActive')), t_data.get('slug'),
                     t_data.get('countryCode'), logo_url)
            async with cache_lock:
                cached_teams.add(team_id)
            return team_id
    except Exception as e:
        log.error(f"Failed ensuring team {team_id}: {e}")
    return None


# ── COPY-based bulk delivery insert ──────────────────────────────────────────

DELIVERY_COLUMNS = [
    'id', 'competition_id', 'sequence', 'bbb_timestamp', 'date',
    'period', 'period_text', 'over_number', 'ball_in_over', 'overs_actual',
    'batsman_id', 'non_striker_id', 'bowler_id', 'other_bowler_id',
    'batting_team_id', 'bowling_team_id',
    'runs_scored', 'is_boundary', 'play_type_id', 'play_type_desc',
    'text', 'short_text',
    'is_wide', 'is_no_ball', 'is_bye', 'is_leg_bye',
    'speed_kph', 'speed_mph', 'x_coordinate', 'y_coordinate', 'hawkeye_id',
    'batsman_runs', 'batsman_balls_faced', 'batsman_fours', 'batsman_sixes',
    'bowler_overs', 'bowler_maidens', 'bowler_wickets', 'bowler_conceded',
    'team_score', 'innings_runs', 'innings_wickets', 'innings_run_rate',
    'innings_required_rr', 'innings_target', 'innings_session', 'innings_day',
    'innings_lead_by', 'innings_trail_by',
    'over_runs', 'over_wickets', 'over_maiden', 'over_complete'
]

DISMISSAL_COLUMNS = [
    'delivery_id', 'type', 'batsman_id', 'bowler_id', 'fielder_id',
    'is_keeper', 'text', 'minutes', 'is_bowled', 'bbb_timestamp'
]

async def bulk_insert_deliveries(pool, delivery_tuples, dismissal_tuples):
    """Use COPY + staging table for maximum insert speed."""
    if not delivery_tuples and not dismissal_tuples:
        return
    
    async with pool.acquire() as conn:
        async with conn.transaction():
            if delivery_tuples:
                await conn.execute("""
                    CREATE TEMP TABLE _stg_deliveries (LIKE cricket.deliveries INCLUDING DEFAULTS)
                    ON COMMIT DROP
                """)
                await conn.copy_records_to_table(
                    '_stg_deliveries', records=delivery_tuples, columns=DELIVERY_COLUMNS
                )
                cols = ', '.join(DELIVERY_COLUMNS)
                placeholders = ', '.join(f's.{c}' for c in DELIVERY_COLUMNS)
                await conn.execute(f"""
                    INSERT INTO cricket.deliveries ({cols})
                    SELECT {placeholders} FROM _stg_deliveries s
                    ON CONFLICT (id) DO NOTHING
                """)
            
            if dismissal_tuples:
                await conn.execute("""
                    CREATE TEMP TABLE _stg_dismissals (LIKE cricket.dismissals INCLUDING DEFAULTS)
                    ON COMMIT DROP
                """)
                await conn.copy_records_to_table(
                    '_stg_dismissals', records=dismissal_tuples, columns=DISMISSAL_COLUMNS
                )
                cols = ', '.join(DISMISSAL_COLUMNS)
                placeholders = ', '.join(f's.{c}' for c in DISMISSAL_COLUMNS)
                await conn.execute(f"""
                    INSERT INTO cricket.dismissals ({cols})
                    SELECT {placeholders} FROM _stg_dismissals s
                    ON CONFLICT (delivery_id) DO NOTHING
                """)


# ── Main match processing ────────────────────────────────────────────────────

async def process_match(pool, session, event_url, progress_file):
    # ── 1. Fetch event (no DB connection held) ──
    event = await fetch(session, event_url)
    if not event: return
    event_id = str(event['id'])
    
    if not event.get('competitions'): 
        # Still save the event itself
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO cricket.events (id, uid, name, short_name, date, end_date, description, time_valid, api_ref)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, short_name=EXCLUDED.short_name, 
                    date=EXCLUDED.date, end_date=EXCLUDED.end_date, description=EXCLUDED.description, 
                    time_valid=EXCLUDED.time_valid, api_ref=EXCLUDED.api_ref
            """, event_id, event.get('uid', f's:200~e:{event_id}'),
                 safe_str(event.get('name')), safe_str(event.get('shortName')),
                 safe_date(event.get('date')), safe_date(event.get('endDate')),
                 safe_str(event.get('description')), event.get('timeValid'), event.get('$ref'))
        progress_file.write(event_url + '\n')
        progress_file.flush()
        return

    comp = event['competitions'][0]
    comp_id = str(comp['id'])

    # ── 2. Fetch ALL HTTP data first (no DB connection held) ──
    league_tasks = [fetch(session, le.get('$ref')) for le in event.get('leagues', [])]
    league_results = await asyncio.gather(*league_tasks) if league_tasks else []
    
    status_data, officials_data, mc_data = await asyncio.gather(
        fetch(session, comp.get('status', {}).get('$ref')),
        fetch(session, comp.get('officials', {}).get('$ref')),
        fetch(session, comp.get('matchcards', {}).get('$ref')),
    )
    
    # Competitors: fetch rosters + linescores concurrently
    competitor_tasks = []
    roster_coros = []
    linescore_coros = []
    for competitor in comp.get('competitors', []):
        competitor_tasks.append({'competitor': competitor})
        roster_coros.append(fetch(session, competitor.get('roster', {}).get('$ref')))
        linescore_coros.append(fetch(session, competitor.get('linescores', {}).get('$ref')))
    
    all_comp_results = await asyncio.gather(*roster_coros, *linescore_coros) if competitor_tasks else []
    num_competitors = len(competitor_tasks)
    roster_results = list(all_comp_results[:num_competitors])
    linescore_results = list(all_comp_results[num_competitors:])

    # ── 3. Ensure venue ──
    venue_id = extract_id_from_ref(comp.get('venue'))
    venue_id = await ensure_venue(pool, session, venue_id, comp.get('venue', {}).get('$ref'))

    # ── 4. Ensure teams ──
    for ct in competitor_tasks:
        c = ct['competitor']
        tid = extract_id_from_ref(c.get('team'))
        ct['team_id'] = await ensure_team(pool, session, tid, c.get('team', {}).get('$ref'))

    # ── 5. Collect ALL athlete IDs from rosters and batch-ensure them ──
    all_athlete_ids = set()
    for i, ct in enumerate(competitor_tasks):
        r_data = roster_results[i]
        if r_data and 'entries' in r_data:
            for entry in r_data['entries']:
                aid = extract_id_from_url(entry.get('athlete', {}).get('$ref'))
                if aid: all_athlete_ids.add(aid)
    
    await batch_ensure_athletes(pool, session, all_athlete_ids)

    # ── 6. Insert event + leagues + competition + officials + competitors ──
    async with pool.acquire() as conn:
        # Event
        await conn.execute("""
            INSERT INTO cricket.events (id, uid, name, short_name, date, end_date, description, time_valid, api_ref)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, short_name=EXCLUDED.short_name, 
                date=EXCLUDED.date, end_date=EXCLUDED.end_date, description=EXCLUDED.description, 
                time_valid=EXCLUDED.time_valid, api_ref=EXCLUDED.api_ref
        """, event_id, safe_str(event.get('uid', f's:200~e:{event_id}')),
             safe_str(event.get('name')), safe_str(event.get('shortName')),
             safe_date(event.get('date')), safe_date(event.get('endDate')),
             safe_str(event.get('description')), safe_bool(event.get('timeValid')), safe_str(event.get('$ref')))
        
        # Leagues
        for league_entry, league_data in zip(event.get('leagues', []), league_results):
            if not league_data: continue
            lid = str(league_data['id'])
            await conn.execute("""
                INSERT INTO cricket.leagues (id, name, is_tournament, league_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name
            """, lid, safe_str(league_data.get('name')), safe_bool(league_data.get('isTournament')),
                 safe_str(league_entry.get('leagueType')))
            await conn.execute("""
                INSERT INTO cricket.event_leagues (event_id, league_id, league_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (event_id, league_id) DO NOTHING
            """, event_id, lid, safe_str(league_entry.get('leagueType')))
        
        # Competition
        await conn.execute("""
            INSERT INTO cricket.competitions (id, event_id, date, end_date, venue_id, class_name,
                neutral_site, day_night, limited_overs, attendance, play_by_play_available)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id) DO NOTHING
        """, comp_id, event_id, safe_date(comp.get('date')), safe_date(comp.get('endDate')),
             venue_id, safe_str(comp.get('class', {}).get('generalClassCard')),
             safe_bool(comp.get('neutralSite')), safe_bool(comp.get('dayNight')), safe_bool(comp.get('limitedOvers')),
             safe_int(comp.get('attendance')), safe_bool(comp.get('playByPlayAvailable')))

        # Officials (batched)
        if officials_data and 'items' in officials_data:
            existing = await conn.fetchval(
                "SELECT COUNT(*) FROM cricket.match_officials WHERE competition_id=$1", comp_id)
            if existing == 0:
                off_tuples = [(comp_id, safe_str(off.get('displayName')), safe_str(off.get('firstName')),
                              safe_str(off.get('lastName')), safe_str(off.get('flag', {}).get('alt')),
                              safe_str(off.get('position', {}).get('displayName')))
                             for off in officials_data['items']]
                await conn.executemany("""
                    INSERT INTO cricket.match_officials (competition_id, display_name, first_name,
                        last_name, country, role)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, off_tuples)
        
        # Competitors + Innings
        db_competitor_ids = {}
        pending_partnerships = []
        pending_fows = []
        for i, ct in enumerate(competitor_tasks):
            competitor = ct['competitor']
            espn_comp_id = str(competitor.get('id'))
            
            score_val = competitor.get('score')
            if isinstance(score_val, dict): score_val = score_val.get('displayValue', str(score_val))
            elif score_val is not None: score_val = str(score_val)
            if score_val: score_val = score_val[:95]
            
            row = await conn.fetchrow("""
                INSERT INTO cricket.competitors (espn_competitor_id, competition_id, team_id,
                    home_away, winner, score_value)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (competition_id, espn_competitor_id) DO UPDATE SET team_id=EXCLUDED.team_id
                RETURNING id
            """, espn_comp_id, comp_id, ct['team_id'],
                 safe_str(competitor.get('homeAway')), safe_bool(competitor.get('winner')), safe_str(score_val))
            db_competitor_id = row['id']
            db_competitor_ids[espn_comp_id] = db_competitor_id
            
            # Innings
            ls_data = linescore_results[i]
            if ls_data and 'items' in ls_data:
                for item in ls_data['items']:
                    period = safe_int(item.get('period'))
                    if period is None: continue
                    
                    inn_row = await conn.fetchrow("""
                        INSERT INTO cricket.innings (competitor_id, period, runs, wickets, overs,
                            fours, sixes, score, description, is_batting, is_current, target, follow_on)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (competitor_id, period) DO UPDATE SET
                            runs=EXCLUDED.runs, wickets=EXCLUDED.wickets, score=EXCLUDED.score
                        RETURNING id
                    """, db_competitor_id, period,
                         safe_int(item.get('runs')), safe_int(item.get('wickets')),
                         safe_float(item.get('overs')), safe_int(item.get('fours')),
                         safe_int(item.get('sixes')), safe_str(item.get('score')),
                         safe_str(item.get('description')), safe_bool(item.get('isBatting', False)),
                         safe_bool(item.get('isCurrent')), safe_int(item.get('target')),
                         safe_bool(item.get('followOn')))
                    db_innings_id = inn_row['id']
                    
                    # Collect partnership and FOW refs for concurrent fetching later
                    pending_partnerships.append((db_innings_id, item.get('partnerships', {}).get('$ref')))
                    pending_fows.append((db_innings_id, item.get('fow', {}).get('$ref')))

    # ── Partnership/FOW HTTP fetches (OUTSIDE pool.acquire — no DB connection held) ──
    all_p_list_coros = [fetch(session, ref) for _, ref in pending_partnerships]
    all_fow_list_coros = [fetch(session, ref) for _, ref in pending_fows]
    all_p_lists = await asyncio.gather(*all_p_list_coros) if all_p_list_coros else []
    all_fow_lists = await asyncio.gather(*all_fow_list_coros) if all_fow_lists else []

    # Fetch individual partnership and FOW details concurrently
    p_detail_coros = []
    p_detail_map = []  # (innings_id, index_range)
    for (db_innings_id, _), p_list_data in zip(pending_partnerships, all_p_lists):
        if p_list_data and 'items' in p_list_data:
            refs = [pi.get('$ref') for pi in p_list_data['items'] if pi.get('$ref')]
            start_idx = len(p_detail_coros)
            p_detail_coros.extend([fetch(session, r) for r in refs])
            p_detail_map.append((db_innings_id, start_idx, len(p_detail_coros)))
        else:
            p_detail_map.append((db_innings_id, 0, 0))

    fow_detail_coros = []
    fow_detail_map = []
    for (db_innings_id, _), fow_list in zip(pending_fows, all_fow_lists):
        if fow_list and 'items' in fow_list:
            refs = [fi.get('$ref') for fi in fow_list['items'] if fi.get('$ref')]
            start_idx = len(fow_detail_coros)
            fow_detail_coros.extend([fetch(session, r) for r in refs])
            fow_detail_map.append((db_innings_id, start_idx, len(fow_detail_coros)))
        else:
            fow_detail_map.append((db_innings_id, 0, 0))

    all_p_details = await asyncio.gather(*p_detail_coros) if p_detail_coros else []
    all_fow_details = await asyncio.gather(*fow_detail_coros) if fow_detail_coros else []

    # Ensure partnership batsmen
    p_athlete_ids = set()
    for p in all_p_details:
        if not p: continue
        for b in p.get('batsmen', []):
            aid = extract_id_from_url(b.get('athlete'))
            if aid: p_athlete_ids.add(aid)

    # Also collect ALL matchcard athlete IDs to batch-ensure once
    mc_all_aids = set()
    if mc_data and 'items' in mc_data:
        for mc in mc_data['items']:
            for pd_item in mc.get('playerDetails', []):
                pid = extract_id_from_url(pd_item.get('href')) or pd_item.get('playerID')
                if pid: mc_all_aids.add(pid)

    # Single batch ensure for partnership + matchcard athletes
    all_extra_aids = p_athlete_ids | mc_all_aids
    valid_p_athletes = await batch_ensure_athletes(pool, session, all_extra_aids)

    # ── Insert partnerships and FOW (new DB connection) ──
    if pending_partnerships or pending_fows:
      async with pool.acquire() as conn2:
            for db_innings_id, start_idx, end_idx in p_detail_map:
                for p in all_p_details[start_idx:end_idx]:
                    if not p: continue
                    wn = safe_int(p.get('wicketNumber'))
                    if wn is None: continue
                    batsmen = p.get('batsmen', [])
                    b1_id = extract_id_from_url(batsmen[0].get('athlete')) if len(batsmen) > 0 else None
                    b2_id = extract_id_from_url(batsmen[1].get('athlete')) if len(batsmen) > 1 else None
                    b1_id = b1_id if b1_id in valid_p_athletes else None
                    b2_id = b2_id if b2_id in valid_p_athletes else None
                    b1_balls = safe_int(batsmen[0].get('balls')) if len(batsmen) > 0 else None
                    b2_balls = safe_int(batsmen[1].get('balls')) if len(batsmen) > 1 else None
                    await conn2.execute("""
                        INSERT INTO cricket.partnerships (innings_id, wicket_number, runs, balls,
                            batsman_1_id, batsman_2_id, start_overs, start_runs, start_wickets,
                            end_overs, end_runs, end_wickets)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                        ON CONFLICT (innings_id, wicket_number) DO NOTHING
                    """, db_innings_id, wn, safe_int(p.get('runs')), (b1_balls or 0) + (b2_balls or 0),
                         b1_id, b2_id,
                         safe_float(p.get('start', {}).get('overs')), safe_int(p.get('start', {}).get('runs')),
                         safe_int(p.get('start', {}).get('wickets')), safe_float(p.get('end', {}).get('overs')),
                         safe_int(p.get('end', {}).get('runs')), safe_int(p.get('end', {}).get('wickets')))
            
            # Insert FOW
            for db_innings_id, start_idx, end_idx in fow_detail_map:
                for fw in all_fow_details[start_idx:end_idx]:
                    if not fw: continue
                    wn = safe_int(fw.get('wicketNumber'))
                    if wn is None: continue
                    await conn2.execute("""
                        INSERT INTO cricket.fall_of_wickets (innings_id, wicket_number,
                            runs_scored, overs, fow_type)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (innings_id, wicket_number) DO NOTHING
                    """, db_innings_id, wn, safe_int(fw.get('runs')),
                         safe_float(fw.get('wicketOver')), safe_str(fw.get('fowType')))

    # Match status
    if status_data:
        potm_id = None
        for fa in status_data.get('featuredAthletes', []):
            if fa.get('name') == 'playerOfTheMatch':
                potm_id = await ensure_single_athlete(pool, session, str(fa.get('playerId')))

        st = status_data.get('type', {})
        async with pool.acquire() as conn3:
            await conn3.execute("""
                INSERT INTO cricket.match_status (competition_id, state, detail, description, summary,
                    long_summary, period, day_number, potm_athlete_id, start_date, end_date)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (competition_id) DO UPDATE SET 
                    state=EXCLUDED.state, summary=EXCLUDED.summary, long_summary=EXCLUDED.long_summary,
                    start_date=EXCLUDED.start_date, end_date=EXCLUDED.end_date
            """, comp_id, safe_str(st.get('state')), safe_str(st.get('detail')), safe_str(st.get('description')),
                 safe_str(status_data.get('summary')), safe_str(status_data.get('longSummary')),
                 safe_int(status_data.get('period')), safe_int(status_data.get('dayNumber')),
                 potm_id, safe_date(comp.get('date')), safe_date(comp.get('endDate')))

    # Matchcards (athletes already batch-ensured above)
    if mc_data and 'items' in mc_data:
        async with pool.acquire() as conn4:
            existing_mc = await conn4.fetchval(
                "SELECT COUNT(*) FROM cricket.matchcard_batting WHERE competition_id=$1", comp_id)
            if existing_mc == 0:
                for mc in mc_data['items']:
                    mc_headline = mc.get('headline')
                    inns = safe_int(mc.get('inningsNumber'))
                    team_name = mc.get('teamName')

                    db_competitor_id = await conn4.fetchval("""
                        SELECT c.id FROM cricket.competitors c 
                        JOIN cricket.teams t ON c.team_id = t.id 
                        WHERE c.competition_id=$1 AND t.name=$2
                    """, comp_id, team_name)

                    if mc_headline == 'Batting':
                        valid_mc = valid_p_athletes  # Already batch-ensured above
                        
                        for idx, pd in enumerate(mc.get('playerDetails', [])):
                            pid = extract_id_from_url(pd.get('href')) or pd.get('playerID')
                            pid = pid if pid in valid_mc else None

                            pname = pd.get('playerName')
                            dismissal = pd.get('dismissal')
                            is_captain = '(c)' in pname if pname else False
                            is_keeper = '(wk)' in pname if pname else False

                            await conn4.execute("""
                                INSERT INTO cricket.matchcard_batting (
                                    competition_id, innings_number, team_name, extras, total,
                                    player_id, player_name, dismissal, runs, balls_faced, fours, sixes, strike_rate
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                            """, comp_id, inns, team_name, mc.get('extras'), mc.get('total'), pid, pname, dismissal,
                                 safe_int(pd.get('runs')), safe_int(pd.get('ballsFaced')), safe_int(pd.get('fours')),
                                 safe_int(pd.get('sixes')), safe_float(pd.get('strikeRate')))

                            if db_competitor_id and pid:
                                await conn4.execute("""
                                    INSERT INTO cricket.player_match_performances (
                                        competitor_id, innings_number, is_batting, batting_order,
                                        is_captain, is_keeper, runs, balls_faced, fours, sixes,
                                        strike_rate, minutes, athlete_id, dismissal_type
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                                    ON CONFLICT DO NOTHING
                                """, db_competitor_id, inns, True, idx + 1, is_captain, is_keeper,
                                     safe_int(pd.get('runs')), safe_int(pd.get('ballsFaced')), safe_int(pd.get('fours')),
                                     safe_int(pd.get('sixes')), safe_float(pd.get('strikeRate')), safe_int(pd.get('minutes')), pid, dismissal)
                                     
                    elif mc_headline == 'Bowling':
                        valid_mc = valid_p_athletes  # Already batch-ensured above
                        
                        for pd in mc.get('playerDetails', []):
                            pid = extract_id_from_url(pd.get('href')) or pd.get('playerID')
                            pid = pid if pid in valid_mc else None
                            
                            nbw = pd.get('nbw', '')
                            wides = no_balls = 0
                            if nbw:
                                m_w = re.search(r'(\d+)w', nbw)
                                if m_w: wides = int(m_w.group(1))
                                m_nb = re.search(r'(\d+)nb', nbw)
                                if m_nb: no_balls = int(m_nb.group(1))
                                
                            await conn4.execute("""
                                INSERT INTO cricket.matchcard_bowling (
                                    competition_id, innings_number, team_name,
                                    player_id, player_name, overs, maidens, runs_conceded, wickets,
                                    economy, wides, no_balls
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                            """, comp_id, inns, team_name, pid, pd.get('playerName'), safe_float(pd.get('overs')),
                                 safe_int(pd.get('maidens')), safe_int(pd.get('conceded')), safe_int(pd.get('wickets')),
                                 safe_float(pd.get('economyRate')), wides, no_balls)

                            if db_competitor_id and pid:
                                await conn4.execute("""
                                    INSERT INTO cricket.player_match_performances (
                                        competitor_id, innings_number, is_batting, runs_conceded,
                                        overs_bowled, maidens, wickets, economy_rate, wides, no_balls,
                                        athlete_id
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    ON CONFLICT DO NOTHING
                                """, db_competitor_id, inns, False, safe_int(pd.get('conceded')), safe_float(pd.get('overs')),
                                     safe_int(pd.get('maidens')), safe_int(pd.get('wickets')), safe_float(pd.get('economyRate')), wides, no_balls, pid)

    # ── 7. Deliveries + Dismissals (single-pass fetch, batch ensure, COPY insert) ──
    details_ref = comp.get('details', {}).get('$ref')
    if details_ref:
        all_raw_deliveries = []  # Store raw JSON in memory
        delivery_athlete_ids = set()
        delivery_team_ids = {}  # id -> ref
        
        # Collect all delivery refs first (using large pages)
        all_refs = []
        page = 1
        while True:
            d_data = await fetch(session, f"{details_ref}?page={page}&limit=1000")
            if not d_data or not d_data.get('items'): break
            
            for it in d_data['items']:
                ref = it.get('$ref')
                if ref: all_refs.append(ref)
            
            if d_data.get('pageIndex', 1) >= d_data.get('pageCount', 1): break
            page += 1
        
        # Fire ALL delivery fetches at once (semaphore controls actual concurrency)
        if all_refs:
            del_tasks = [fetch(session, ref) for ref in all_refs]
            deliveries = await asyncio.gather(*del_tasks)
        else:
            deliveries = []
        
        for item in deliveries:
                if not item or not item.get('id'): continue
                all_raw_deliveries.append(item)
                
                batsman = item.get('batsman', {})
                bowler = item.get('bowler', {})
                o_batsman = item.get('otherBatsman', {})
                o_bowler = item.get('otherBowler', {})
                
                for ref in [batsman.get('athlete'), o_batsman.get('athlete'),
                           bowler.get('athlete'), o_bowler.get('athlete')]:
                    aid = extract_id_from_ref(ref)
                    if aid: delivery_athlete_ids.add(aid)
                
                for entity in [batsman, bowler]:
                    tid = extract_id_from_ref(entity.get('team'))
                    if tid and tid not in cached_teams:
                        delivery_team_ids[tid] = entity.get('team', {}).get('$ref')
                
                dismissal = item.get('dismissal')
                if dismissal and dismissal.get('dismissal'):
                    for ref in [dismissal.get('batsman', {}).get('athlete'),
                               dismissal.get('bowler', {}).get('athlete'),
                               dismissal.get('fielder', {}).get('athlete')]:
                        aid = extract_id_from_ref(ref)
                        if aid: delivery_athlete_ids.add(aid)
        
        # Batch-ensure all athletes and teams
        await batch_ensure_athletes(pool, session, delivery_athlete_ids)
        await asyncio.gather(*[
            ensure_team(pool, session, tid, tref)
            for tid, tref in delivery_team_ids.items()
        ])
        
        # Build tuples from cached data (no more HTTP calls)
        delivery_tuples = []
        dismissal_tuples = []
        for item in all_raw_deliveries:
            item_id = f"{comp_id}_{item['id']}"
            over = item.get('over', {})
            innings = item.get('innings', {})
            batsman = item.get('batsman', {})
            bowler = item.get('bowler', {})
            o_batsman = item.get('otherBatsman', {})
            o_bowler = item.get('otherBowler', {})
            
            bat_id = extract_id_from_ref(batsman.get('athlete'))
            n_str_id = extract_id_from_ref(o_batsman.get('athlete'))
            bowl_id = extract_id_from_ref(bowler.get('athlete'))
            o_bowl_id = extract_id_from_ref(o_bowler.get('athlete'))
            bat_team_id = extract_id_from_ref(batsman.get('team'))
            bowl_team_id = extract_id_from_ref(bowler.get('team'))
            
            bat_id = bat_id if bat_id in cached_athletes else None
            n_str_id = n_str_id if n_str_id in cached_athletes else None
            bowl_id = bowl_id if bowl_id in cached_athletes else None
            o_bowl_id = o_bowl_id if o_bowl_id in cached_athletes else None
            bat_team_id = bat_team_id if bat_team_id in cached_teams else None
            bowl_team_id = bowl_team_id if bowl_team_id in cached_teams else None
            
            delivery_tuples.append((
                 item_id, comp_id, safe_int(item.get('sequence')),
                 safe_int(item.get('bbbTimestamp')), safe_date(item.get('date')),
                 safe_int(item.get('period')), safe_str(item.get('periodText')),
                 safe_int(over.get('number')), safe_int(over.get('ball')),
                 safe_float(over.get('actual')),
                 bat_id, n_str_id, bowl_id, o_bowl_id, bat_team_id, bowl_team_id,
                 safe_int(item.get('scoreValue')), safe_bool(item.get('boundary')),
                 safe_str(item.get('playType', {}).get('id')), safe_str(item.get('playType', {}).get('description')),
                 safe_str(item.get('text')), safe_str(item.get('shortText')),
                 safe_bool(over.get('wide', 0) > 0), safe_bool(over.get('noBall', 0) > 0),
                 safe_bool(over.get('byes', 0) > 0), safe_bool(over.get('legByes', 0) > 0),
                 safe_float(item.get('speedKPH')), safe_float(item.get('speedMPH')),
                 safe_float(item.get('xCoordinate')), safe_float(item.get('yCoordinate')),
                 safe_str(item.get('hawkeyeId')),
                 safe_int(batsman.get('runs')), safe_int(batsman.get('faced')),
                 safe_int(batsman.get('fours')), safe_int(batsman.get('sixes')),
                 safe_float(bowler.get('overs')), safe_int(bowler.get('maidens')),
                 safe_int(bowler.get('wickets')), safe_int(bowler.get('conceded')),
                 safe_str(item.get('homeScore')),
                 safe_int(innings.get('runs')), safe_int(innings.get('wickets')),
                 safe_float(innings.get('runRate')), safe_float(innings.get('requiredRunRate')),
                 safe_int(innings.get('target')), safe_int(innings.get('session')), safe_int(innings.get('day')),
                 safe_int(innings.get('leadBy')), safe_int(innings.get('trailBy')),
                 safe_int(over.get('runs')), safe_int(over.get('wickets')),
                 safe_bool(over.get('maiden')), safe_bool(over.get('complete'))
            ))
            
            dismissal = item.get('dismissal')
            if dismissal and dismissal.get('dismissal'):
                d_bat_id = extract_id_from_ref(dismissal.get('batsman', {}).get('athlete'))
                d_bowl_id = extract_id_from_ref(dismissal.get('bowler', {}).get('athlete'))
                d_field_id = extract_id_from_ref(dismissal.get('fielder', {}).get('athlete'))
                
                d_bat_id = d_bat_id if d_bat_id in cached_athletes else None
                d_bowl_id = d_bowl_id if d_bowl_id in cached_athletes else None
                d_field_id = d_field_id if d_field_id in cached_athletes else None
                
                dismissal_tuples.append((
                     item_id, safe_str(dismissal.get('type')), d_bat_id, d_bowl_id, d_field_id,
                     safe_bool(dismissal.get('fielder', {}).get('isKeeper')),
                     safe_str(dismissal.get('text')), safe_int(dismissal.get('minutes')),
                     safe_bool(dismissal.get('bowled')), safe_int(item.get('bbbTimestamp'))
                ))
        
        # Bulk insert via COPY
        if delivery_tuples or dismissal_tuples:
            await bulk_insert_deliveries(pool, delivery_tuples, dismissal_tuples)

    # ── 8. Mark as complete ──
    progress_file.write(event_url + '\n')
    progress_file.flush()


# ── Worker + Main ────────────────────────────────────────────────────────────

async def worker(pool, session, queue, progress_file, worker_id):
    while True:
        try:
            event_url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        
        try:
            await asyncio.wait_for(
                process_match(pool, session, event_url, progress_file),
                timeout=300  # 5 minutes — enough for large matches with 700+ HTTP requests
            )
            progress['done'] += 1
            elapsed = time.time() - progress['start']
            rate = progress['done'] / elapsed * 60 if elapsed > 0 else 0
            remaining = progress['total'] - progress['done']
            eta_min = remaining / rate if rate > 0 else 0
            eta_h, eta_m = divmod(int(eta_min), 60)
            log.info(f"[W{worker_id:02d}] ✓ {progress['done']}/{progress['total']} "
                     f"| {rate:.0f}/min | ETA: {eta_h}h {eta_m}m | Q: {queue.qsize()}")
        except asyncio.TimeoutError:
            log.warning(f"[W{worker_id:02d}] ⏰ TIMEOUT (90s) - skipped: {event_url}")
        except Exception as e:
            log.error(f"[W{worker_id:02d}] ✗ {event_url}: {e}")
        finally:
            queue.task_done()


async def main():
    parser = argparse.ArgumentParser(description="Bulk Ingest Cricket Data")
    parser.add_argument('--shard', type=int, default=1, help='Which shard this instance is processing (1-indexed)')
    parser.add_argument('--total-shards', type=int, default=1, help='Total number of instances running')
    args = parser.parse_args()

    try:
        with open('events.json', 'r', encoding='utf-8') as f:
            all_events = json.load(f)
            
        # Sharding logic: only keep events assigned to this VM
        if args.total_shards > 1:
            if args.shard < 1 or args.shard > args.total_shards:
                log.error(f"Invalid shard number: {args.shard}. Must be between 1 and {args.total_shards}")
                return
            
            # Use modulo arithmetic to evenly distribute events
            # e.g., if total=4, shard 1 gets 0, 4, 8... shard 2 gets 1, 5, 9...
            shard_index = args.shard - 1
            all_events = [e for i, e in enumerate(all_events) if i % args.total_shards == shard_index]
            log.info(f"Sharding enabled: Processing shard {args.shard} of {args.total_shards} ({len(all_events)} events assigned to this VM)")
            
    except FileNotFoundError:
        log.error("events.json not found")
        return
        
    completed_events = set()
    try:
        with open('completed_events.txt', 'r', encoding='utf-8') as f:
            completed_events = set(line.strip() for line in f if line.strip())
    except FileNotFoundError: pass
        
    queue = asyncio.Queue()
    for event_url in all_events:
        if event_url not in completed_events: queue.put_nowait(event_url)
            
    progress['total'] = queue.qsize()
    progress['start'] = time.time()
    
    log.info(f"Total events: {len(all_events)}")
    log.info(f"Already completed: {len(completed_events)}")
    log.info(f"To process: {progress['total']}")
    if progress['total'] == 0: return

    db_url = os.getenv("DATABASE_URL")
    pool = await asyncpg.create_pool(db_url, min_size=20, max_size=50)
    
    # ── Pre-warm caches ──
    log.info("Pre-warming caches from DB...")
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM cricket.athletes")
        cached_athletes.update(r['id'] for r in rows)
        rows = await conn.fetch("SELECT id FROM cricket.teams")
        cached_teams.update(r['id'] for r in rows)
        rows = await conn.fetch("SELECT id FROM cricket.venues")
        cached_venues.update(r['id'] for r in rows)
    log.info(f"  Cached: {len(cached_athletes)} athletes, {len(cached_teams)} teams, {len(cached_venues)} venues")
    
    progress_file = open('completed_events.txt', 'a', encoding='utf-8')
    connector = aiohttp.TCPConnector(limit=300, ttl_dns_cache=300, enable_cleanup_closed=True)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        workers = [asyncio.create_task(worker(pool, session, queue, progress_file, i)) for i in range(40)]
        await asyncio.gather(*workers)
        
    progress_file.close()
    await pool.close()
    
    elapsed = time.time() - progress['start']
    log.info(f"Done! Processed {progress['done']} events in {elapsed/60:.1f} minutes")

if __name__ == '__main__':
    asyncio.run(main())
