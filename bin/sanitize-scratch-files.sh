#!/bin/bash
set -e

# Automatically removes any temporary root .py files matching test_*.py, tmp_*.py, scratch_*.py,
# as well as *_scratch.py, *_test.py, *_tmp.py, *_debug.py and files in tmp/ and scratch/

find . -maxdepth 1 -type f \( -name "test_*.py" -o -name "tmp_*.py" -o -name "scratch_*.py" -o -name "*_scratch.py" -o -name "*_test.py" -o -name "*_tmp.py" -o -name "*_debug.py" \) -delete

if [ -d "tmp" ]; then
    rm -rf tmp/*
fi

if [ -d "scratch" ]; then
    rm -rf scratch/*
fi
