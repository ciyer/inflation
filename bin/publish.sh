#!/usr/bin/env bash

pushd .

SCRIPT_PATH=$(dirname `which $0`)
cd $SCRIPT_PATH/../qtm

jupyter nbconvert --to markdown --no-input QTM-Part1.ipynb --execute --output QTM-Part1.md
jupyter nbconvert --to markdown --no-input QTM-Part2.ipynb --execute --output QTM-Part2.md
jupyter nbconvert --to markdown --no-input QTM-Part3.ipynb --execute --output QTM-Part3.md

cd ..
mv qtm/*.md markdown/
mv qtm/*_files markdown/

popd
