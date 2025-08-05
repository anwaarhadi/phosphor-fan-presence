#!/usr/bin/env bash
for file in ./test_cases/*; do
    FILENAME=$(basename $file)
    ./groups_expand.py -f $file -o "./test_output/${FILENAME%.*}_output.json"
done