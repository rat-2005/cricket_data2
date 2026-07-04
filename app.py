"""
app.py — Cricket Analytics Dashboard

Thin Flask layer. All data logic lives in data_service.py (blackbox).
All database access goes through db.py (DuckDB + S3 Parquet).
No PostgreSQL. No raw SQL in this file.
"""
from flask import Flask, render_template, request, jsonify, redirect
import data_service as ds

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


import datetime
@app.before_request
def log_request_info():
    with open("requests.log", "a") as f:
        f.write(f"[{datetime.datetime.now()}] URL: {request.url}\n")
        f.write(f"[{datetime.datetime.now()}] ARGS: {dict(request.args)}\n")



# ── Helper ───────────────────────────────────────────────────

def _filters(args):
    """Extract filter dict from request query params."""
    keys = [
        "format", "league", "opponent", "phase", "venue", "year", 
        "innings", "bowling_type", "batting_type", "recent", "result",
        "wicket_type", "pitch_length", "pitch_line", "shot_type", "delivery_output"
    ]
    f = {}
    for k in keys:
        val = args.getlist(k)
        # Handle comma-separated arrays sent as a single string
        if len(val) == 1 and "," in val[0]:
            val = [x.strip() for x in val[0].split(",") if x.strip()]
            
        if not val or val == [''] or val == ['All']:
            f[k] = "All"
        elif len(val) == 1:
            f[k] = val[0]
        else:
            f[k] = val
            
        f[f"{k}_not"] = args.get(f"{k}_not", "false").lower() == "true"
        
    return f


# ── Pages ────────────────────────────────────────────────────

@app.route('/api/debug')
def debug_query():
    sql = request.args.get('sql')
    if not sql: return jsonify({"error": "no sql"})
    try:
        from db import query
        res = query(sql)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/")
def index():
    fmt = request.args.get("format", "All")
    batters, bowlers, stats = ds.get_dashboard_data(fmt)
    return render_template(
        "index.html",
        batters=batters,
        bowlers=bowlers,
        stats=stats,
        current_format=fmt,
    )


@app.route("/batter")
@app.route("/batter/<slug>")
def batter_page(slug=None):
    athlete_id = request.args.get("id")
    info = None
    if slug:
        info = ds.get_player_by_slug(slug)
        if info: athlete_id = info["id"]
    elif athlete_id:
        info = ds.get_player_info(athlete_id)
        if info and "slug" in info:
            return redirect(f"/batter/{info['slug']}")
    return render_template("batter.html", athlete_id=athlete_id, info=info)


@app.route("/bowler")
@app.route("/bowler/<slug>")
def bowler_page(slug=None):
    athlete_id = request.args.get("id")
    info = None
    if slug:
        info = ds.get_player_by_slug(slug)
        if info: athlete_id = info["id"]
    elif athlete_id:
        info = ds.get_player_info(athlete_id)
        if info and "slug" in info:
            return redirect(f"/bowler/{info['slug']}")
    return render_template("bowler.html", athlete_id=athlete_id, info=info)


@app.route("/faceoff")
@app.route("/faceoff/<slugs>")
def faceoff_page(slugs=None):
    batter_id = request.args.get("batter_id")
    bowler_id = request.args.get("bowler_id")
    batter_info = None
    bowler_info = None
    
    if slugs and "-vs-" in slugs:
        parts = slugs.split("-vs-")
        if len(parts) == 2:
            batter_info = ds.get_player_by_slug(parts[0])
            bowler_info = ds.get_player_by_slug(parts[1])
            if batter_info: batter_id = batter_info["id"]
            if bowler_info: bowler_id = bowler_info["id"]
            
    if (batter_id and not batter_info) or (bowler_id and not bowler_info):
        if batter_id: batter_info = ds.get_player_info(batter_id)
        if bowler_id: bowler_info = ds.get_player_info(bowler_id)
        
        # If both present and we didn't come from a slug route, redirect to slug route
        if batter_info and bowler_info and "slug" in batter_info and "slug" in bowler_info and not slugs:
            return redirect(f"/faceoff/{batter_info['slug']}-vs-{bowler_info['slug']}")

    return render_template(
        "faceoff.html",
        batter_id=batter_id,
        bowler_id=bowler_id,
        batter_info=batter_info,
        bowler_info=bowler_info
    )


