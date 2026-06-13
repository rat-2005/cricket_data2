import os

with open('ingest_bulk.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. We need to wrap the deliveries insert in a try..except block
target_delivery_start = """                        await conn.execute(\"\"\"
                            INSERT INTO cricket.deliveries ("""

replacement_delivery_start = """                        async def ensure_athlete(aid):
                            if not aid: return
                            try:
                                exists = await conn.fetchval("SELECT id FROM cricket.athletes WHERE id=$1", aid)
                                if exists: return
                                a_data = await fetch(session, f"http://core.espnuk.org/v2/sports/cricket/athletes/{aid}")
                                if a_data:
                                    bat_s = bowl_s = None
                                    for s in a_data.get('styles', []):
                                        if s.get('type') == 'batting': bat_s = s.get('description')
                                        if s.get('type') == 'bowling': bowl_s = s.get('description')
                                    c = a_data.get('country')
                                    country = c.get('abbreviation', c.get('name')) if isinstance(c, dict) else (str(c) if c else None)
                                    await conn.execute("INSERT INTO cricket.athletes (id, full_name, short_name, country_code, date_of_birth, batting_style, bowling_style, position, is_active) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) ON CONFLICT (id) DO NOTHING", aid, a_data.get('fullName'), a_data.get('shortName'), country, safe_date(a_data.get('dateOfBirth')), bat_s, bowl_s, a_data.get('position', {}).get('name'), a_data.get('active'))
                            except Exception as e:
                                pass

                        try:
                            await conn.execute(\"\"\"
                                INSERT INTO cricket.deliveries ("""

content = content.replace(target_delivery_start, replacement_delivery_start)


# 2. Add the except block for deliveries
target_delivery_end = """                             bool(over.get('maiden')), bool(over.get('complete'))
                        )
                        
                        dismissal = item.get('dismissal')"""

replacement_delivery_end = """                             bool(over.get('maiden')), bool(over.get('complete'))
                        )
                        except asyncpg.exceptions.ForeignKeyViolationError as e:
                            await ensure_athlete(extract_id_from_ref(batsman.get('athlete')))
                            await ensure_athlete(extract_id_from_ref(o_batsman.get('athlete')))
                            await ensure_athlete(extract_id_from_ref(bowler.get('athlete')))
                            await ensure_athlete(extract_id_from_ref(o_bowler.get('athlete')))
                            try:
                                await conn.execute(\"\"\"
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
                                    ON CONFLICT (id) DO NOTHING
                                \"\"\",
                                     item_id, comp_id, safe_int(item.get('sequence')),
                                     safe_int(item.get('bbbTimestamp')), safe_date(item.get('date')),
                                     safe_int(item.get('period')), item.get('periodText'),
                                     safe_int(over.get('number')), safe_int(over.get('ball')),
                                     safe_float(over.get('actual')),
                                     extract_id_from_ref(batsman.get('athlete')), extract_id_from_ref(o_batsman.get('athlete')),
                                     extract_id_from_ref(bowler.get('athlete')), extract_id_from_ref(o_bowler.get('athlete')),
                                     extract_id_from_ref(batsman.get('team')), extract_id_from_ref(bowler.get('team')),
                                     safe_int(item.get('scoreValue')), bool(item.get('boundary')),
                                     item.get('playType', {}).get('id'), item.get('playType', {}).get('description'),
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
                                     safe_float(innings.get('runRate')), safe_float(innings.get('requiredRunRate')),
                                     safe_int(innings.get('target')), safe_int(innings.get('session')), safe_int(innings.get('day')),
                                     safe_int(innings.get('leadBy')), safe_int(innings.get('trailBy')),
                                     safe_int(over.get('runs')), safe_int(over.get('wickets')),
                                     bool(over.get('maiden')), bool(over.get('complete'))
                                )
                            except Exception as e2:
                                log.error(f"Delivery {item_id} final error: {e2}")
                        except Exception as e:
                            log.error(f"Delivery {item_id} error: {e}")
                        
                        dismissal = item.get('dismissal')"""

content = content.replace(target_delivery_end, replacement_delivery_end)


# 3. Add the try..except for dismissals
target_dismissal = """                        if dismissal and dismissal.get('dismissal'):
                            await conn.execute(\"\"\"
                                INSERT INTO cricket.dismissals (delivery_id, type, batsman_id,
                                    bowler_id, fielder_id, is_keeper, text, minutes, is_bowled)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                ON CONFLICT (delivery_id) DO NOTHING
                            \"\"\", item_id, dismissal.get('type'),
                                 extract_id_from_ref(dismissal.get('batsman', {}).get('athlete')),
                                 extract_id_from_ref(dismissal.get('bowler', {}).get('athlete')),
                                 extract_id_from_ref(dismissal.get('fielder', {}).get('athlete')),
                                 dismissal.get('fielder', {}).get('isKeeper'),
                                 dismissal.get('text'), safe_int(dismissal.get('minutes')),
                                 dismissal.get('bowled'))"""

replacement_dismissal = """                        if dismissal and dismissal.get('dismissal'):
                            try:
                                await conn.execute(\"\"\"
                                    INSERT INTO cricket.dismissals (delivery_id, type, batsman_id,
                                        bowler_id, fielder_id, is_keeper, text, minutes, is_bowled)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                    ON CONFLICT (delivery_id) DO NOTHING
                                \"\"\", item_id, dismissal.get('type'),
                                     extract_id_from_ref(dismissal.get('batsman', {}).get('athlete')),
                                     extract_id_from_ref(dismissal.get('bowler', {}).get('athlete')),
                                     extract_id_from_ref(dismissal.get('fielder', {}).get('athlete')),
                                     dismissal.get('fielder', {}).get('isKeeper'),
                                     dismissal.get('text'), safe_int(dismissal.get('minutes')),
                                     dismissal.get('bowled'))
                            except asyncpg.exceptions.ForeignKeyViolationError as e:
                                await ensure_athlete(extract_id_from_ref(dismissal.get('batsman', {}).get('athlete')))
                                await ensure_athlete(extract_id_from_ref(dismissal.get('bowler', {}).get('athlete')))
                                await ensure_athlete(extract_id_from_ref(dismissal.get('fielder', {}).get('athlete')))
                                try:
                                    await conn.execute(\"\"\"
                                        INSERT INTO cricket.dismissals (delivery_id, type, batsman_id,
                                            bowler_id, fielder_id, is_keeper, text, minutes, is_bowled)
                                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                                        ON CONFLICT (delivery_id) DO NOTHING
                                    \"\"\", item_id, dismissal.get('type'),
                                         extract_id_from_ref(dismissal.get('batsman', {}).get('athlete')),
                                         extract_id_from_ref(dismissal.get('bowler', {}).get('athlete')),
                                         extract_id_from_ref(dismissal.get('fielder', {}).get('athlete')),
                                         dismissal.get('fielder', {}).get('isKeeper'),
                                         dismissal.get('text'), safe_int(dismissal.get('minutes')),
                                         dismissal.get('bowled'))
                                except Exception as e2:
                                    log.error(f"Dismissal {item_id} final error: {e2}")
                            except Exception as e:
                                log.error(f"Dismissal {item_id} error: {e}")"""

content = content.replace(target_dismissal, replacement_dismissal)

with open('ingest_bulk.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Foreign key fix applied successfully!")
