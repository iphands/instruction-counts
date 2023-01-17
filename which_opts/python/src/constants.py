from typing import List

DATA_DIR: str = './data'
DATABASE: str = f'{DATA_DIR}/database.db'
X86_REF_PATH: str = f'{DATA_DIR}/ref/x86_64.json'
REFS: List[str] = [X86_REF_PATH]
FAMILY_ALLOW = [
    'mmx',
    'mmx+',
    '3dnow!',
    '3dnow!+',
    'sse',
    'sse2',
    'sse3',
    'ssse3',
    'sse4',
    'sse4a',
    'sse4.1',
    'sse4.2',
    'avx',
    'avx2',
    'avx512',
]
