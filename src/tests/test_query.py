import unittest

from cmds.query import sort_output

def make_entry(prof: str, binp: str) -> dict:
    return {"profile": prof, "bin": binp, "arch": "x86_64", "instructions": []}

def make_dict(*pairs: tuple) -> dict:
    return {f'{p} {b}': make_entry(p, b) for p, b in pairs}

class TestQuerySort(unittest.TestCase):
    def test_newest_version_first(self) -> None:
        out = sort_output(make_dict(
            ('gentoo.cosmo', '/boot/vmlinuz-linux-6.19.6-gentoo.026'),
            ('gentoo.cosmo', '/boot/vmlinuz-linux-7.2.3-gentoo.027'),
            ('gentoo.cosmo', '/boot/vmlinuz-linux-6.19.12-gentoo.027'),
            ('gentoo.cosmo', '/boot/vmlinuz-linux-7.2.3-gentoo.028'),
        ))
        self.assertEqual([
            '/boot/vmlinuz-linux-7.2.3-gentoo.028',
            '/boot/vmlinuz-linux-7.2.3-gentoo.027',
            '/boot/vmlinuz-linux-6.19.12-gentoo.027',
            '/boot/vmlinuz-linux-6.19.6-gentoo.026',
        ], [v["bin"] for v in out.values()])

    def test_profiles_stay_grouped_and_ascending(self) -> None:
        out = sort_output(make_dict(
            ('gentoo.cosmo', '/usr/bin/ls'),
            ('darwin.air.lan', '/usr/bin/ls'),
            ('gentoo.cosmo', '/usr/bin/cat'),
            ('darwin.air.lan', '/usr/bin/cat'),
        ))
        self.assertEqual([
            ('darwin.air.lan', '/usr/bin/ls'),
            ('darwin.air.lan', '/usr/bin/cat'),
            ('gentoo.cosmo', '/usr/bin/ls'),
            ('gentoo.cosmo', '/usr/bin/cat'),
        ], [(v["profile"], v["bin"]) for v in out.values()])
