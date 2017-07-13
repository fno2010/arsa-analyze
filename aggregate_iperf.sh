#!/bin/bash

N=$1
GAP=$2

rm -rf iperf.log
for i in $(seq 0 $N); do
    cat $i.log | sed '1,3d;s/-/ /g;/ID/q' | sed 'N;$d' \
        | awk '{print '$i'+2 " " $4+'$GAP'*'$i' " " $11}' >> iperf.log
done
