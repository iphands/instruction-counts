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
(venv) $ pip install -t requirements.txt
```

### Collect raw stats about bins in /usr/bin

```
(venv) $ python src/main.py collect --name gcc13
```

### Fetch mappings files, and (re)build the database

```
(venv) $ make reset_db
```

### Query data

```
(venv) $ python src/main.py query %/htop

fedora37.station-lan x86_64
  /usr/bin/htop
    mmx: 577
    sse: 407
    sse2: 1010
    total: 1994

clear-linux-os.noir x86_64
  /usr/bin/htop
    mmx: 1367
    sse: 2358
    sse2: 1420
    sse3: 12
    ssse3: 12
    sse4.1: 75
    total: 5244

gentoo.cosmo.gcc12 x86_64
  /usr/bin/htop
    mmx: 117
    avx: 928
    avx2: 11
    avx512: 679
    total: 1735
```
