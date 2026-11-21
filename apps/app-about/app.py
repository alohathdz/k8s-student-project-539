import os
from pathlib import Path

from flask import Flask, render_template_string

app = Flask(__name__)


@app.get("/about")
def about():
    return render_template_string(
        """<!doctype html><html lang="th"><meta charset="utf-8">
        <title>Student Information</title><h1>Student Information</h1>
        {% if photo %}<img width="220" src="/static/student.jpg" alt="รูปนักศึกษา">{% endif %}
        <p>Name: {{ name }}</p><p>ID: {{ student_id }}</p></html>""",
        name=os.environ.get("STUDENT_NAME", "Student"),
        student_id=os.environ.get("STUDENT_ID", "539"),
        photo=(Path(app.static_folder) / "student.jpg").is_file(),
    )


@app.get("/health")
def health():
    return "OK"
