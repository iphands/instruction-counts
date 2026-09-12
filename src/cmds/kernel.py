"""Collect instruction counts for the Linux kernel images in /boot.

A bzImage (vmlinuz) is a small real-mode boot stub followed by a compressed
vmlinux ELF. The compressed payload is not at a fixed offset, so like the
kernel's own scripts/extract-vmlinux we scan for the magic bytes of each
supported compressor and try to decompress from every hit until one yields an
ELF. Uncompressed vmlinux files in /boot are used as-is.
"""
import bz2
import glob
import logging as log
import lzma
import multiprocessing as mp
import os
import shutil
import subprocess
import tempfile
import zlib
from dataclasses import dataclass
from typing import Callable, List, Optional

import click

import constants as const
from cmds.collect import BinData, get_instructions, make_name, pool_size, write_json_list
from cmds import process as proc_cmd

ELF_MAGIC: bytes = b'\x7fELF'
KERNEL_GLOB: str = '/boot/vmlinu*'

def _gzip(data: bytes) -> bytes:
    return zlib.decompressobj(wbits=zlib.MAX_WBITS | 16).decompress(data)

def _xz(data: bytes) -> bytes:
    return lzma.LZMADecompressor(format=lzma.FORMAT_XZ).decompress(data)

def _lzma(data: bytes) -> bytes:
    return lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(data)

def _bzip2(data: bytes) -> bytes:
    return bz2.BZ2Decompressor().decompress(data)

def _external(tool: str, args: List[str]) -> Callable[[bytes], bytes]:
    def run(data: bytes) -> bytes:
        if shutil.which(tool) is None:
            raise FileNotFoundError(f'{tool} not found in PATH')
        # The payload is followed by trailing data (size append, relocs) so the
        # tool usually exits non-zero after the first stream. Ignore that and
        # validate the output instead.
        result = subprocess.run([tool] + args, input=data, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=False)
        return result.stdout
    return run

@dataclass
class Codec:
    name: str
    magic: bytes
    decompress: Callable[[bytes], bytes]

CODECS: List[Codec] = [
    Codec('zstd',  b'\x28\xb5\x2f\xfd', _external('zstd', ['-dc'])),
    Codec('gzip',  b'\x1f\x8b\x08', _gzip),
    Codec('xz',    b'\xfd7zXZ\x00', _xz),
    Codec('bzip2', b'BZh', _bzip2),
    Codec('lzma',  b'\x5d\x00\x00\x00', _lzma),
    Codec('lzo',   b'\x89LZO\x00', _external('lzop', ['-dc'])),
    Codec('lz4',   b'\x02\x21\x4c\x18', _external('lz4', ['-d'])),
]

def is_elf(data: bytes) -> bool:
    return data.startswith(ELF_MAGIC)

def extract_vmlinux(image: bytes) -> bytes:
    """Return the ELF vmlinux embedded in a kernel image, or the image itself
    if it is already an ELF. Raises ValueError if nothing usable is found."""
    if is_elf(image):
        return image

    for codec in CODECS:
        pos = image.find(codec.magic)
        while pos >= 0:
            try:
                out = codec.decompress(image[pos:])
                if is_elf(out):
                    log.debug('Found %s payload at offset %d', codec.name, pos)
                    return out
            except FileNotFoundError as err:
                log.warning('Skipping %s: %s', codec.name, err)
                break
            except (OSError, EOFError, ValueError, lzma.LZMAError, zlib.error):
                pass
            pos = image.find(codec.magic, pos + 1)

    raise ValueError('No supported compressed ELF payload found')

def get_kernels(pattern: str = KERNEL_GLOB) -> List[str]:
    ret = []
    for path in sorted(glob.glob(pattern)):
        if not os.path.isfile(path):
            continue
        if not os.access(path, os.R_OK):
            log.warning('Skipping unreadable kernel: %s', path)
            continue
        ret.append(path)
    return ret

def collect_kernel(path: str) -> Optional[BinData]:
    log.info('Extracting %s', path)
    try:
        with open(path, 'rb') as file_handle:
            vmlinux = extract_vmlinux(file_handle.read())
    except ValueError as err:
        log.error('%s: %s', path, err)
        return None

    with tempfile.NamedTemporaryFile(prefix='vmlinux.', suffix='.elf') as tmp:
        tmp.write(vmlinux)
        tmp.flush()
        del vmlinux
        log.info('Counting instructions in %s', path)
        return get_instructions(tmp.name, name=path)

@click.command('collect-kernels')
@click.option('-f', '--force-name', 'force_name', required=False)
@click.option('-p', '--pattern', 'pattern', default=KERNEL_GLOB, show_default=True,
              help='Glob of kernel images to collect')
def collect_kernels(force_name: str, pattern: str) -> None:
    name = make_name()
    if force_name:
        name = force_name
    assert name is not None

    output_file = f'{const.DATA_DIR}/{name}.kernels.json_list'
    kernels = get_kernels(pattern)
    if not kernels:
        raise click.ClickException(f'No readable kernel images match {pattern}')

    log.info('Collecting %d kernel(s), writing to: %s', len(kernels), output_file)
    with mp.Pool(min(pool_size(), len(kernels))) as pool:
        results = pool.imap_unordered(collect_kernel, kernels)
        write_json_list(output_file, name, (r for r in results if r is not None))

    log.info('Loading %s into %s', output_file, const.DATABASE)
    con, cur = proc_cmd.prep_db()
    proc_cmd.do_file(output_file, cur)
    con.commit()
    cur.close()
    con.close()
    log.info('Kernel collection complete')
