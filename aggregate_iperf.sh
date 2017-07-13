#!/bin/bash

N=$1
GAP=$2
CAPTURE=$3 # 7 - throughput, 10 - cwnd
OUTPUT=$4

rm -rf $OUTPUT
for i in $(seq 0 $N); do
    cat $i.log | sed '1,3d;s/-/ /g;s/\[//g;s/\]//g;/ID/q' | sed 'N;$d' \
        | awk '{print '$i'+2 " " $3+'$GAP'*'$i' " " $'$CAPTURE'}' >> $OUTPUT
done
