from flask import Flask, request, render_template
import sqlite3
import re
from markupsafe import escape

app = Flask(__name__)

def get_ch_eng_db():
    conn = sqlite3.connect('db/ChineseEnglishDictionary.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_new_oxford_db():
    conn = sqlite3.connect('db/NewOxfordAmericanDictionary.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/ChineseEnglishDictionary")
def chinese_english_dictionary():
    word = request.args.get("word")
    if word is None:
        return render_template('ChineseEnglishDictionary.html')
    conn = get_ch_eng_db()
    row = conn.execute("SELECT * FROM definitions WHERE title = ?", (word,)).fetchone()
    conn.close()
    if row is None:
        return render_template('WordNotFound.html', word=escape(word))
    entry = row["entry"].decode("utf-8")
    entry = re.sub(r'href="x-dictionary.*?"', '', entry)
    return render_template('ChineseEnglishDictionary.html', entry=entry)

@app.route("/NewOxfordAmericanDictionary")
def new_oxford_american_dictionary():
    word = request.args.get("word")
    if word is None:
        return render_template('NewOxfordAmericanDictionary.html')
    conn = get_new_oxford_db()
    row = conn.execute("SELECT * FROM definitions WHERE title = ?", (word,)).fetchone()
    conn.close()
    if row is None:
        return render_template('WordNotFound.html', word=escape(word))
    entry = row["entry"].decode("utf-8")
    # entry = re.sub(r'href="x-dictionary.*?"', '', entry)
    return render_template('NewOxfordAmericanDictionary.html', entry=entry)
