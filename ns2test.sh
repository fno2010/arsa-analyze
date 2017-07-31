#!/bin/bash

for i in `seq 1 10`; do
    mkdir -p data/query$i
    ./datagen.py 10 4 data/query$i/ 5 5 0
done
