import unittest
from cmds.collect import avx_reg_check

class TestCollect(unittest.TestCase):
    def test_avx_reg_check(self) -> None:
        line = '    5f81:       62 b2 6d 28 3d d2       vpmaxsd %zmm,%ymm2,%ymm2'
        self.assertTrue(avx_reg_check(line))

        line = '    5f81:       62 b2 6d 28 3d d2       vpmaxsd %ymm18,%ymm2,%ymm2'
        self.assertTrue(avx_reg_check(line))

        line = '    5f81:       62 b2 6d 28 3d d2       vpmaxsd %xmm32,%ymm2,%ymm2'
        self.assertTrue(avx_reg_check(line))

        line = '    5f81:       62 b2 6d 28 3d d2       vpmaxsd %xmm3,%ymm2,%ymm2'
        self.assertFalse(avx_reg_check(line))

if __name__ == '__main__':
    unittest.main()
