#!/bin/sh

mkdir data

for k in $(seq 4 2 10); do
    for i in $(seq 10 20); do
        for j in $(seq 10); do
            python2.7 closgen.py $i $k \
                      "data/test$k-$i-$j.json" \
                      "data/test$k-$i-$j.matrix" \
                      "data/test$k-$i-$j.mnout"
        done
    done
done
