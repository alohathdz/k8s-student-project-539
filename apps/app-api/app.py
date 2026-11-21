from flask import Flask
from html import escape
app=Flask(__name__)
@app.get("/api/<path:message>")
def show(message):
    return f'<meta charset="utf-8"><div style="min-height:100vh;display:grid;place-items:center"><h1 style="font: bold 6vw sans-serif;overflow-wrap:anywhere">{escape(message)}</h1></div>'
@app.get("/health")
def health(): return "OK"
