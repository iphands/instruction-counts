import bz2
import gzip
import lzma
import shutil
import subprocess
import unittest

from cmds.kernel import extract_vmlinux

FAKE_ELF = b'\x7fELF' + bytes(range(256)) * 64

class TestKernel(unittest.TestCase):
    def test_plain_elf_passthrough(self) -> None:
        self.assertEqual(FAKE_ELF, extract_vmlinux(FAKE_ELF))

    def test_gzip_with_false_positive_and_trailing_data(self) -> None:
        # 'BZh' and a gzip header-looking blob before the real payload,
        # and trailing bytes after it (bzImage appends size + relocs)
        image = b'boot stub BZh junk \x1f\x8b\x08 not gzip' + gzip.compress(FAKE_ELF) + b'\x00' * 32
        self.assertEqual(FAKE_ELF, extract_vmlinux(image))

    def test_xz(self) -> None:
        image = b'stub' + lzma.compress(FAKE_ELF, format=lzma.FORMAT_XZ) + b'tail'
        self.assertEqual(FAKE_ELF, extract_vmlinux(image))

    def test_lzma_alone(self) -> None:
        # the kernel uses a large dictionary; the magic we scan for assumes the
        # low 3 bytes of the dict size are zero (multiple of 16 MiB)
        filters = [{'id': lzma.FILTER_LZMA1, 'dict_size': 16 << 20}]
        image = b'stub' + lzma.compress(FAKE_ELF, format=lzma.FORMAT_ALONE, filters=filters) + b'tail'
        self.assertEqual(FAKE_ELF, extract_vmlinux(image))

    def test_bzip2(self) -> None:
        image = b'stub' + bz2.compress(FAKE_ELF) + b'tail'
        self.assertEqual(FAKE_ELF, extract_vmlinux(image))

    @unittest.skipIf(shutil.which('zstd') is None, 'zstd not installed')
    def test_zstd(self) -> None:
        payload = subprocess.run(['zstd', '-c'], input=FAKE_ELF, stdout=subprocess.PIPE, check=True).stdout
        image = b'stub' + payload + b'tail'
        self.assertEqual(FAKE_ELF, extract_vmlinux(image))

    def test_no_payload(self) -> None:
        with self.assertRaises(ValueError):
            extract_vmlinux(b'nothing to see here')

if __name__ == '__main__':
    unittest.main()
