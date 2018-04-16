#!/usr/bin/bash

N=$(python testgen.py)

echo $N > test-time.meta

python simprediction.py 32 $N | awk -F: -e '{}{print $3}{}' > test-time.log

#for i in $(seq 1 10)
#do
#    echo test-%i.log
#    python simprediction.py 32 $N | awk -F: -e '{}{print $3}{}' > time-%i.log
#done

python plottt.py
