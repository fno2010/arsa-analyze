#!/usr/bin/env python2.7

import dpkt

def tcp_timeseries(filename):
    f = open(filename)
    pcap = dpkt.pcap.Reader(f)

    for ts, buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)
        ip = eth.data
        tcp = ip.data

        try:
            print ts, len(tcp.data)
        except Exception:
            pass

    f.close()

if __name__ == '__main__':
    import sys

    tcp_timeseries(sys.argv[1])
