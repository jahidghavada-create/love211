import hmac
import os
import re
import secrets
from datetime import date, time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from markupsafe import Markup, escape
from werkzeug.exceptions import HTTPException

import database as db

ROOT = Path(__file__).resolve().parent

# VERCEL ENTRYPOINT: vercel.json points to this file ("src": "app.py"), and Vercel
# runs the module-level Flask object named `app` defined below. Keep that name.

DEFAULT_FINAL_MESSAGE = (
    "Wait for me for five years, my Qalbi ❤️\n\n"
    "Get well soon, my baby. Take care of yourself and keep smiling. "
    "Your happiness matters so much to me."
)
DRIVE_URL = os.environ.get(
    "AASHI_EDIT_COLLECTION_URL",
    "https://drive.google.com/drive/folders/1TA19GRnZrIkguMG9As3s1QH2rUtDHOjE?usp=drive_link",
)

# stage 0 = logged out, 1 = proposal, 2 = beauty, 3 = date invite opened,
# 4 = date answered, 5 = funny, 6 = final
STAGE_PAGE = {1: "proposal", 2: "beauty", 3: "date", 4: "date", 5: "funny", 6: "final"}

USERNAME = os.environ.get("PROPOSAL_USERNAME", "").strip().casefold()
PASSWORD = os.environ.get("PROPOSAL_PASSWORD", "")
SECRET = os.environ.get("FLASK_SECRET_KEY", "")
CONFIGURED = bool(USERNAME and PASSWORD and SECRET)

on_vercel = os.environ.get("VERCEL") == "1"

app = Flask(
    __name__,
    static_folder=str(ROOT / "public" / "static"),
    static_url_path="/static",
    template_folder=str(ROOT / "templates"),
)
app.config.update(
    SECRET_KEY=SECRET or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1"
    or (on_vercel and os.environ.get("VERCEL_ENV") in {"preview", "production"}),
    PERMANENT_SESSION_LIFETIME=8 * 60 * 60,
    MAX_CONTENT_LENGTH=64 * 1024,
)


# ---------- security helpers ----------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


@app.context_processor
def template_helpers():
    return {"csrf_input": lambda: Markup(f'<input type="hidden" name="_csrf" value="{csrf_token()}">')}


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("_csrf", "").encode("utf-8")
        expected = session.get("_csrf", "").encode("utf-8")
        if not sent or not hmac.compare_digest(sent, expected):
            abort(400)


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response


@app.errorhandler(400)
def bad_request(_error):
    return render_template("error.html"), 400


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html"), 404


@app.errorhandler(Exception)
def unexpected_error(error):
    if isinstance(error, HTTPException):
        return error
    app.logger.exception("Unhandled error")
    if os.environ.get("SHOW_ERRORS") == "1":
        return f"<pre>{type(error).__name__}: {escape(str(error))}</pre>", 500
    return "Something went wrong. Please try again in a moment.", 500


@app.get("/health")
def health():
    """Plain check with no templates or database: shows what the server can see."""
    templates = ROOT / "templates"
    return {
        "app": "running",
        "env_set": {
            "FLASK_SECRET_KEY": bool(SECRET),
            "PROPOSAL_USERNAME": bool(USERNAME),
            "PROPOSAL_PASSWORD": bool(PASSWORD),
        },
        "root_files": sorted(p.name for p in ROOT.iterdir())[:40],
        "template_files": sorted(p.name for p in templates.iterdir()) if templates.is_dir() else "templates folder NOT FOUND",
    }


def gate(minimum):
    """Send the visitor back to the page they've reached if they skip ahead."""
    stage = session.get("stage", 0)
    if stage < minimum:
        return redirect(url_for(STAGE_PAGE.get(stage, "login")))
    return None


# ---------- video ----------
def video_from_url(value):
    """Return (kind, source, mime_type) for a public https video link, or None."""
    value = (value or "").strip()
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not host or parsed.username or parsed.password:
            return None
    except ValueError:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        if host == "youtu.be":
            vid = parts[0] if parts else ""
        elif parsed.path == "/watch":
            vid = parse_qs(parsed.query).get("v", [""])[0]
        else:
            vid = parts[1] if len(parts) > 1 and parts[0] in {"embed", "shorts", "live"} else ""
        if re.fullmatch(r"[A-Za-z0-9_-]{6,20}", vid):
            return "embed", f"https://www.youtube-nocookie.com/embed/{vid}?playsinline=1&rel=0", ""
        return None
    if host in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        if parts and parts[0] == "video":
            parts = parts[1:]
        if parts and re.fullmatch(r"[0-9]{6,12}", parts[0]):
            return "embed", f"https://player.vimeo.com/video/{parts[0]}?playsinline=1", ""
        return None
    mime = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}.get(
        Path(parsed.path).suffix.lower()
    )
    return ("direct", value, mime) if mime else None


