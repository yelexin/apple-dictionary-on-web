import sqlite3

from utils import timeit


class DictionaryDB:
    def __init__(self, db_path: str):
        print("Opening database connection")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def __del__(self):
        print("Closing database connection")
        self.conn.close()


    def find_definition_by_id(self, id: int) -> str | None:
        row = self.conn.execute(
            "SELECT article FROM entry WHERE id = ?", (id,)
        ).fetchone()
        if not row:
            return None
        definition = row["article"]
        return definition

    def find_definitions_by_ids(self, ids: list[int]) -> list[str]:
        rows = self.conn.execute(
            f"SELECT article FROM entry WHERE id IN ({','.join(['?']*len(ids))})", ids
        ).fetchall()
        definitions = [row["article"] for row in rows]
        return definitions

    @timeit
    def find_definitions_by_alt(self, alt: str) -> list[str]:
        rows = self.conn.execute("SELECT id FROM alt WHERE term = ? COLLATE NOCASE", (alt,)).fetchall()
        ids = [row["id"] for row in rows]
        definitions = self.find_definitions_by_ids(ids)
        return definitions

    @timeit
    def find_definitions_by_term(self, term: str) -> list[str]:
        rows = self.conn.execute(
            "SELECT article FROM entry WHERE term = ? COLLATE NOCASE", (term,)
        ).fetchall()
 
        definitions = [row["article"] for row in rows]
        return definitions