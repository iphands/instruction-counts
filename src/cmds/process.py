import os
import logging as log
import sqlite3
import json

import click

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
    log.info('Processing file: %s', path)
    with open(path, 'rb') as file_handle:
        first_line = file_handle.readline()
        data = json.loads(first_line)
        assert data['name']

        cur.execute('INSERT OR IGNORE INTO profile(name) VALUES(?)', (data['name'],))
        cur.execute('SELECT * FROM profile WHERE name = ?', (data['name'],))
        prof_id = cur.fetchone()[0]

        for line in file_handle:
            data = json.loads(line)
            cur.execute('INSERT OR IGNORE INTO bin(name) VALUES(?)', (data['path'],))
            cur.execute('SELECT * FROM bin WHERE name = ?', (data['path'],))
            bin_id = cur.fetchone()[0]
            for k, val in data['counts'].items():
                sql = '''INSERT OR IGNORE INTO op_count(bin_id, prof_id, name, count)
                VALUES(?, ?, ?, ?)
                '''
                cur.execute(sql, (bin_id, prof_id, k, val))

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
