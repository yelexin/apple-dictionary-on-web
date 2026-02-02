import re
from db import DictionaryDB
from enum import Enum
import os


class Dictionary(Enum):
    CHINESE_ENGLISH = "ChineseEnglishDictionary"
    NEW_OXFORD_AMERICAN = "NewOxfordAmericanDictionary"
    SWEDISH_ENGLISH_DICTIONARY = "SwedishEnglishDictionary"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class HtmlService:
    @staticmethod
    def fix_links_in_definition(definition: str, link_prefix: str) -> str:
        return re.sub(
            r'href="bword://.*" title="(.*?)"',
            f'href="{link_prefix}?word=\\1" title="\\1"',
            definition,
        )


    @staticmethod
    def remove_stylesheet_tags(text: str) -> str:
        return text.replace(r'<link rel="stylesheet" href="style.css">', "")


class DictionaryService:
    dict_base_cache = None
    dict_alt_cache = None

    @classmethod
    def create_cache(cls):
        dict_base_cache = {}
        dict_alt_cache = {}
        dictionaries = [
            Dictionary.CHINESE_ENGLISH,
            Dictionary.NEW_OXFORD_AMERICAN,
            Dictionary.SWEDISH_ENGLISH_DICTIONARY,
        ]
        for dictionary in dictionaries:
            DICTIONARY_DB_PATH = os.path.join(BASE_DIR, "db", dictionary.value + ".db")
            dict_alt_cache[dictionary] = {}

            db = DictionaryDB(DICTIONARY_DB_PATH)
            rows = db.conn.execute("SELECT DISTINCT term FROM entry").fetchall()
            words = [row["term"] for row in rows]
            dict_base_cache[dictionary] = set(words)
            rows = db.conn.execute("SELECT id,term FROM alt").fetchall()
            for row in rows:
                if row["term"] not in dict_alt_cache[dictionary]:
                    dict_alt_cache[dictionary][row["term"]] = []
                dict_alt_cache[dictionary][row["term"]].append(row["id"])
        print("Cache initialization completed")
        cls.dict_base_cache = dict_base_cache
        cls.dict_alt_cache = dict_alt_cache

    def __init__(self, dictionary: Dictionary):
        DICTIONARY_DB_PATH = os.path.join(BASE_DIR, "db", dictionary.value + ".db")
        self.dictionary = dictionary
        self.db = DictionaryDB(DICTIONARY_DB_PATH)

    def find_definitions_by_term(self, term: str) -> list[str]:
        if self.dict_base_cache and term not in self.dict_base_cache[self.dictionary]:
            return []
        return self.db.find_definitions_by_term(term)

    def find_definitions_by_alt(self, alt: str) -> list[str]:
        if self.dict_alt_cache:
            if alt not in self.dict_alt_cache[self.dictionary]:
                return []
            ids = self.dict_alt_cache[self.dictionary][alt]
            return self.db.find_definitions_by_ids(ids)
        return self.db.find_definitions_by_alt(alt)

    def find_definition_by_id(self, id: int) -> str | None:
        return self.db.find_definition_by_id(id)

    def find_definitions_by_ids(self, ids: list[int]) -> list[str]:
        return self.db.find_definitions_by_ids(ids)
