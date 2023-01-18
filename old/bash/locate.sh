#!/bin/bash
set -e
source ./env

add() {
  echo "$1" >> "$BIN_LIST"
}

do_linux() {
  for var in `find /usr/bin -type f`
  do
    file "$var" | grep -q 'ELF.*executable' && add "$var" || true
  done
}

do_darwin() {
  for var in `find /usr/bin -type f`
  do
    file "$var" | grep -qm1 'universal binary' && add "$var" || true
  done
}

rm "$BIN_LIST" || true
if [[ "$OSTYPE" == "darwin"* ]]
then
  do_darwin
  exit 0
fi

do_linux
