import click
import io
import os
import magic
import subprocess
import sys
import json
import multiprocessing as mp
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class BinData:
    path: str
    counts: Dict[str, int]

def get_bins(base: str) -> List[str]:
    ret = []
    for i in os.listdir(base):
        f = f'{base}/{i}'

        if not os.path.isfile(f):
            continue
        if not os.access(f, os.R_OK):
            continue

        m = magic.from_file(f)
        if 'ELF' in m:
            ret.append(f)
            # print(f'{f}: {m}')
    return ret

def get_instructions(binpath: str) -> BinData:
    proc = subprocess.Popen(['objdump','-d', binpath], stdout=subprocess.PIPE)
    ret = {}
    for line in io.TextIOWrapper(proc.stdout, encoding="utf-8"):
        line_parts = line.split('\t')
        line_parts_len = len(line_parts)
        if line_parts_len == 3:
            instr = line_parts[2]
            instr = instr.split(' ')[0]
            instr = instr.strip()
            # if instr == '':
            #     print('WARNING:')
            #     print(line_parts)
            if instr not in ret:
                ret[instr] = 1
                continue
            ret[instr] = ret[instr] + 1
            continue
    return BinData(binpath, ret)

@click.group()
def cli():
    pass

@click.command()
@click.option('-n', '--name', 'name', required=True)
def collect(name: str) -> None:
    print('Collecting data from /usr/bin')
    bins = get_bins('/usr/bin')
    cpu_count = mp.cpu_count()
    threads = cpu_count
    if cpu_count > 4:
        threads = threads - 1

    pool = mp.Pool(threads)
    results = pool.imap_unordered(get_instructions, bins)

    with open(f'./raw_data/{name}.log', 'w', encoding='utf-8') as f:
        for i in results:
            json.dump({
                "path": i.path,
                "counts": i.counts,
            }, f)

    pool.close()

@click.command()
def process() -> None:
    pass

if __name__ == "__main__":
    cli.add_command(collect)
    cli.add_command(process)
    cli()
