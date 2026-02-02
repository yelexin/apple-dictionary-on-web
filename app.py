import os
from typing import Callable

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from markupsafe import escape
from symspellpy import SymSpell, Verbosity

import utils
from service import Dictionary, DictionaryService, HtmlService

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYM_SPELL_DICTIONARY_PATH = os.path.join(BASE_DIR, "assets", "en-80k.txt")

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
sym_spell.load_dictionary(
    SYM_SPELL_DICTIONARY_PATH,
    term_index=0,
    count_index=1,
)

app = Flask(__name__)
# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10000 per day"],
    storage_uri="memory://",
)


def init():
    if os.getenv("ENABLE_CACHE") == "true":
        DictionaryService.create_cache()


init()


def toLowerCase(word: str) -> str:
    return word.lower()


def toSimilarWord(words_set: set[str]) -> Callable[[str], str | None]:
    def inner(word: str) -> str | None:
        return utils.find_most_similar(word, words_set)

    return inner


def correctSpelling(word: str) -> str:
    suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions:
        return suggestions[0].term
    return word


def toLowerCaseAndCorrectSpelling(word: str) -> str:
    lower_word = word.lower()
    suggestions = sym_spell.lookup(lower_word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions:
        return suggestions[0].term
    return lower_word


def returnSelf(word: str) -> str:
    return word


def render_dictionary(
    word: str | None,
    dictionary: Dictionary,
):
    DICTIONARY_TEMPLATE = dictionary.value + ".html"
    LINK_PREFIX = f"/{dictionary.value}"
    if word is None:
        return render_template(DICTIONARY_TEMPLATE)
    word = word.strip()
    if len(word) > 60:
        return render_template("WordNotFound.html", word=escape(word))
    dictionary_service = DictionaryService(dictionary)
    transforms = [
        returnSelf,
        toLowerCase,
        correctSpelling,
        toLowerCaseAndCorrectSpelling,
    ]
    definitions = []
    for transform in transforms:
        # try to transform the word
        transformed_word = transform(word)
        print(transformed_word)
        # try exact match first
        definitions = dictionary_service.find_definitions_by_term(transformed_word)
        # then try alt match
        if len(definitions) == 0:
            definitions = dictionary_service.find_definitions_by_alt(transformed_word)
        if len(definitions) > 0:
            break
    if len(definitions) == 0:
        return render_template("WordNotFound.html", word=escape(word))

    for i in range(len(definitions)):
        definitions[i] = HtmlService.fix_links_in_definition(
            definitions[i], LINK_PREFIX
        )
        definitions[i] = HtmlService.remove_stylesheet_tags(definitions[i])

    return render_template(DICTIONARY_TEMPLATE, entries=definitions)


@app.route("/")
def main():
    return render_template("index.html")


@app.route("/ChineseEnglishDictionary")
@limiter.limit("1 per 1 second")
def chinese_english_dictionary():
    word = request.args.get("word")
    return render_dictionary(
        word=word,
        dictionary=Dictionary.CHINESE_ENGLISH,
    )


@app.route("/NewOxfordAmericanDictionary")
@limiter.limit("1 per 1 second")
def new_oxford_american_dictionary():
    word = request.args.get("word")
    return render_dictionary(
        word=word,
        dictionary=Dictionary.NEW_OXFORD_AMERICAN,
    )


@app.route("/SwedishEnglishDictionary")
@limiter.limit("1 per 1 second")
def swedish_english_dictionary():
    word = request.args.get("word")
    return render_dictionary(
        word=word,
        dictionary=Dictionary.SWEDISH_ENGLISH_DICTIONARY,
    )
