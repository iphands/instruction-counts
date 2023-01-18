import socket
import click
import distro
import io
import os
import magic
import subprocess
import sys
import json
import logging as log
import multiprocessing as mp

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

import constants as const

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

    stdout = proc.stdout
    assert(stdout is not None)

    for line in io.TextIOWrapper(stdout, encoding="utf-8"):
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

@click.command()
@click.option('-n', '--name', 'name', required=True)
def collect(name: str) -> None:
    name = make_name(name)
    assert(name is not None)

    output_file = f'{const.DATA_DIR}/{name}.json_list'

    log.info(f'Collecting data from /usr/bin, writing to: {output_file}')
    bins = get_bins('/usr/bin')
    cpu_count = mp.cpu_count()
    threads = cpu_count
    if cpu_count > 4:
        threads = threads - 1

    pool = mp.Pool(threads)
    results = pool.imap_unordered(get_instructions, bins)

    if not os.path.exists(const.DATA_DIR):
        os.makedirs(const.DATA_DIR)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "name": name
        }, f)
        f.write('\n')

        for i in results:
            s = json.dump({
                "path": i.path,
                "counts": i.counts,
            }, f)
            f.write('\n')

    pool.close()
    log.info('Collection complete')

def make_name(name: str) -> str:
    hostname = socket.gethostname()
    if hostname == '':
        raise Exception('System hostname must not be empty string')
    if hostname == 'localhost':
        raise Exception("System hostname must not be localhost")

    # date = datetime.today().strftime('%Y-%m-%d')
    dist = distro.id()

    # full_name = f'{dist}.{hostname}.{name}.{date}.json_list'
    full_name = f'{dist}.{hostname}.{name}'
    return full_name
