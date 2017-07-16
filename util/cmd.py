#!/usr/bin/env python2.7

SND_CMD = "iperf3 -c %s -i 0.1 -t %d -C %s -f k > %d.log"
MON_CMD = "tcpdump -i %s -w %s.pcap %s"

CLEAR_LINE = "\r\033[K"
