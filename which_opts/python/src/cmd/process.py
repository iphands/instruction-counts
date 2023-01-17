import click
import os
import logging as log
import sqlite3
import json
import constants as const

def prep_db() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    con = sqlite3.connect(const.DATABASE)
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS profile(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
    )
    ''')

    cur.execute('''CREATE TABLE IF NOT EXISTS bin(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
    )
    ''')

    cur.execute('''CREATE TABLE IF NOT EXISTS op_count(
    id INTEGER PRIMARY KEY,
    bin_id INTEGER,
    prof_id INTEGER,
    name TEXT,
    count INTEGER,
    FOREIGN KEY(bin_id) REFERENCES bin
    FOREIGN KEY(prof_id) REFERENCES profile
    UNIQUE(name, bin_id, prof_id)
    )
    ''')

    return con, cur

def do_file(path: str, cur: sqlite3.Cursor) -> None:
    log.info(f'Processing file: {path}')
    with open(path, 'rb') as f:
        first_line = f.readline()
        data = json.loads(first_line)
        assert(data['name'])

        cur.execute('INSERT OR IGNORE INTO profile(name) VALUES(?)', (data['name'],))
        prof_id = cur.lastrowid

        for line in f:
            data = json.loads(line)
            cur.execute('INSERT OR IGNORE INTO bin(name) VALUES(?)', (data['path'],))
            bin_id = cur.lastrowid
            for k, v in data['counts'].items():
                sql = '''INSERT OR IGNORE INTO op_count(bin_id, prof_id, name, count)
                VALUES(?, ?, ?, ?)
                '''
                cur.execute(sql, (bin_id, prof_id, k, v))

@click.command()
def process() -> None:
    con, cur = prep_db()

    for i in os.listdir(const.DATA_DIR):
        if not i.endswith('.json_list'):
            continue
        path = f'{const.DATA_DIR}/{i}'
        do_file(path, cur)
        con.commit()

    cur.close()
    con.close()
