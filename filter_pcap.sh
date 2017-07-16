#!/bin/bash

PCAP_FILE=$1
N=$2

for i in $(seq 1 $N); do
    tshark -r raw.pcap \
           -Y "tcp.ack  and ip.addr == 10.0.1.$i" \
           -e tcp.nxtseq \
           -e frame.time_relative \
           -e tcp.srcport \
           -e tcp.dstport \
           -e tcp.ack \
           -e tcp.window_size \
           -e tcp.len \
           -T fields | sed 's/^/0/g;s/$/.0/g' \
        | awk '{ print $2" "$3" "$4" "$1" "$5" "$6" "$7}' > $i.log
    python2.7 read_pcap.py $i.log > $i.data
done
