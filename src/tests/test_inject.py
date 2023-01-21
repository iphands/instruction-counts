import unittest
import json
import os
from cmds.ingest import get_isas

class TestIngest(unittest.TestCase):
    def test_finds_avx_isas(self) -> None:
        test_data = os.path.join(os.path.dirname(__file__), 'testdata', 'instr.json')
        with open(test_data, 'r', encoding='utf-8') as instr_file:
            instr = json.load(instr_file)
            self.assertEqual(['avx', 'avx512'], sorted(get_isas(instr['forms'])))

    def test_handles_no_isa(self) -> None:
        test_data = os.path.join(os.path.dirname(__file__), 'testdata', 'instr-mov.json')
        with open(test_data, 'r', encoding='utf-8') as instr_file:
            instr = json.load(instr_file)
            self.assertEqual([''], sorted(get_isas(instr['forms'])))

if __name__ == '__main__':
    unittest.main()
