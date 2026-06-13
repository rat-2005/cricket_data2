"""
ingest_sample.py - Self-contained ingestion for The Ashes 2023, 1st Test.
Populates all 18 cricket schema tables from the ESPN API.
"""
import asyncio
import aiohttp
import asyncpg
import re
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def safe_int(val, default=None):
    try: return int(float(val))
    except (TypeError, ValueError): return default

def safe_float(val, default=None):
    try: return float(val)
    except (TypeError, ValueError): return default

def safe_date(val):
    if not val: return None
    for fmt in ('%Y-%m-%dT%H:%M%z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d %H:%M:%S'):
        try: return datetime.strptime(val.replace('Z', '+0000'), fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except: return None

def extract_id_from_ref(ref_dict):
    """Extract numeric ID from {'$ref': 'http://.../12345'} dicts."""
    if not ref_dict: return None
    url = ref_dict.get('$ref', '') if isinstance(ref_dict, dict) else str(ref_dict)
    m = re.search(r'/(\d+)/?$', url.split('?')[0])
    if m and m.group(1) != '0':
        return m.group(1)
    return None

def extract_id_from_url(url):
    """Extract numeric ID from a plain URL string."""
    if not url: return None
    m = re.search(r'/(\d+)/?$', str(url).split('?')[0])
    if m and m.group(1) != '0':
        return m.group(1)
    return None

# ── Async fetch with semaphore ───────────────────────────────────────────────

SEM = asyncio.Semaphore(30)  # max concurrent requests

async def fetch(session, url):
    if not url: return None
    async with SEM:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            log.warning(f"Fetch failed: {url} -> {e}")
    return None

# ── Main ingestion ───────────────────────────────────────────────────────────

async def ingest_sample():
    EVENT_URL = "http://core.espnuk.org/v2/sports/cricket/leagues/8039/events/1336043"
    
    db_url = os.getenv("DATABASE_URL")
    pool = await asyncpg.create_pool(db_url)
    
    async with aiohttp.ClientSession() as session:
        # ════════════════════════════════════════════════════════════════════
        # 1. EVENT
        # ════════════════════════════════════════════════════════════════════
        log.info("Fetching event...")
        event = await fetch(session, EVENT_URL)
        if not event:
            log.error("Failed to fetch event. Aborting.")
            return
        event_id = str(event['id'])
        
        await pool.execute("""
            INSERT INTO cricket.events (id, uid, name, short_name, date, end_date)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, short_name=EXCLUDED.short_name, 
                date=EXCLUDED.date, end_date=EXCLUDED.end_date
        """, event_id, event.get('uid', f's:200~e:{event_id}'),
             event.get('name'), event.get('shortName'),
             safe_date(event.get('date')), safe_date(event.get('endDate')))
        log.info(f"  Event: {event.get('name')}")

        # ════════════════════════════════════════════════════════════════════
        # 2. LEAGUES + EVENT_LEAGUES
        # ════════════════════════════════════════════════════════════════════
        log.info("Fetching leagues...")
        for league_entry in event.get('leagues', []):
            league_ref = league_entry.get('$ref')
            league_data = await fetch(session, league_ref)
            if not league_data: continue
            lid = str(league_data['id'])
            
            await pool.execute("""
                INSERT INTO cricket.leagues (id, name, is_tournament, league_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name
            """, lid, league_data.get('name'), league_data.get('isTournament'),
                 league_entry.get('leagueType'))
            
            await pool.execute("""
                INSERT INTO cricket.event_leagues (event_id, league_id, league_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (event_id, league_id) DO NOTHING
            """, event_id, lid, league_entry.get('leagueType'))
            log.info(f"  League: {league_data.get('name')}")

        # ════════════════════════════════════════════════════════════════════
        # 3. COMPETITION
        # ════════════════════════════════════════════════════════════════════
        comp = event['competitions'][0]
        comp_id = str(comp['id'])
        
        # Venue
        v_data = await fetch(session, comp.get('venue', {}).get('$ref'))
        if v_data:
            await pool.execute("""
                INSERT INTO cricket.venues (id, full_name, short_name, city, country, capacity, grass)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET full_name=EXCLUDED.full_name
            """, str(v_data['id']), v_data.get('fullName'), v_data.get('shortName'),
                 v_data.get('address', {}).get('city'), v_data.get('address', {}).get('country'),
                 safe_int(v_data.get('capacity')), v_data.get('grass'))
            log.info(f"  Venue: {v_data.get('fullName')}")
        
        venue_id = extract_id_from_ref(comp.get('venue'))
        await pool.execute("""
            INSERT INTO cricket.competitions (id, event_id, date, end_date, venue_id, class_name,
                neutral_site, day_night, limited_overs, attendance, play_by_play_available)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id) DO NOTHING
        """, comp_id, event_id, safe_date(comp.get('date')), safe_date(comp.get('endDate')),
             venue_id, comp.get('class', {}).get('generalClassCard'),
             comp.get('neutralSite'), comp.get('dayNight'), comp.get('limitedOvers'),
             safe_int(comp.get('attendance')), comp.get('playByPlayAvailable'))
        log.info(f"  Competition: {comp_id}")

        # ════════════════════════════════════════════════════════════════════
        # 4. MATCH STATUS (fetch now, insert AFTER athletes are loaded)
        # ════════════════════════════════════════════════════════════════════
        log.info("Fetching match status...")
        status_data = await fetch(session, comp.get('status', {}).get('$ref'))

        # ════════════════════════════════════════════════════════════════════
        # 5. MATCH OFFICIALS
        # ════════════════════════════════════════════════════════════════════
        log.info("Fetching officials...")
        officials_data = await fetch(session, comp.get('officials', {}).get('$ref'))
        if officials_data and 'items' in officials_data:
            for off in officials_data['items']:
                await pool.execute("""
                    INSERT INTO cricket.match_officials (competition_id, display_name, first_name,
                        last_name, country, role)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, comp_id, off.get('displayName'), off.get('firstName'),
                     off.get('lastName'), off.get('flag', {}).get('alt'),
                     off.get('position', {}).get('displayName'))
                log.info(f"  Official: {off.get('displayName')} ({off.get('position', {}).get('displayName')})")

        # ════════════════════════════════════════════════════════════════════
        # 6. COMPETITORS (Teams + Rosters + Innings + Partnerships + FOW)
        # ════════════════════════════════════════════════════════════════════
        for competitor in comp.get('competitors', []):
            espn_comp_id = str(competitor.get('id'))
            
            # Team
            t_data = await fetch(session, competitor.get('team', {}).get('$ref'))
            if t_data:
                await pool.execute("""
                    INSERT INTO cricket.teams (id, name, short_display_name, abbreviation, is_national,
                        display_name, location, nickname, color, is_active, slug)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, display_name=EXCLUDED.display_name
                """, str(t_data['id']), t_data.get('name'),
                     t_data.get('shortDisplayName', t_data.get('shortName')),
                     t_data.get('abbreviation'), t_data.get('isNational'),
                     t_data.get('displayName'), t_data.get('location'),
                     t_data.get('nickname'), t_data.get('color'),
                     t_data.get('isActive'), t_data.get('slug'))
                log.info(f"  Team: {t_data.get('name')}")
            
            # Score
            score_val = competitor.get('score')
            if isinstance(score_val, dict):
                score_val = score_val.get('displayValue', str(score_val))
            elif score_val is not None:
                score_val = str(score_val)
            if score_val:
                score_val = score_val[:95]
            
            await pool.execute("""
                INSERT INTO cricket.competitors (espn_competitor_id, competition_id, team_id,
                    home_away, winner, score_value)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (competition_id, espn_competitor_id) DO NOTHING
            """, espn_comp_id, comp_id, extract_id_from_ref(competitor.get('team')),
                 competitor.get('homeAway'), competitor.get('winner'), score_val)
            
            # Get the DB-generated competitor PK
            db_competitor_id = await pool.fetchval("""
                SELECT id FROM cricket.competitors 
                WHERE competition_id=$1 AND espn_competitor_id=$2
            """, comp_id, espn_comp_id)
            
            # ── Roster (Athletes) ──
            log.info(f"  Fetching roster for competitor {espn_comp_id}...")
            r_data = await fetch(session, competitor.get('roster', {}).get('$ref'))
            if r_data and 'entries' in r_data:
                athlete_tasks = []
                for entry in r_data['entries']:
                    a_ref = entry.get('athlete', {}).get('$ref')
                    if a_ref:
                        athlete_tasks.append(fetch(session, a_ref))
                
                athletes = await asyncio.gather(*athlete_tasks)
                for a in athletes:
                    if not a or not a.get('id'): continue
                    batting_style = bowling_style = None
                    for s in a.get('styles', []):
                        if s.get('type') == 'batting': batting_style = s.get('description')
                        if s.get('type') == 'bowling': bowling_style = s.get('description')
                    
                    country = None
                    c = a.get('country')
                    if isinstance(c, dict):
                        country = c.get('abbreviation', c.get('name'))
                    elif c:
                        country = str(c)
                    
                    await pool.execute("""
                        INSERT INTO cricket.athletes (id, full_name, short_name, country_code,
                            date_of_birth, batting_style, bowling_style, position, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id) DO UPDATE SET 
                            full_name=EXCLUDED.full_name, country_code=EXCLUDED.country_code,
                            date_of_birth=EXCLUDED.date_of_birth, batting_style=EXCLUDED.batting_style,
                            bowling_style=EXCLUDED.bowling_style, position=EXCLUDED.position
                    """, str(a['id']), a.get('fullName'), a.get('shortName'),
                         country, safe_date(a.get('dateOfBirth')), batting_style, bowling_style,
                         a.get('position', {}).get('name'), a.get('active'))
                log.info(f"    Loaded {len([a for a in athletes if a])} athletes")
            
            # ── Innings (Linescores) ──
            log.info(f"  Fetching innings for competitor {espn_comp_id}...")
            ls_data = await fetch(session, competitor.get('linescores', {}).get('$ref'))
            if ls_data and 'items' in ls_data:
                for item in ls_data['items']:
                    period = safe_int(item.get('period'))
                    if period is None: continue
                    
                    await pool.execute("""
                        INSERT INTO cricket.innings (competitor_id, period, runs, wickets, overs,
                            fours, sixes, score, description, is_batting, is_current, target, follow_on)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (competitor_id, period) DO UPDATE SET
                            runs=EXCLUDED.runs, wickets=EXCLUDED.wickets, score=EXCLUDED.score
                    """, db_competitor_id, period,
                         safe_int(item.get('runs')), safe_int(item.get('wickets')),
                         safe_float(item.get('overs')), safe_int(item.get('fours')),
                         safe_int(item.get('sixes')), item.get('score'),
                         item.get('description'), item.get('isBatting', False),
                         bool(item.get('isCurrent')), safe_int(item.get('target')),
                         bool(item.get('followOn')))
                    log.info(f"    Innings {period}: {item.get('score', 'N/A')} ({item.get('description')})")
                    
                    # Get the DB-generated innings PK
                    db_innings_id = await pool.fetchval("""
                        SELECT id FROM cricket.innings 
                        WHERE competitor_id=$1 AND period=$2
                    """, db_competitor_id, period)
                    
                    # ── Partnerships ──
                    p_ref = item.get('partnerships', {}).get('$ref')
                    if p_ref:
                        p_list_data = await fetch(session, p_ref)
                        if p_list_data and 'items' in p_list_data:
                            p_tasks = [fetch(session, pi.get('$ref')) for pi in p_list_data['items'] if pi.get('$ref')]
                            partnerships = await asyncio.gather(*p_tasks)
                            for p in partnerships:
                                if not p: continue
                                wn = safe_int(p.get('wicketNumber'))
                                if wn is None: continue
                                
                                batsmen = p.get('batsmen', [])
                                b1_id = extract_id_from_url(batsmen[0].get('athlete')) if len(batsmen) > 0 else None
                                b2_id = extract_id_from_url(batsmen[1].get('athlete')) if len(batsmen) > 1 else None
                                b1_balls = safe_int(batsmen[0].get('balls')) if len(batsmen) > 0 else None
                                b2_balls = safe_int(batsmen[1].get('balls')) if len(batsmen) > 1 else None
                                
                                await pool.execute("""
                                    INSERT INTO cricket.partnerships (innings_id, wicket_number, runs, balls,
                                        batsman_1_id, batsman_2_id, start_overs, start_runs, start_wickets,
                                        end_overs, end_runs, end_wickets)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                                    ON CONFLICT (innings_id, wicket_number) DO NOTHING
                                """, db_innings_id, wn, safe_int(p.get('runs')),
                                     (b1_balls or 0) + (b2_balls or 0),
                                     b1_id, b2_id,
                                     safe_float(p.get('start', {}).get('overs')),
                                     safe_int(p.get('start', {}).get('runs')),
                                     safe_int(p.get('start', {}).get('wickets')),
                                     safe_float(p.get('end', {}).get('overs')),
                                     safe_int(p.get('end', {}).get('runs')),
                                     safe_int(p.get('end', {}).get('wickets')))
                            log.info(f"      {len([p for p in partnerships if p])} partnerships")
                    
                    # ── Fall of Wickets ──
                    fow_ref = item.get('fow', {}).get('$ref')
                    if fow_ref:
                        fow_list = await fetch(session, fow_ref)
                        if fow_list and 'items' in fow_list:
                            fow_tasks = [fetch(session, fi.get('$ref')) for fi in fow_list['items'] if fi.get('$ref')]
                            fows = await asyncio.gather(*fow_tasks)
                            for fw in fows:
                                if not fw: continue
                                wn = safe_int(fw.get('wicketNumber'))
                                if wn is None: continue
                                
                                await pool.execute("""
                                    INSERT INTO cricket.fall_of_wickets (innings_id, wicket_number,
                                        runs_scored, overs, fow_type)
                                    VALUES ($1, $2, $3, $4, $5)
                                    ON CONFLICT (innings_id, wicket_number) DO NOTHING
                                """, db_innings_id, wn,
                                     safe_int(fw.get('runs')), safe_float(fw.get('wicketOver')),
                                     fw.get('fowType'))
                            log.info(f"      {len([f for f in fows if f])} fall of wickets")

        # ════════════════════════════════════════════════════════════════════
        # 6b. MATCH STATUS (deferred — athletes are now loaded)
        # ════════════════════════════════════════════════════════════════════
        if status_data:
            potm_id = None
            for fa in status_data.get('featuredAthletes', []):
                if fa.get('name') == 'playerOfTheMatch':
                    potm_id = str(fa.get('playerId'))
                    # Ensure POTM athlete exists in DB
                    potm_athlete = await fetch(session, f"http://core.espnuk.org/v2/sports/cricket/athletes/{potm_id}")
                    if potm_athlete:
                        bat_s = bowl_s = None
                        for s in potm_athlete.get('styles', []):
                            if s.get('type') == 'batting': bat_s = s.get('description')
                            if s.get('type') == 'bowling': bowl_s = s.get('description')
                        c = potm_athlete.get('country')
                        country = c.get('abbreviation', c.get('name')) if isinstance(c, dict) else (str(c) if c else None)
                        await pool.execute("""
                            INSERT INTO cricket.athletes (id, full_name, short_name, country_code, date_of_birth, batting_style, bowling_style, position, is_active)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                            ON CONFLICT (id) DO UPDATE SET full_name=EXCLUDED.full_name, country_code=EXCLUDED.country_code,
                                date_of_birth=EXCLUDED.date_of_birth, batting_style=EXCLUDED.batting_style, bowling_style=EXCLUDED.bowling_style
                        """, potm_id, potm_athlete.get('fullName'), potm_athlete.get('shortName'),
                             country, safe_date(potm_athlete.get('dateOfBirth')), bat_s, bowl_s, potm_athlete.get('position', {}).get('name'), potm_athlete.get('active'))
            
            st = status_data.get('type', {})
            await pool.execute("""
                INSERT INTO cricket.match_status (competition_id, state, detail, description, summary,
                    long_summary, period, day_number, potm_athlete_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (competition_id) DO UPDATE SET 
                    state=EXCLUDED.state, summary=EXCLUDED.summary, long_summary=EXCLUDED.long_summary
            """, comp_id, st.get('state'), st.get('detail'), st.get('description'),
                 status_data.get('summary'), status_data.get('longSummary'),
                 safe_int(status_data.get('period')), safe_int(status_data.get('dayNumber')),
                 potm_id)
            log.info(f"  Match Status: {status_data.get('longSummary')}")

        # ════════════════════════════════════════════════════════════════════
        # 6c. MATCHCARDS & PLAYER MATCH PERFORMANCES
        # ════════════════════════════════════════════════════════════════════
        log.info("Fetching matchcards...")
        mc_ref = comp.get('matchcards', {}).get('$ref')
        if mc_ref:
            mc_data = await fetch(session, mc_ref)
            if mc_data and 'items' in mc_data:
                for mc in mc_data['items']:
                    mc_headline = mc.get('headline')
                    inns = safe_int(mc.get('inningsNumber'))
                    team_name = mc.get('teamName')
                    extras = mc.get('extras')
                    total = mc.get('total')
                    
                    db_competitor_id = await pool.fetchval("""
                        SELECT c.id FROM cricket.competitors c 
                        JOIN cricket.teams t ON c.team_id = t.id 
                        WHERE c.competition_id=$1 AND t.name=$2
                    """, comp_id, team_name)
                    
                    if mc_headline == 'Batting':
                        for idx, pd in enumerate(mc.get('playerDetails', [])):
                            pid = extract_id_from_url(pd.get('href')) or pd.get('playerID')
                            pname = pd.get('playerName')
                            dismissal = pd.get('dismissal')
                            runs = safe_int(pd.get('runs'))
                            bf = safe_int(pd.get('ballsFaced'))
                            fours = safe_int(pd.get('fours'))
                            sixes = safe_int(pd.get('sixes'))
                            sr = safe_float(pd.get('strikeRate'))
                            mins = safe_int(pd.get('minutes'))
                            
                            is_captain = '(c)' in pname if pname else False
                            is_keeper = '(wk)' in pname if pname else False
                            
                            await pool.execute("""
                                INSERT INTO cricket.matchcard_batting (
                                    competition_id, innings_number, team_name, extras, total,
                                    player_id, player_name, dismissal, runs, balls_faced, fours, sixes, strike_rate
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                            """, comp_id, inns, team_name, extras, total, pid, pname, dismissal, runs, bf, fours, sixes, sr)
                            
                            if db_competitor_id and pid:
                                try:
                                    await pool.execute("""
                                        INSERT INTO cricket.player_match_performances (
                                            competitor_id, innings_number, is_batting, batting_order,
                                            is_captain, is_keeper, runs, balls_faced, fours, sixes,
                                            strike_rate, minutes, athlete_id, dismissal_type
                                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                                    """, db_competitor_id, inns, True, idx + 1, is_captain, is_keeper,
                                         runs, bf, fours, sixes, sr, mins, pid, dismissal)
                                except Exception as e:
                                    log.warning(f"Skipping batting perf for {pid}: {e}")
                                     
                    elif mc_headline == 'Bowling':
                        for pd in mc.get('playerDetails', []):
                            pid = extract_id_from_url(pd.get('href')) or pd.get('playerID')
                            pname = pd.get('playerName')
                            ovs = safe_float(pd.get('overs'))
                            mdns = safe_int(pd.get('maidens'))
                            conc = safe_int(pd.get('conceded'))
                            wkts = safe_int(pd.get('wickets'))
                            econ = safe_float(pd.get('economyRate'))
                            nbw = pd.get('nbw', '')
                            
                            wides = no_balls = 0
                            if nbw:
                                m_w = re.search(r'(\d+)w', nbw)
                                if m_w: wides = int(m_w.group(1))
                                m_nb = re.search(r'(\d+)nb', nbw)
                                if m_nb: no_balls = int(m_nb.group(1))
                                
                            await pool.execute("""
                                INSERT INTO cricket.matchcard_bowling (
                                    competition_id, innings_number, team_name,
                                    player_id, player_name, overs, maidens, runs_conceded, wickets,
                                    economy, wides, no_balls
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                            """, comp_id, inns, team_name, pid, pname, ovs, mdns, conc, wkts, econ, wides, no_balls)
                            
                            if db_competitor_id and pid:
                                try:
                                    await pool.execute("""
                                        INSERT INTO cricket.player_match_performances (
                                            competitor_id, innings_number, is_batting, runs_conceded,
                                            overs_bowled, maidens, wickets, economy_rate, wides, no_balls,
                                            athlete_id
                                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    """, db_competitor_id, inns, False, conc, ovs, mdns, wkts, econ, wides, no_balls, pid)
                                except Exception as e:
                                    log.warning(f"Skipping bowling perf for {pid}: {e}")

        # ════════════════════════════════════════════════════════════════════
        # 7. DELIVERIES + DISMISSALS
        # ════════════════════════════════════════════════════════════════════
        log.info("Fetching deliveries (ball-by-ball)...")
        details_ref = comp.get('details', {}).get('$ref')
        if details_ref:
            page = 1
            total_deliveries = 0
            total_dismissals = 0
            while True:
                d_data = await fetch(session, f"{details_ref}?page={page}")
                if not d_data or not d_data.get('items'): break
                
                # Fetch all deliveries on this page concurrently
                del_tasks = [fetch(session, it.get('$ref')) for it in d_data['items'] if it.get('$ref')]
                deliveries = await asyncio.gather(*del_tasks)
                
                for item in deliveries:
                    if not item or not item.get('id'): continue
                    item_id = f"{comp_id}_{item['id']}"
                    over = item.get('over', {})
                    innings = item.get('innings', {})
                    batsman = item.get('batsman', {})
                    bowler = item.get('bowler', {})
                    o_batsman = item.get('otherBatsman', {})
                    o_bowler = item.get('otherBowler', {})
                    bat_team_id = extract_id_from_ref(batsman.get('team'))
                    bowl_team_id = extract_id_from_ref(bowler.get('team'))
                    
                    try:
                        await pool.execute("""
                            INSERT INTO cricket.deliveries (
                                id, competition_id, sequence, timestamp, date,
                                period, period_text, over_number, ball_in_over, overs_actual,
                                batsman_id, non_striker_id, bowler_id, other_bowler_id,
                                batting_team_id, bowling_team_id,
                                runs_scored, is_boundary, play_type_id, play_type_desc,
                                text, short_text,
                                is_wide, is_no_ball, is_bye, is_leg_bye,
                                speed_kph, speed_mph, x_coordinate, y_coordinate, hawkeye_id,
                                batsman_runs, batsman_balls_faced, batsman_fours, batsman_sixes,
                                bowler_overs, bowler_maidens, bowler_wickets, bowler_conceded,
                                team_score, innings_runs, innings_wickets, innings_run_rate,
                                innings_required_rr, innings_target, innings_session, innings_day,
                                innings_lead_by, innings_trail_by,
                                over_runs, over_wickets, over_maiden, over_complete
                            ) VALUES (
                                $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,
                                $21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35,$36,$37,$38,
                                $39,$40,$41,$42,$43,$44,$45,$46,$47,$48,$49,$50,$51,$52,$53
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                overs_actual=EXCLUDED.overs_actual, non_striker_id=EXCLUDED.non_striker_id,
                                other_bowler_id=EXCLUDED.other_bowler_id, batting_team_id=EXCLUDED.batting_team_id,
                                bowling_team_id=EXCLUDED.bowling_team_id, play_type_id=EXCLUDED.play_type_id,
                                play_type_desc=EXCLUDED.play_type_desc, text=EXCLUDED.text, short_text=EXCLUDED.short_text,
                                batsman_runs=EXCLUDED.batsman_runs, batsman_balls_faced=EXCLUDED.batsman_balls_faced,
                                bowler_overs=EXCLUDED.bowler_overs, bowler_wickets=EXCLUDED.bowler_wickets,
                                bowler_conceded=EXCLUDED.bowler_conceded, team_score=EXCLUDED.team_score,
                                innings_runs=EXCLUDED.innings_runs, innings_wickets=EXCLUDED.innings_wickets,
                                over_runs=EXCLUDED.over_runs, over_wickets=EXCLUDED.over_wickets
                        """,
                             item_id, comp_id, safe_int(item.get('sequence')),
                             safe_int(item.get('bbbTimestamp')), safe_date(item.get('date')),
                             safe_int(item.get('period')), item.get('periodText'),
                             safe_int(over.get('number')), safe_int(over.get('ball')),
                             safe_float(over.get('actual')),
                             extract_id_from_ref(batsman.get('athlete')),
                             extract_id_from_ref(o_batsman.get('athlete')),
                             extract_id_from_ref(bowler.get('athlete')),
                             extract_id_from_ref(o_bowler.get('athlete')),
                             bat_team_id, bowl_team_id,
                             safe_int(item.get('scoreValue')), bool(item.get('boundary')),
                             item.get('playType', {}).get('id'),
                             item.get('playType', {}).get('description'),
                             item.get('text'), item.get('shortText'),
                             over.get('wide', 0) > 0, over.get('noBall', 0) > 0,
                             over.get('byes', 0) > 0, over.get('legByes', 0) > 0,
                             safe_float(item.get('speedKPH')), safe_float(item.get('speedMPH')),
                             safe_float(item.get('xCoordinate')), safe_float(item.get('yCoordinate')),
                             item.get('hawkeyeId'),
                             safe_int(batsman.get('runs')), safe_int(batsman.get('faced')),
                             safe_int(batsman.get('fours')), safe_int(batsman.get('sixes')),
                             safe_float(bowler.get('overs')), safe_int(bowler.get('maidens')),
                             safe_int(bowler.get('wickets')), safe_int(bowler.get('conceded')),
                             item.get('homeScore'),
                             safe_int(innings.get('runs')), safe_int(innings.get('wickets')),
                             safe_float(innings.get('runRate')),
                             safe_float(innings.get('requiredRunRate')),
                             safe_int(innings.get('target')),
                             safe_int(innings.get('session')), safe_int(innings.get('day')),
                             safe_int(innings.get('leadBy')), safe_int(innings.get('trailBy')),
                             safe_int(over.get('runs')), safe_int(over.get('wickets')),
                             bool(over.get('maiden')), bool(over.get('complete'))
                        )
                        total_deliveries += 1
                    except Exception as e:
                        log.error(f"Delivery {item_id}: {e}")
                    
                    # Dismissal
                    dismissal = item.get('dismissal')
                    if dismissal and dismissal.get('dismissal'):
                        try:
                            await pool.execute("""
                                INSERT INTO cricket.dismissals (delivery_id, type, batsman_id,
                                    bowler_id, fielder_id, is_keeper, text, minutes, is_bowled)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                ON CONFLICT (delivery_id) DO NOTHING
                            """, item_id, dismissal.get('type'),
                                 extract_id_from_ref(dismissal.get('batsman', {}).get('athlete')),
                                 extract_id_from_ref(dismissal.get('bowler', {}).get('athlete')),
                                 extract_id_from_ref(dismissal.get('fielder', {}).get('athlete')),
                                 dismissal.get('fielder', {}).get('isKeeper'),
                                 dismissal.get('text'), safe_int(dismissal.get('minutes')),
                                 dismissal.get('bowled'))
                            total_dismissals += 1
                        except Exception as e:
                            log.error(f"Dismissal for delivery {item_id}: {e}")
                
                log.info(f"  Page {page}: {len([d for d in deliveries if d])} deliveries fetched")
                if d_data.get('pageIndex', 1) >= d_data.get('pageCount', 1):
                    break
                page += 1
            
            log.info(f"  Total deliveries: {total_deliveries}, dismissals: {total_dismissals}")

    # ════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ════════════════════════════════════════════════════════════════════
    tables = ['venues','teams','athletes','leagues','events','event_leagues',
              'competitions','match_status','match_officials','competitors',
              'innings','partnerships','fall_of_wickets','player_match_performances',
              'deliveries','dismissals','matchcard_batting','matchcard_bowling']
    
    log.info("=" * 60)
    log.info("FINAL TABLE COUNTS:")
    log.info("=" * 60)
    for t in tables:
        count = await pool.fetchval(f'SELECT count(*) FROM cricket.{t}')
        status = "OK" if count > 0 else "EMPTY"
        log.info(f"  {t:35s} {count:>6d}  [{status}]")
    log.info("=" * 60)
    
    await pool.close()
    log.info("Done!")

if __name__ == '__main__':
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(ingest_sample())
