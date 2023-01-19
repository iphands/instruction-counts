import json
import sqlite3
from typing import Any, Dict

import click

import constants as const

def get_family(meta: Dict[str, Any]) -> str:
    for form in meta['forms']:
        if 'isa' in form:
            # if len(form['isa']) != 1:
            #     if form['isa'][0]['id'].lower().startswith('avx512'):
            #         return 'avx512'
            #     print(f"WARN: {form['isa']}")
            # return form['isa'][0]['id'].lower()
            family = form['isa'][0]['id'].lower()
            if family.startswith('avx512'):
                return 'avx512'

            if family not in const.FAMILY_ALLOW:
                return ''

            return family
    return ''

def do_x86_64(filepath: str, cur: sqlite3.Cursor) -> None:
    with open(filepath, 'r', encoding='UTF-8') as file_handle:
        data = json.loads(file_handle.read())
        for name, meta  in data['instructions'].items():
            family = get_family(meta)
            args = (name.lower(), family, 'x86_64')
            cur.execute('INSERT OR IGNORE INTO instr(opcode, family, arch) VALUES(?, ?, ?)', args)

def do_ingest(filepath: str, cur: sqlite3.Cursor) -> None:
    if 'x86_64' in filepath:
        do_x86_64(filepath, cur)
        return
    assert False, "For now only x86_64 is supported"


def prep_db() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    con = sqlite3.connect(const.DATABASE)
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS instr(
    id INTEGER PRIMARY KEY,
    opcode TEXT NOT NULL UNIQUE,
    family TEXT,
    arch TEXT
    )
    ''')

    return (con, cur)

@click.command()
def ingest_refs() -> None:
    con, cur = prep_db()
    for ref in const.REFS:
        do_ingest(ref, cur)
    con.commit()
    con.close()
