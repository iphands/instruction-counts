import sqlite3
import json
import re
from dataclasses import dataclass
from typing import Tuple, Union

import click

import constants as const

NUM_RE = re.compile(r'(\d+)')

@dataclass
class Options():
    host: str
    package: str
    form: str

@click.command()
@click.argument('query_str')
@click.option('-f', '--format', 'form')
@click.option('-h', '--host', 'host')
def query(query_str: str, host: str, form: str) -> None:
    con = sqlite3.connect(const.DATABASE)
    cur = con.cursor()
    opts = Options(host=host, package=query_str, form=form)
    package(cur, opts)
    cur.close()
    con.close()

def natural_key(text: str) -> Tuple[Tuple[int, Union[int, str]], ...]:
    """Split a name into text/number chunks so 6.19.12 sorts after 6.19.6."""
    return tuple(
        (1, int(part)) if part.isdigit() else (0, part)
        for part in NUM_RE.split(text) if part != ''
    )

def sort_output(output_dict: dict) -> dict:
    """Group by profile (A-Z), newest binary first within each profile."""
    rows = sorted(output_dict.items(),
                  key=lambda kv: natural_key(kv[1]["bin"]), reverse=True)
    rows.sort(key=lambda kv: natural_key(kv[1]["profile"]))
    return dict(rows)

def package(cur: sqlite3.Cursor, opts: Options) -> None:
    host_predicate = ""
    values = (opts.package,)
    if opts.host:
        host_predicate = "AND profile.name LIKE ?"
        values = (opts.package, opts.host)

    sql = f"""
    SELECT DISTINCT profile.name, bin.name, op_count.name, instr.family, instr.arch, op_count.count
    FROM bin
    INNER JOIN op_count ON bin.id = op_count.bin_id
    INNER JOIN profile ON op_count.prof_id = profile.id
    INNER JOIN instr ON op_count.name = instr.opcode AND (op_count.mod = instr.family OR (op_count.mod = '' AND instr.family != 'avx512'))
    WHERE bin.name LIKE ?
    AND instr.family != ''
    {host_predicate}
    """

    output_dict = {}

    for row in cur.execute(sql, values):
        prof, binp, opcode, family, arch, count = row
        key = f'{prof} {binp}'
        if key not in output_dict:
            output_dict[key] = {
                "profile": prof,
                "bin": binp,
                "arch": arch,
                "instructions": []
            }

        output_dict[key]["instructions"].append({
            "opcode": opcode,
            "family": family,
            "count": count,
        })

    cur.close()

    output_dict = sort_output(output_dict)

    if opts.form == 'json':
        print(json.dumps(output_dict))
        return


    for _k, val in output_dict.items():
        print()
        print(f'''{val["profile"]} {val["arch"]}
  {val["bin"]}''')
        family_counts = {}
        for i in val["instructions"]:
            if i['family'] == '':
                continue

            if i['family'] not in family_counts:
                family_counts[i['family']] = i['count']
                continue

            family_counts[i['family']] += i['count']

        total = 0
        for i in const.FAMILY_ALLOW:
            if i not in family_counts:
                continue
            print(f'    {i}: {family_counts[i]}')
            total += family_counts[i]
        print(f'    total: {total}')
