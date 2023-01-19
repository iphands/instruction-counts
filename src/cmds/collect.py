import socket
import io
import os
import subprocess
import json
import logging as log
import multiprocessing as mp
from typing import Dict, List
from dataclasses import dataclass

import click
import distro
import magic

import constants as const

@dataclass
class BinData:
    path: str
    counts: Dict[str, int]

def get_bins(base: str) -> List[str]:
    ret = []
    for i in os.listdir(base):
        file_path = f'{base}/{i}'

        if not os.path.isfile(file_path):
            continue
        if not os.access(file_path, os.R_OK):
            continue

        mag = magic.from_file(file_path)
        if 'ELF' in mag:
            ret.append(file_path)
            # print(file_path'{file_path}: {m}')
    return ret

def get_instructions(binpath: str) -> BinData:
    with subprocess.Popen(['objdump','-d', binpath], stdout=subprocess.PIPE) as proc:
        ret = {}

        stdout = proc.stdout
        assert stdout is not None

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
    assert name is not None

    output_file = f'{const.DATA_DIR}/{name}.json_list'

    log.info('Collecting data from /usr/bin, writing to: %s', output_file)
    bins = get_bins('/usr/bin')
    cpu_count = mp.cpu_count()
    threads = cpu_count
    if cpu_count > 4:
        threads = threads - 1

    with mp.Pool(threads) as pool:
        results = pool.imap_unordered(get_instructions, bins)

        if not os.path.exists(const.DATA_DIR):
            os.makedirs(const.DATA_DIR)

        with open(output_file, 'w', encoding='utf-8') as file_handle:
            json.dump({
                "name": name
            }, file_handle)
            file_handle.write('\n')

            for i in results:
                json.dump({
                    "path": i.path,
                    "counts": i.counts,
                }, file_handle)
                file_handle.write('\n')

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
