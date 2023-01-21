import json
import sqlite3
from typing import Any, Dict, List

import click

import constants as const

def get_isas(forms: List[Dict[str, Any]]) -> List[str]:
    isas = []
    for form in forms:
        if 'isa' not in form:
            continue
        if len(form['isa']) == 0:
            continue

        for i in form['isa']:
            isa = i['id'].lower()
            # NOTE: We collapse all AVX512* into one here
            # We might not want to do this in the future
            if isa.startswith('avx512'):
                isa = 'avx512'
            isas.append(isa)

    if not isas:
        return ['']
    return list(set(isas))

def do_x86_64(filepath: str, cur: sqlite3.Cursor) -> None:
    with open(filepath, 'r', encoding='utf-8') as file_handle:
        data = json.loads(file_handle.read())
        for name, meta  in data['instructions'].items():
            for isa in get_isas(meta['forms']):
                family = isa
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
    opcode TEXT NOT NULL,
    family TEXT,
    arch TEXT NOT NULL,
    UNIQUE (opcode, family, arch)
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
