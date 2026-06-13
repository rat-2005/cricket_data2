import asyncio
import aiohttp
import asyncpg
import json
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def safe_int(val, default=None):
    try: return int(float(val))
    except (TypeError, ValueError): return default

def safe_float(val, default=None):
    try: return float(val)
    except (TypeError, ValueError): return default

def safe_date(val):
    if not val: return None
    try: return datetime.strptime(val.replace('Z', '+0000'), '%Y-%m-%dT%H:%M%z')
    except:
        try: return datetime.fromisoformat(val.replace('Z', '+00:00'))
        except: return None

import re

def extract_id(ref_dict):
    if not ref_dict or '$ref' not in ref_dict: return None
    url = str(ref_dict.get('$ref', '')).split('?')[0]
    m = re.search(r'/(\d+)/?$', url)
    if m:
        val = m.group(1)
        return val if val != '0' else None
    return None

async def fetch_json(session, url):
    if not url: return None
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        logging.warning(f"Error fetching {url}: {e}")
    return None

class AsyncIngester:
    def __init__(self, pool):
        self.pool = pool
        
    async def upsert_venue(self, v):
        if not v or not v.get('id'): return
        await self.pool.execute("""
            INSERT INTO cricket.venues (id, full_name, short_name, city, country, capacity, grass)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name, updated_at = CURRENT_TIMESTAMP
        """, str(v.get('id')), v.get('fullName'), v.get('shortName'), 
             v.get('address', {}).get('city'), v.get('address', {}).get('country'),
             safe_int(v.get('capacity')), v.get('grass'))

    async def upsert_team(self, t):
        if not t or not t.get('id'): return
        await self.pool.execute("""
            INSERT INTO cricket.teams (id, name, short_display_name, abbreviation, is_national)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = CURRENT_TIMESTAMP
        """, str(t.get('id')), t.get('name'), t.get('shortDisplayName', t.get('shortName')), t.get('abbreviation'), t.get('isNational'))

    async def upsert_athlete(self, a):
        if not a or not a.get('id'): return
        batting_style = None
        bowling_style = None
        for s in a.get('styles', []):
            if s.get('type') == 'batting': batting_style = s.get('description')
            if s.get('type') == 'bowling': bowling_style = s.get('description')
        position = a.get('position', {}).get('name')
        country = str(a.get('country')) if a.get('country') else None
        
        await self.pool.execute("""
            INSERT INTO cricket.athletes (id, full_name, short_name, country_code, date_of_birth, batting_style, bowling_style, position, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO UPDATE SET 
                full_name = EXCLUDED.full_name, country_code = EXCLUDED.country_code,
                date_of_birth = EXCLUDED.date_of_birth, batting_style = EXCLUDED.batting_style,
                bowling_style = EXCLUDED.bowling_style, position = EXCLUDED.position, updated_at = CURRENT_TIMESTAMP
        """, str(a.get('id')), a.get('fullName'), a.get('shortName'), country, safe_date(a.get('dateOfBirth')), batting_style, bowling_style, position, a.get('active'))

    async def ingest_event(self, session, event_url):
        event_data = await fetch_json(session, event_url)
        if not event_data: return
        event_id = str(event_data['id'])
        
        await self.pool.execute("""
            INSERT INTO cricket.events (id, uid, name, short_name, date, end_date)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
        """, event_id, event_data.get('uid', 's:0~e:'+event_id), event_data.get('name'), event_data.get('shortName'), 
             safe_date(event_data.get('date')), safe_date(event_data.get('endDate')))

        for comp in event_data.get('competitions', []):
            comp_id = str(comp['id'])
            
            # 1. Venue
            v_ref = comp.get('venue', {}).get('$ref')
            if v_ref:
                v_data = await fetch_json(session, v_ref)
                if v_data: await self.upsert_venue(v_data)
                
            await self.pool.execute("""
                INSERT INTO cricket.competitions (id, event_id, date, venue_id, class_name)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO NOTHING
            """, comp_id, event_id, safe_date(comp.get('date')), extract_id(comp.get('venue')), 
                 comp.get('format', {}).get('name'))

            # 2. Competitors (Teams, Rosters, Innings)
            for competitor in comp.get('competitors', []):
                t_ref = competitor.get('team', {}).get('$ref')
                if t_ref:
                    t_data = await fetch_json(session, t_ref)
                    if t_data: await self.upsert_team(t_data)
                
                score_val = competitor.get('score')
                if isinstance(score_val, dict): score_val = score_val.get('displayValue', str(score_val))
                else: score_val = str(score_val) if score_val is not None else None
                if score_val: score_val = score_val[:95]
                
                await self.pool.execute("""
                    INSERT INTO cricket.competitors (espn_competitor_id, competition_id, team_id, home_away, winner, score_value)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (competition_id, espn_competitor_id) DO NOTHING
                """, str(competitor.get('id')), comp_id, extract_id(competitor.get('team')), 
                     competitor.get('homeAway'), competitor.get('winner'), score_val)

                # Rosters (Athletes)
                r_ref = competitor.get('roster', {}).get('$ref')
                if r_ref:
                    r_data = await fetch_json(session, r_ref)
                    if r_data and 'entries' in r_data:
                        for entry in r_data['entries']:
                            a_ref = entry.get('athlete', {}).get('$ref')
                            if a_ref:
                                a_data = await fetch_json(session, a_ref)
                                if a_data: await self.upsert_athlete(a_data)
                
                # Innings (Linescores)
                ls_ref = competitor.get('linescores', {}).get('$ref')
                if ls_ref:
                    ls_data = await fetch_json(session, ls_ref)
                    if ls_data and 'items' in ls_data:
                        for item in ls_data['items']:
                            await self.pool.execute("""
                                INSERT INTO cricket.innings (
                                    competitor_id, period, runs, wickets, overs, 
                                    fours, sixes, score, description, is_batting
                                )
                                VALUES (
                                    (SELECT id FROM cricket.competitors WHERE competition_id=$1 AND espn_competitor_id=$2), 
                                    $3, $4, $5, $6, $7, $8, $9, $10, $11
                                )
                                ON CONFLICT (competitor_id, period) DO NOTHING
                            """, comp_id, str(competitor.get('id')), safe_int(item.get('period')), 
                                 safe_int(item.get('runs')), safe_int(item.get('wickets')), 
                                 safe_float(item.get('overs')), safe_int(item.get('fours')), 
                                 safe_int(item.get('sixes')), item.get('score'), 
                                 item.get('description'), item.get('isBatting', False))

            # 3. Deliveries (Details)
            details_ref = comp.get('details', {}).get('$ref')
            if details_ref:
                page = 1
                while True:
                    d_data = await fetch_json(session, f"{details_ref}?page={page}")
                    if not d_data or not d_data.get('items'): break
                    
                    for item_ref in d_data['items']:
                        # The item is just a $ref, we MUST fetch it to get the delivery!
                        del_url = item_ref.get('$ref')
                        if not del_url: continue
                        
                        item = await fetch_json(session, del_url)
                        if not item or not item.get('id'): continue
                        
                        item_id = f"{comp_id}_{item.get('id')}"
                        over = item.get('over', {})
                        
                        try:
                            # 1. Prepare all variables to make the query cleaner
                            bat_team = extract_id(item.get('batsman', {}).get('team'))
                            bowl_team = extract_id(item.get('bowler', {}).get('team'))
                            team_score = item.get('homeScore') if str(bat_team) == '1' else item.get('awayScore')
                            
                            await self.pool.execute("""
                                INSERT INTO cricket.deliveries (
                                    id, competition_id, sequence, timestamp, date,
                                    period, period_text, over_number, ball_in_over, overs_actual,
                                    batsman_id, non_striker_id, bowler_id, other_bowler_id, batting_team_id, bowling_team_id,
                                    runs_scored, is_boundary, play_type_id, play_type_desc, text, short_text,
                                    is_wide, is_no_ball, is_bye, is_leg_bye,
                                    speed_kph, speed_mph, x_coordinate, y_coordinate, hawkeye_id,
                                    batsman_runs, batsman_balls_faced, batsman_fours, batsman_sixes,
                                    bowler_overs, bowler_maidens, bowler_wickets, bowler_conceded,
                                    team_score, innings_runs, innings_wickets, innings_run_rate,
                                    innings_required_rr, innings_target, innings_session, innings_day,
                                    innings_lead_by, innings_trail_by, over_runs, over_wickets,
                                    over_maiden, over_complete
                                ) VALUES (
                                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                                    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
                                    $31, $32, $33, $34, $35, $36, $37, $38, $39, $40,
                                    $41, $42, $43, $44, $45, $46, $47, $48, $49, $50,
                                    $51, $52, $53
                                )
                                ON CONFLICT (id) DO UPDATE SET 
                                    overs_actual = EXCLUDED.overs_actual, non_striker_id = EXCLUDED.non_striker_id,
                                    other_bowler_id = EXCLUDED.other_bowler_id, batting_team_id = EXCLUDED.batting_team_id,
                                    bowling_team_id = EXCLUDED.bowling_team_id, play_type_id = EXCLUDED.play_type_id,
                                    play_type_desc = EXCLUDED.play_type_desc, text = EXCLUDED.text, short_text = EXCLUDED.short_text,
                                    is_wide = EXCLUDED.is_wide, is_no_ball = EXCLUDED.is_no_ball, is_bye = EXCLUDED.is_bye,
                                    is_leg_bye = EXCLUDED.is_leg_bye, hawkeye_id = EXCLUDED.hawkeye_id, batsman_runs = EXCLUDED.batsman_runs,
                                    batsman_balls_faced = EXCLUDED.batsman_balls_faced, batsman_fours = EXCLUDED.batsman_fours,
                                    batsman_sixes = EXCLUDED.batsman_sixes, bowler_overs = EXCLUDED.bowler_overs,
                                    bowler_maidens = EXCLUDED.bowler_maidens, bowler_wickets = EXCLUDED.bowler_wickets,
                                    bowler_conceded = EXCLUDED.bowler_conceded, team_score = EXCLUDED.team_score,
                                    innings_runs = EXCLUDED.innings_runs, innings_wickets = EXCLUDED.innings_wickets,
                                    innings_run_rate = EXCLUDED.innings_run_rate, innings_required_rr = EXCLUDED.innings_required_rr,
                                    innings_target = EXCLUDED.innings_target, innings_session = EXCLUDED.innings_session,
                                    innings_day = EXCLUDED.innings_day, innings_lead_by = EXCLUDED.innings_lead_by,
                                    innings_trail_by = EXCLUDED.innings_trail_by, over_runs = EXCLUDED.over_runs,
                                    over_wickets = EXCLUDED.over_wickets, over_maiden = EXCLUDED.over_maiden, over_complete = EXCLUDED.over_complete
                            """, 
                                 item_id, comp_id, safe_int(item.get('sequence')), safe_int(item.get('bbbTimestamp')), safe_date(item.get('date')),
                                 safe_int(item.get('period')), item.get('periodText'), safe_int(over.get('number')), safe_int(over.get('ball')), safe_float(over.get('actual')),
                                 extract_id(item.get('batsman', {}).get('athlete')), extract_id(item.get('otherBatsman', {}).get('athlete')), 
                                 extract_id(item.get('bowler', {}).get('athlete')), extract_id(item.get('otherBowler', {}).get('athlete')),
                                 bat_team, bowl_team,
                                 safe_int(item.get('scoreValue')), bool(item.get('boundary')), item.get('playType', {}).get('id'), item.get('playType', {}).get('description'),
                                 item.get('text'), item.get('shortText'),
                                 over.get('wide', 0) > 0, over.get('noBall', 0) > 0, over.get('byes', 0) > 0, over.get('legByes', 0) > 0,
                                 safe_float(item.get('speedKPH')), safe_float(item.get('speedMPH')), safe_float(item.get('xCoordinate')), safe_float(item.get('yCoordinate')), item.get('hawkeyeId'),
                                 safe_int(item.get('batsman', {}).get('runs')), safe_int(item.get('batsman', {}).get('faced')), safe_int(item.get('batsman', {}).get('fours')), safe_int(item.get('batsman', {}).get('sixes')),
                                 safe_float(item.get('bowler', {}).get('overs')), safe_int(item.get('bowler', {}).get('maidens')), safe_int(item.get('bowler', {}).get('wickets')), safe_int(item.get('bowler', {}).get('conceded')),
                                 team_score, safe_int(item.get('innings', {}).get('runs')), safe_int(item.get('innings', {}).get('wickets')), safe_float(item.get('innings', {}).get('runRate')),
                                 safe_float(item.get('innings', {}).get('requiredRunRate')), safe_int(item.get('innings', {}).get('target')), safe_int(item.get('innings', {}).get('session')), safe_int(item.get('innings', {}).get('day')),
                                 safe_int(item.get('innings', {}).get('leadBy')), safe_int(item.get('innings', {}).get('trailBy')), safe_int(over.get('runs')), safe_int(over.get('wickets')),
                                 bool(over.get('maiden')), bool(over.get('complete'))
                            )
                        except Exception as e:
                            logging.error(f"Failed to insert delivery {item_id}: {e}")
                    page += 1

async def main():
    with open('events.json', 'r') as f:
        events = json.load(f)
        
    db_url = os.getenv("DATABASE_URL")
    pool = await asyncpg.create_pool(db_url)
    ingester = AsyncIngester(pool)
    
    async with aiohttp.ClientSession() as session:
        for event in events:
            await ingester.ingest_event(session, event['url'])
            
    await pool.close()

if __name__ == '__main__':
    asyncio.run(main())
