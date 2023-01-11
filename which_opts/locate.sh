#!/bin/bash
set -e
source ./env

add() {
  echo "$1" >> "$BIN_LIST"
}

rm "$BIN_LIST" || true

for var in `find /usr/bin -type f`
do
  file "$var" | grep -q 'ELF.*executable' && add "$var" || true
done
