#!/usr/bin/env python2.7

SND_CMD = "iperf3 -c %s -i 1 -t %d -C %s -M %d -f k > %d.log"
MON_CMD = "tcpdump -i %s -w %s.pcap %s"

CLEAR_LINE = "\r\033[K"

# Color print in terminal
BLACK  = lambda s: "\033[0;30m%s\033[0m" % s
RED    = lambda s: "\033[0;31m%s\033[0m" % s
GREEN  = lambda s: "\033[0;32m%s\033[0m" % s
BLUE   = lambda s: "\033[0;34m%s\033[0m" % s
PURPLE = lambda s: "\033[0;35m%s\033[0m" % s
CYAN   = lambda s: "\033[0;36m%s\033[0m" % s
YELLOW = lambda s: "\033[1;33m%s\033[0m" % s
WHITE  = lambda s: "\033[1;37m%s\033[0m" % s
