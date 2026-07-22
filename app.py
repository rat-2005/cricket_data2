"""
app.py — Cricket Analytics Dashboard

Thin Flask layer. All data logic lives in data_service.py (blackbox).
All database access goes through db.py (DuckDB + S3 Parquet).
No PostgreSQL. No raw SQL in this file.
"""
from flask import Flask, render_template, request, jsonify, redirect, g
import data_service as ds
import logging
import logging.handlers
import os
import re
import time
import uuid
from pythonjsonlogger import jsonlogger

# ── Production Logging Setup (PLG-Ready Structured JSON) ────────
_log_dir = '/data' if os.path.isdir('/data') else '.'
_log_file = os.path.join(_log_dir, 'app.log')
_security_log_file = os.path.join(_log_dir, 'security.log')

# ── Suspicious pattern detection for security logging ────────
SUSPICIOUS_PATTERNS = [
    re.compile(r"(\.\./|\.\.\\)", re.IGNORECASE),           # Path traversal
    re.compile(r"(union\s+select|drop\s+table|;\s*delete)", re.IGNORECASE),  # SQL injection
    re.compile(r"(<script|javascript:|onerror=)", re.IGNORECASE),            # XSS
    re.compile(r"(etc/passwd|/proc/self|cmd\.exe)", re.IGNORECASE),          # OS probe
    re.compile(r"(\.env|\.git/|wp-admin|phpmyadmin)", re.IGNORECASE),        # Common scans
]

# ── Sensitive data mask list ────────
SENSITIVE_KEYS = {'password', 'token', 'authorization', 'api_key', 'secret', 'cookie', 'session'}

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Enterprise JSON formatter with correlation ID injection and data sanitization."""
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        # Inject correlation ID if in Flask context
        if not log_record.get('request_id'):
            try:
                from flask import has_request_context, g as flask_g
                if has_request_context() and hasattr(flask_g, 'request_id'):
                    log_record['request_id'] = flask_g.request_id
            except Exception:
                pass
        
        # Sanitize sensitive fields
        for key in list(log_record.keys()):
            if key.lower() in SENSITIVE_KEYS:
                log_record[key] = '***MASKED***'

def _build_handler(path, max_bytes=10*1024*1024, backup_count=5):
    """Create a rotating file handler with JSON formatting."""
    handler = logging.handlers.RotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    handler.setFormatter(CustomJsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    return handler

# ── App log (general) ────────
app_file_handler = _build_handler(_log_file)
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomJsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
logging.basicConfig(level=logging.INFO, handlers=[app_file_handler, console_handler])

# ── Security log (separate file for audit trail) ────────
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)
security_logger.addHandler(_build_handler(_security_log_file))
security_logger.addHandler(console_handler)
security_logger.propagate = False

# ── Wire Gunicorn/Werkzeug into same handlers ────────
for logger_name in ('gunicorn.error', 'werkzeug'):
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.INFO)
    _logger.handlers = []
    _logger.addHandler(app_file_handler)
    _logger.addHandler(console_handler)

log = logging.getLogger('app')
log.info({"event": "app_startup", "log_file": _log_file, "security_log": _security_log_file})

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# REQUEST LIFECYCLE MIDDLEWARE (Enterprise Observability)
# ═══════════════════════════════════════════════════════════════

@app.before_request
def before_request_middleware():
    """Runs before every request. Injects correlation ID, logs request, runs security checks."""
    # 1. Correlation ID
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.request_start_time = time.time()

    # 2. Extract client context
    g.client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
    if ',' in g.client_ip:
        g.client_ip = g.client_ip.split(',')[0].strip()  # First IP in chain

    # 3. Log every request (INFO level)
    log.info({
        "event": "request_started",
        "method": request.method,
        "path": request.path,
        "query": request.query_string.decode('utf-8', errors='replace')[:500],
        "client_ip": g.client_ip,
        "user_agent": request.headers.get('User-Agent', 'unknown')[:300],
        "referer": request.headers.get('Referer', 'direct')[:500],
        "content_length": request.content_length or 0,
        "accept_language": request.headers.get('Accept-Language', 'unknown')[:100],
        "origin": request.headers.get('Origin', 'none'),
    })

    # 4. Security: Detect suspicious patterns
    full_url = request.url
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(full_url):
            security_logger.warning({
                "event": "suspicious_request",
                "threat_type": pattern.pattern[:50],
                "method": request.method,
                "path": request.path,
                "full_url": full_url[:1000],
                "client_ip": g.client_ip,
                "user_agent": request.headers.get('User-Agent', 'unknown')[:300],
                "referer": request.headers.get('Referer', 'direct'),
            })
            break  # One alert per request

    # 5. Security: Detect oversized payloads (potential DoS)
    if request.content_length and request.content_length > 1_000_000:
        security_logger.warning({
            "event": "oversized_payload",
            "content_length": request.content_length,
            "client_ip": g.client_ip,
            "path": request.path,
        })

@app.after_request
def after_request_middleware(response):
    """Runs after every request. Logs response details with latency."""
    duration_ms = round((time.time() - getattr(g, 'request_start_time', time.time())) * 1000, 2)

    # Log completed request with response metadata
    log_data = {
        "event": "request_completed",
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "duration_ms": duration_ms,
        "response_size": response.content_length or 0,
        "client_ip": getattr(g, 'client_ip', 'unknown'),
    }

    # Use appropriate log level based on status code
    if response.status_code >= 500:
        log.error(log_data)
    elif response.status_code >= 400:
        log.warning(log_data)
    else:
        log.info(log_data)

    # Flag slow requests (> 5 seconds)
    if duration_ms > 5000:
        log.warning({
            "event": "slow_request",
            "method": request.method,
            "path": request.path,
            "duration_ms": duration_ms,
            "client_ip": getattr(g, 'client_ip', 'unknown'),
        })

    # Inject headers
    response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
    response.headers['X-Response-Time'] = f"{duration_ms}ms"
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Global unhandled exception logger."""
    log.critical({
        "event": "unhandled_exception",
        "error_type": type(e).__name__,
        "error_message": str(e)[:500],
        "method": request.method,
        "path": request.path,
        "client_ip": getattr(g, 'client_ip', 'unknown'),
    })
    return jsonify({"error": "Internal server error"}), 500

