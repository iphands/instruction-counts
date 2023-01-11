#!/bin/bash
set -e
source ./env
cat $BIN_LIST | parallel --jobs 30 bash ./worker.sh
