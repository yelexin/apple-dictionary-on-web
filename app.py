from flask import Flask, request, render_template
import sqlite3
import re
from markupsafe import escape
import utils

app = Flask(__name__)


def get_ch_eng_db():
    conn = sqlite3.connect("db/ChineseEnglishDictionary.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_new_oxford_db():
    conn = sqlite3.connect("db/NewOxfordAmericanDictionary.db")
    conn.row_factory = sqlite3.Row
    return conn


def init():
    conn = get_ch_eng_db()
    # get all words from db
    rows = conn.execute("SELECT title FROM definitions").fetchall()
    global ch_eng_db_words
    ch_eng_db_words = [row["title"] for row in rows]
    conn.close()

    conn = get_new_oxford_db()
    # get all words from db
    rows = conn.execute("SELECT title FROM definitions").fetchall()
    global new_oxford_db_words
    new_oxford_db_words = [row["title"] for row in rows]
    conn.close()


init()


@app.route("/")
def main():
    return render_template("index.html")


@app.route("/ChineseEnglishDictionary")
def chinese_english_dictionary():
    word = request.args.get("word")
    if word is None:
        return render_template("ChineseEnglishDictionary.html")
    word = word.lower()
    most_similar_word = utils.find_most_similar(word, ch_eng_db_words)
    if most_similar_word is None:
        return render_template("WordNotFound.html", word=escape(word))

    conn = get_ch_eng_db()
    rows = conn.execute(
        "SELECT * FROM definitions WHERE title = ?", (most_similar_word,)
    ).fetchall()
    conn.close()
    if rows is None or len(rows) == 0:
        return render_template("WordNotFound.html", word=escape(word))
    entries = [row["entry"].decode("utf-8") for row in rows]
    entries = [
        re.sub(
            r'href="x-dictionary.*?" title="(.*?)"',
            'href="/ChineseEnglishDictionary?word=\\1" title="\\1"',
            entry,
        )
        for entry in entries
    ]
    return render_template("ChineseEnglishDictionary.html", entries=entries)


@app.route("/NewOxfordAmericanDictionary")
def new_oxford_american_dictionary():
    word = request.args.get("word")
    if word is None:
        return render_template("NewOxfordAmericanDictionary.html")
    word = word.lower()
    most_similar_word = utils.find_most_similar(word, new_oxford_db_words)
    if most_similar_word is None:
        return render_template("WordNotFound.html", word=escape(word))

    conn = get_new_oxford_db()
    rows = conn.execute(
        "SELECT * FROM definitions WHERE title = ?", (most_similar_word,)
    ).fetchall()
    conn.close()
    if rows is None or len(rows) == 0:
        return render_template("WordNotFound.html", word=escape(word))
    entries = [row["entry"].decode("utf-8") for row in rows]
    entries = [
        re.sub(
            r'href="x-dictionary.*?" title="(.*?)"',
            'href="/NewOxfordAmericanDictionary?word=\\1" title="\\1"',
            entry,
        )
        for entry in entries
    ]
    return render_template("NewOxfordAmericanDictionary.html", entries=entries)
