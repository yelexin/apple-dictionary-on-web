import sqlite3


def get_ch_eng_db():
    conn = sqlite3.connect("db/ChineseEnglishDictionary.db")
    conn.row_factory = sqlite3.Row
    return conn


def get_new_oxford_db():
    conn = sqlite3.connect("db/NewOxfordAmericanDictionary.db")
    conn.row_factory = sqlite3.Row
    return conn


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
