import socket
import io
import os
import subprocess
import re
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

INSTR_PATTERN: re.Pattern = re.compile('^[a-z]{2,}[a-z0-9]*$')


def get_real_path(base: str, file_path: str) -> str:
    if not os.path.islink(file_path):
        return file_path
    if file_path.startswith('.'):
        file_path = f'{base}/{os.readlink(file_path)}'

    file_path = os.path.realpath(file_path)
    base = os.path.dirname(file_path)
    return get_real_path(base, file_path)


def get_bins(base: str) -> List[str]:
    ret = []
    for i in os.listdir(base):
        file_path = f'{base}/{i}'
        original_file_path = file_path

        if not os.path.isfile(file_path):
            continue

        file_path = get_real_path(base, file_path)

        if not os.access(file_path, os.R_OK):
            continue

        mag = magic.from_file(file_path)
        if 'ELF' in mag or 'x86_64 executable' in mag:
            ret.append(original_file_path)

    return ret

def find_instr_position(binpath: str) -> int:
    with subprocess.Popen(['objdump','-d', binpath], stdout=subprocess.PIPE) as proc:
        stdout = proc.stdout
        assert stdout is not None

        instr_list = [ 'mov', 'jmp', 'push', 'pop', 'int', 'ret' ]
        for line in io.TextIOWrapper(stdout, encoding='utf-8', errors='ignore'):
            instr = None

            for i in instr_list:
                if i in line:
                    instr = i
                    break

            if instr is None:
                continue

            for i, token in enumerate(line.split('\t')):
                if token.startswith(instr):
                    return i

    raise Exception(f'Could not determine instruction location for {binpath}')

def get_instructions(binpath: str) -> BinData:
    with subprocess.Popen(['objdump','-d', binpath], stdout=subprocess.PIPE) as proc:
        ret = {}

        stdout = proc.stdout
        assert stdout is not None

        instr_pos = find_instr_position(binpath)

        for line in io.TextIOWrapper(stdout, encoding='utf-8', errors='ignore'):
            line_parts = line.split('\t')
            line_parts_len = len(line_parts)

            if line_parts_len >= 3:
                instr = line_parts[instr_pos]
                instr = instr.split(' ')[0]
                instr = instr.strip()

                if INSTR_PATTERN.match(instr) is None:
                    continue
                if instr not in ret:
                    ret[instr] = 1
                    continue
                ret[instr] = ret[instr] + 1
                continue

        return BinData(binpath, ret)

@click.command()
@click.option('-f', '--force-name', 'force_name', required=False)
def collect(force_name: str) -> None:
    name = make_name()
    if force_name:
        name = force_name
    assert name is not None

    output_file = f'{const.DATA_DIR}/{name}.json_list'

    log.info('Collecting data, writing to: %s', output_file)
    bins = get_bins('/usr/bin')
    bins.extend(get_bins('/usr/local/bin'))

    assert '/usr/bin/gcc' in bins

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

def make_name() -> str:
    hostname = socket.gethostname()
    if hostname == '':
        raise Exception('System hostname must not be empty string')
    if hostname == 'localhost':
        raise Exception("System hostname must not be localhost")

    # date = datetime.today().strftime('%Y-%m-%d')
    dist = distro.id()

    # full_name = f'{dist}.{hostname}.{name}.{date}.json_list'
    full_name = f'{dist}.{hostname}'
    return full_name