# ---------- pages ----------
@app.get("/")
def index():
    return redirect(url_for(STAGE_PAGE.get(session.get("stage", 0), "login")))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("stage", 0) >= 1:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "")[:80]
        password = request.form.get("password", "")
        ok = (
            CONFIGURED
            and name.strip().casefold() == USERNAME
            and hmac.compare_digest(password.encode("utf-8"), PASSWORD.encode("utf-8"))
        )
        login_id = db.record_login(name, ok)
        if ok:
            session.clear()
            session.permanent = True
            session["stage"] = 1
            session["login_id"] = login_id
            session["response_id"] = db.create_response(login_id)
            return redirect(url_for("proposal"))
        flash("That didn't match. Try again, my baby 🥺", "error")
    return render_template("login.html", configured=CONFIGURED)


@app.get("/proposal")
def proposal():
    if (r := gate(1)):
        return r
    return render_template("proposal.html", answer=session.get("proposal_answer"))


@app.post("/proposal/answer")
def proposal_answer():
    if (r := gate(1)):
        return r
    answer = request.form.get("answer")
    if answer not in {"yes", "no"}:
        abort(400)
    session["proposal_answer"] = answer
    db.set_answer(session.get("response_id"), "proposal", answer == "yes")
    if answer == "yes":
        session["stage"] = max(session["stage"], 2)
        return redirect(url_for("beauty"))
    return redirect(url_for("proposal"))


@app.get("/beauty")
def beauty():
    if (r := gate(2)):
        return r
    return render_template("beauty.html")


@app.post("/date/open")
def open_date():
    if (r := gate(2)):
        return r
    session["stage"] = max(session["stage"], 3)
    return redirect(url_for("date_invitation"))


@app.route("/date", methods=["GET", "POST"])
def date_invitation():
    if (r := gate(3)):
        return r
    response_id = session.get("response_id")

    if request.method == "POST":
        action = request.form.get("action")
        if action in {"yes", "no"}:
            session["date_answer"] = action
            session["stage"] = max(session["stage"], 4)
            db.set_answer(response_id, "date", action == "yes")
            return redirect(url_for("date_invitation"))

        if action == "plan" and session.get("date_answer") == "yes":
            v = {k: request.form.get(k, "").strip() for k in (
                "preferred_date", "preferred_time", "preferred_location",
                "activity", "food_or_drink", "message")}
            limits = {"preferred_location": 120, "food_or_drink": 120, "message": 1000}
            try:
                if v["preferred_date"]:
                    date.fromisoformat(v["preferred_date"])
                if v["preferred_time"]:
                    time.fromisoformat(v["preferred_time"])
                if any(len(v[k]) > n for k, n in limits.items()):
                    raise ValueError
                if v["activity"] not in {"", "cafe", "dinner", "walk", "movie", "other"}:
                    raise ValueError
                if v["activity"] == "other":
                    other = request.form.get("other_activity", "").strip()
                    if not other or len(other) > 80:
                        raise ValueError
                    v["activity"] = f"other: {other}"
            except ValueError:
                flash("Please check the plan details and try again.", "error")
                return redirect(url_for("date_invitation"))
            db.save_plan(response_id, v)
            session["plan_saved"] = True
            return redirect(url_for("date_invitation"))
        abort(400)

    return render_template(
        "date.html", answer=session.get("date_answer"), plan_saved=session.get("plan_saved", False)
    )


@app.post("/funny/open")
def open_funny():
    if (r := gate(4)):
        return r
    session["stage"] = max(session["stage"], 5)
    return redirect(url_for("funny"))


@app.get("/funny")
def funny():
    if (r := gate(5)):
        return r
    return render_template("funny.html")


@app.post("/final/open")
def open_final():
    if (r := gate(5)):
        return r
    session["stage"] = max(session["stage"], 6)
    return redirect(url_for("final"))


@app.get("/final")
def final():
    if (r := gate(6)):
        return r
    message = os.environ.get("FINAL_MESSAGE", DEFAULT_FINAL_MESSAGE).replace("\\n", "\n")
    video = video_from_url(os.environ.get("FINAL_VIDEO_URL", ""))
    return render_template("final.html", message=message, video=video)


@app.get("/editing-show")
def editing_show():
    if (r := gate(6)):
        return r
    return render_template("editing.html", drive_url=DRIVE_URL)


@app.post("/replay")
def replay():
    if (r := gate(1)):
        return r
    for key in ("proposal_answer", "date_answer", "plan_saved"):
        session.pop(key, None)
    session["stage"] = 1
    session["response_id"] = db.create_response(session.get("login_id"))
    return redirect(url_for("proposal"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=os.environ.get("FLASK_DEBUG") == "1")
