from flask import Flask, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import sqlite3
import re
from markupsafe import escape
import utils
import csv

app = Flask(__name__)

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10000 per day"],
    storage_uri="memory://",
)


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
    ch_eng_db_words = set([row["title"] for row in rows])
    conn.close()

    conn = get_new_oxford_db()
    # get all words from db
    rows = conn.execute("SELECT title FROM definitions").fetchall()
    global new_oxford_db_words
    new_oxford_db_words = set([row["title"] for row in rows])
    conn.close()

    # generate a mapping from other verb forms to base forms
    global verb_form_to_base
    verb_form_to_base = {}
    with open("verbs-dictionaries.csv", "r") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) == 5:
                base, third_person, past, past_participle, present_participle = row
                # Map all forms to the base form
                verb_form_to_base[third_person] = base
                verb_form_to_base[past] = base
                verb_form_to_base[past_participle] = base
                verb_form_to_base[present_participle] = base
                # The base form maps to itself for consistency
                if base not in verb_form_to_base:
                    verb_form_to_base[base] = base


def lookup_word_in_ch_eng_db(word: str):
    conn = get_ch_eng_db()
    rows = conn.execute("SELECT * FROM definitions WHERE title = ?", (word,)).fetchall()
    conn.close()
    return rows


def lookup_word_in_new_oxford_db(word: str):
    conn = get_new_oxford_db()
    rows = conn.execute("SELECT * FROM definitions WHERE title = ?", (word,)).fetchall()
    conn.close()
    return rows


init()


def render_dictionary(
    word: str | None,
    words_set,
    lookup_db,
    template_name: str,
    link_prefix: str,
):
    if word is None:
        return render_template(template_name)
    if len(word) > 60:
        return render_template("WordNotFound.html", word=escape(word))
    # try exact match first
    if not word in words_set:
        word = word.lower()
        # try lowercase match
        if not word in words_set:
            # try to map the verb to base form
            if word in verb_form_to_base:
                word = verb_form_to_base.get(word)
            else:
                # or find the most similar word
                word = utils.find_most_similar(word, words_set)
    if word is None:
        return render_template("WordNotFound.html", word=escape(word))
    rows = lookup_db(word)
    if rows is None or len(rows) == 0:
        return render_template("WordNotFound.html", word=escape(word))
    # fix links in entries
    entries = [row["entry"].decode("utf-8") for row in rows]
    entries = [
        re.sub(
            r'href="x-dictionary.*?" title="(.*?)"',
            f'href="{link_prefix}?word=\\1" title="\\1"',
            entry,
        )
        for entry in entries
    ]
    return render_template(template_name, entries=entries)


@app.route("/")
def main():
    return render_template("index.html")


@app.route("/ChineseEnglishDictionary")
@limiter.limit("1 per 1 second")
def chinese_english_dictionary():
    word = request.args.get("word")
    return render_dictionary(
        word=word,
        words_set=ch_eng_db_words,
        lookup_db=lookup_word_in_ch_eng_db,
        template_name="ChineseEnglishDictionary.html",
        link_prefix="/ChineseEnglishDictionary",
    )


@app.route("/NewOxfordAmericanDictionary")
@limiter.limit("1 per 1 second")
def new_oxford_american_dictionary():
    word = request.args.get("word")
    return render_dictionary(
        word=word,
        words_set=new_oxford_db_words,
        lookup_db=lookup_word_in_new_oxford_db,
        template_name="NewOxfordAmericanDictionary.html",
        link_prefix="/NewOxfordAmericanDictionary",
    )
