import click
import sqlite3
import json

import constants as const

@click.command()
@click.argument('q')
@click.option('-f', '--format', 'form')
def query(q: str, form: str) -> None:
    con = sqlite3.connect(const.DATABASE)
    cur = con.cursor()

    # SELECT profile.name, bin.name, op_count.name, op_count.count
    sql = """
    SELECT DISTINCT profile.name, bin.name, op_count.name, instr.family, instr.arch, op_count.count
    FROM bin
    INNER JOIN op_count ON bin.id = op_count.bin_id
    INNER JOIN profile ON op_count.prof_id = profile.id
    INNER JOIN instr ON op_count.name = instr.opcode
    WHERE bin.name LIKE ?
    AND instr.family != ''
    """

    output_dict = {}

    for row in cur.execute(sql, (q,)):
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
    con.close()

    if form == 'json':
        print(json.dumps(output_dict))
        return


    for k, v in output_dict.items():
        print()
        print(f'''{v["profile"]} {v["arch"]}
  {v["bin"]}''')
        family_counts = {}
        for i in v["instructions"]:
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
