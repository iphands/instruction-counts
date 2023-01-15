#!/bin/bash
set -e
source ./env
cat $BIN_LIST | parallel --jobs 4 bash ./worker.sh
