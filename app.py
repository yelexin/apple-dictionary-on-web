from flask import Flask, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from typing import Callable
import re
from markupsafe import escape
from db import get_ch_eng_db, get_new_oxford_db, lookup_word_in_ch_eng_db, lookup_word_in_new_oxford_db
import utils
import csv
import inflect
import importlib.resources
from symspellpy import SymSpell, Verbosity


sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
sym_spell.load_dictionary(
    importlib.resources.path(
        "symspellpy", "frequency_dictionary_en_82_765.txt"
    ).__enter__(),
    term_index=0,
    count_index=1,
)
p = inflect.engine()

app = Flask(__name__)
# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10000 per day"],
    storage_uri="memory://",
)




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




init()


def toLowerCase(word: str) -> str:
    return word.lower()


def toBaseForm(word: str) -> str | None:
    return verb_form_to_base.get(word, None)


def toSingular(word: str) -> str | None:
    return p.singular_noun(word) or None  # type: ignore


def toSimilarWord(words_set: set[str]) -> Callable[[str], str | None]:
    def inner(word: str) -> str | None:
        return utils.find_most_similar(word, words_set)

    return inner


def correctSpelling(word: str) -> str | None:
    suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions:
        return suggestions[0].term
    return None


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
        transforms = [
            lambda x: x,
            toBaseForm,
            toSingular,
            correctSpelling,
            # toSimilarWord(words_set),
        ]
        for transform in transforms:
            transformed_word = transform(word)
            if transformed_word and transformed_word in words_set:
                word = transformed_word
                break

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