# ═══════════════════════════════════════════════════════════════
# LOG VIEWER ROUTE (Admin-only in production)
# ═══════════════════════════════════════════════════════════════

@app.route("/admin/logs")
def view_logs():
    """View recent log entries in the browser. Query params: lines (default 100), type (app|security)."""
    log_type = request.args.get('type', 'app')
    num_lines = min(int(request.args.get('lines', 100)), 500)
    
    target_file = _security_log_file if log_type == 'security' else _log_file
    
    if not os.path.exists(target_file):
        return jsonify({"error": f"No {log_type} log file found", "path": target_file}), 404
    
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent = lines[-num_lines:] if len(lines) > num_lines else lines
        from flask import Response
        return Response(''.join(recent), mimetype='text/plain')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
@app.route("/faceoff/<slug>")
def faceoff_page(slug=None):
    batter_id = request.args.get("batter_id", "")
    bowler_id = request.args.get("bowler_id", "")
    batter_info = None
    bowler_info = None

    if slug and "-vs-" in slug:
        parts = slug.split("-vs-")
        batter_slug, bowler_slug = parts[0], parts[1]
        batter_info = ds.get_player_by_slug(batter_slug)
        bowler_info = ds.get_player_by_slug(bowler_slug)
        if batter_info: batter_id = batter_info["id"]
        if bowler_info: bowler_id = bowler_info["id"]

    if batter_id and not batter_info:
        batter_info = ds.get_player_info(batter_id)
    if bowler_id and not bowler_info:
        bowler_info = ds.get_player_info(bowler_id)

    if batter_info and bowler_info:
        expected_slug = f"{batter_info.get('slug','')}-vs-{bowler_info.get('slug','')}"
        if slug != expected_slug:
            return redirect(f"/faceoff/{expected_slug}")

    return render_template(
        "faceoff.html",
        batter_id=batter_id,
        bowler_id=bowler_id,
        batter_info=batter_info,
        bowler_info=bowler_info,
    )


@app.route("/player/<identifier>")
def player_page(identifier):
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

# Start daily background cron job to sync Parquet files at 4:30 AM IST (23:00 UTC)
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from db import safe_hot_swap

def start_scheduler():
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    # 23:00 UTC is exactly 04:30 AM IST. 
    # This runs 1.5 hours after the GitHub Actions pipeline starts at 3:00 AM IST.
    scheduler.add_job(safe_hot_swap, 'cron', hour=23, minute=0)
    scheduler.start()
    log.info({"event": "scheduler_started", "job": "safe_hot_swap", "schedule": "23:00 UTC daily"})

# Start it automatically
start_scheduler()

if __name__ == "__main__":
    # use_reloader=False keeps DuckDB's singleton connection alive.
    # Without this, Flask restarts the process on every file save,
    # which resets _conn=None and triggers a full ~60s S3 re-init.
    app.run(debug=True, port=5000, use_reloader=False)
