# instruction-counts

## What is this

Some simple tooling that can be used to count the number of times various
instructions or instruction "families" occur in a compiled binary.

The original use-case was to count/verify how many SIMD instructions are present
in bins from various Linux distros, gcc versions, bins built with different
cflags.

## Setup

### Prep the python env

```
$ make venv/bin/activate
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

### Collect raw stats about bins in /usr/bin, /usr/local/bin

```
(venv) $ python src/main.py collect
```

### Fetch mappings files, and (re)build the database

```
(venv) $ make reset_db
```

## Usage

### Query data by package

```
(venv) $ python src/main.py query %/htop

clear-linux-os.noir x86_64
  /usr/bin/htop
    mmx: 1367
    sse: 2358
    sse2: 1420
    sse3: 12
    ssse3: 12
    sse4.1: 75
    total: 5244

fedora37.station-lan x86_64
  /usr/bin/htop
    mmx: 577
    sse: 407
    sse2: 1010
    total: 1994

darwin.air.lan x86_64
  /usr/local/bin/htop
    mmx: 6576
    sse: 278
    sse2: 482
    sse3: 16
    sse4.1: 14
    sse4.2: 2
    total: 7368

gentoo.cosmo.gcc12 x86_64
  /usr/bin/htop
    mmx: 117
    avx: 928
    avx2: 11
    avx512: 679
    total: 1735
```


### Query data with host filter

```
# Get all top from a host like gentoo%
$ python src/main.py query --host gentoo% %top%

gentoo.cosmo.gcc12 x86_64
  /usr/bin/slabtop
    mmx: 7
    avx: 38
    avx512: 79
    total: 124

gentoo.cosmo.gcc12 x86_64
  /usr/bin/top
    mmx: 16
    avx: 267
    avx2: 8
    avx512: 301
    total: 592
...

# Get all packages from a host like darwin%
$ python src/main.py query --host darwin% %

darwin.air.lan x86_64
  /usr/bin/grops
    mmx: 4243
    sse: 201
    sse2: 272
    sse3: 4
    ssse3: 1
    sse4.1: 12
    total: 4733

darwin.air.lan x86_64
  /usr/bin/pic
    mmx: 4931
    sse: 590
    sse2: 3406
    sse3: 36
    sse4.1: 7
    total: 8970

darwin.air.lan x86_64
  /usr/bin/troff
    mmx: 15001
    sse: 787
    sse2: 286
...
```

### Or use the database directly!

```
$ sqlite3 data/database.db '.tables'
bin       instr     op_count  profile

$ sqlite3 data/database.db '.schema instr'
CREATE TABLE instr(
    id INTEGER PRIMARY KEY,
    opcode TEXT NOT NULL UNIQUE,
    family TEXT,
    arch TEXT
    );

$ sqlite3 data/database.db 'SELECT DISTINCT(family) FROM instr'

sse2
sse
sse3
sse4.1
sse4.2
mmx
sse4a
avx512
mmx+
ssse3
3dnow!
3dnow!+
avx
avx2
```
