import os
import secrets
from html import escape
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Flask, Response, redirect, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024
DATA = Path(os.environ.get("RESEARCH_DATA", "/data/research.txt"))


def content():
    if DATA.exists():
        return DATA.read_text(encoding="utf-8")
    return "กรุณาเพิ่มสรุปงานวิจัย 300–500 คำผ่านหน้า admin"


def authorized():
    auth = request.authorization
    username = os.environ.get("ADMIN_USER", "")
    password = os.environ.get("ADMIN_PASSWORD", "")
    return bool(
        username and password and auth and auth.type == "basic"
        and secrets.compare_digest((auth.username or "").encode(), username.encode())
        and secrets.compare_digest((auth.password or "").encode(), password.encode())
    )


@app.get("/")
def admin_root():
    return redirect("/edit")


@app.get("/research")
def research():
    return (
        '<meta charset="utf-8"><title>Research Summary</title><h1>Research Summary</h1>'
        '<article style="white-space:pre-wrap;max-width:900px">'
        + escape(content()) + "</article>"
    )


@app.route("/edit", methods=["GET", "POST"])
def edit():
    if not authorized():
        return Response(
            "Authentication required", 401, {"WWW-Authenticate": 'Basic realm="ResearchAdmin"'}
        )
    if request.method == "POST":
        if request.headers.get("Sec-Fetch-Site") in {"cross-site", "same-site"}:
            return "Invalid request origin", 403
        summary = request.form.get("summary", "").strip()
        if not summary or len(summary) > 20000:
            return "Invalid length", 400
        DATA.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=DATA.parent, delete=False) as handle:
            temporary = Path(handle.name)
            try:
                handle.write(summary)
                handle.close()
                temporary.replace(DATA)
            finally:
                temporary.unlink(missing_ok=True)
        return redirect("/edit?saved=1", code=303)
    saved = '<p role="status">บันทึกแล้ว</p>' if request.args.get("saved") == "1" else ""
    return (
        '<meta charset="utf-8"><title>Edit research</title><h1>Edit research</h1>' + saved
        + '<form method="post"><label for="summary">Research summary</label><br>'
        + '<textarea id="summary" name="summary" rows="22" cols="95">' + escape(content())
        + '</textarea><br><button type="submit">Save</button></form>'
    )


@app.get("/health")
def health():
    return "OK"