@app.route("/player")
def player_search():
    return render_template("player.html", athlete=None, batting=None, bowling=None)


@app.route("/player/<identifier>")
def player_profile(identifier):
    # Try as slug first
    info = ds.get_player_by_slug(identifier)
    if info:
        athlete_id = info["id"]
    else:
        # Fallback to ID
        athlete_id = identifier
        info = ds.get_player_info(athlete_id)
        if info and "slug" in info:
            return redirect(f"/player/{info['slug']}")
            
    data = ds.get_player_profile(athlete_id)
    if not data:
        return "Player not found", 404
        
    return render_template(
        "player.html",
        athlete=data["athlete"],
        batting=data["batting"],
        bowling=data["bowling"],
        slug=info["slug"] if info and "slug" in info else identifier
    )


@app.route("/robots.txt")
def robots_txt():
    content = f"User-agent: *\nAllow: /\nSitemap: {request.host_url}sitemap.xml\n"
    from flask import Response
    return Response(content, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap_xml():
    # In a real app, generate from database of top players and faceoffs.
    # We will return a basic static sitemap for now or dynamic if easy.
    return render_template("sitemap.xml", host=request.host_url)

# ── APIs ─────────────────────────────────────────────────────

@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    return jsonify(
        ds.search_players(
            q,
            against_batter=request.args.get("against_batter"),
            against_bowler=request.args.get("against_bowler"),
        )
    )


@app.route("/api/athlete/<athlete_id>")
def athlete_api(athlete_id):
    info = ds.get_player_info(athlete_id)
    if info:
        return jsonify(info)
    return jsonify({"error": "not found"}), 404


@app.route("/api/stats/batter")
def stats_batter():
    pid = request.args.get("id")
    if not pid:
        return jsonify({"error": "missing id"}), 400
    return jsonify(ds.get_batter_stats(pid, _filters(request.args)))


@app.route('/api/stats/bowler', methods=['GET'])
def stats_bowler():
    pid = request.args.get("id")
    if not pid: return jsonify({"error": "id required"}), 400
    try:
        return jsonify(ds.get_bowler_stats(pid, _filters(request.args)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats/faceoff")
def stats_faceoff():
    bid  = request.args.get("batter_id")
    boid = request.args.get("bowler_id")
    if not bid and not request.args.get("batting_type"):
        return jsonify({"error": "missing batter"}), 400
    if not boid and not request.args.get("bowling_type"):
        return jsonify({"error": "missing bowler"}), 400
    return jsonify(ds.get_faceoff_stats(bid, boid, _filters(request.args)))


@app.route("/api/filters")
def filters_api():
    return jsonify(ds.get_global_filters())


@app.route("/api/batter_filters")
def batter_filters():
    pid = request.args.get("id")
    if not pid:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": []})
    return jsonify(ds.get_batter_filters(pid, _filters(request.args)))


@app.route("/api/bowler_filters")
def bowler_filters():
    pid = request.args.get("id")
    if not pid:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": []})
    return jsonify(ds.get_bowler_filters(pid, _filters(request.args)))


@app.route("/api/faceoff_filters")
def faceoff_filters():
    bid  = request.args.get("batter_id")
    boid = request.args.get("bowler_id")
    if not bid and not request.args.get("batting_type"):
        return jsonify({"error": "missing batter"}), 400
    if not boid and not request.args.get("bowling_type"):
        return jsonify({"error": "missing bowler"}), 400
    return jsonify(ds.get_faceoff_filters(bid, boid, _filters(request.args)))


# ── Run ──────────────────────────────────────────────────────

# Start daily background cron job to sync Parquet files
import threading
import time
from db import sync_parquet_files, reload_db

def run_daily_sync():
    while True:
        # Wait 24 hours
        time.sleep(24 * 60 * 60)
        try:
            print("Running daily background Parquet sync...")
            sync_parquet_files()
            reload_db()
        except Exception as e:
            print(f"Error in daily sync: {e}")

# Daemon thread will close when the server stops
threading.Thread(target=run_daily_sync, daemon=True).start()

if __name__ == "__main__":
    # use_reloader=False keeps DuckDB's singleton connection alive.
    # Without this, Flask restarts the process on every file save,
    # which resets _conn=None and triggers a full ~60s S3 re-init.
    app.run(debug=True, port=5000, use_reloader=False)
