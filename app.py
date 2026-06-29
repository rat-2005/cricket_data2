"""
app.py — Cricket Analytics Dashboard

Thin Flask layer. All data logic lives in data_service.py (blackbox).
All database access goes through db.py (DuckDB + S3 Parquet).
No PostgreSQL. No raw SQL in this file.
"""
from flask import Flask, render_template, request, jsonify
import data_service as ds

app = Flask(__name__)


# ── Helper ───────────────────────────────────────────────────

def _filters(args):
    """Extract filter dict from request query params."""
    return {
        "format":       args.get("format", "All"),
        "league":       args.get("league", "All"),
        "opponent":     args.get("opponent", "All"),
        "phase":        args.get("phase", "All"),
        "venue":        args.get("venue", "All"),
        "year":         args.get("year", "All"),
        "innings":      args.get("innings", "All"),
        "bowling_type": args.get("bowling_type", "All"),
        "recent":       args.get("recent", "All"),
    }


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
def batter_page():
    return render_template("batter.html", athlete_id=request.args.get("id"))


@app.route("/bowler")
def bowler_page():
    return render_template("bowler.html", athlete_id=request.args.get("id"))


@app.route("/faceoff")
def faceoff_page():
    return render_template(
        "faceoff.html",
        batter_id=request.args.get("batter_id"),
        bowler_id=request.args.get("bowler_id"),
    )


@app.route("/player")
def player_search():
    return render_template("player.html", athlete=None, batting=None, bowling=None)


@app.route("/player/<athlete_id>")
def player_profile(athlete_id):
    data = ds.get_player_profile(athlete_id)
    if not data:
        return "Player not found", 404
    return render_template(
        "player.html",
        athlete=data["athlete"],
        batting=data["batting"],
        bowling=data["bowling"],
    )


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


@app.route("/api/stats/bowler")
def stats_bowler():
    pid = request.args.get("id")
    if not pid:
        return jsonify({"error": "missing id"}), 400
    return jsonify(ds.get_bowler_stats(pid, _filters(request.args)))


@app.route("/api/stats/faceoff")
def stats_faceoff():
    bid  = request.args.get("batter_id")
    boid = request.args.get("bowler_id")
    if not bid or not boid:
        return jsonify({"error": "missing ids"}), 400
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
    if not bid or not boid:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": []})
    return jsonify(ds.get_faceoff_filters(bid, boid, _filters(request.args)))


# ── Run ──────────────────────────────────────────────────────

if __name__ == "__main__":
    # use_reloader=False keeps DuckDB's singleton connection alive.
    # Without this, Flask restarts the process on every file save,
    # which resets _conn=None and triggers a full ~60s S3 re-init.
    app.run(debug=True, port=5000, use_reloader=False)
