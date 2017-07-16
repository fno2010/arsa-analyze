#!/usr/bin/env python2.7

import dpkt
import struct
import argparse
import socket

TSSND='tssnd'
TSRCV='tsrcv'

def parse_opts(tcp):
    options = {}
    for opt in dpkt.tcp.parse_opts(tcp.opts):
        field, value = opt
        if dpkt.tcp.TCP_OPT_TIMESTAMP == field:
            options[TSSND], options[TSRCV] = struct.unpack('>II', value)
    return options

class TcpAnalyzer(object):
    def __init__(self, src_ip, dst_ip, sport, dport, first_seen):
        self.src_ip, self.dst_ip = src_ip, dst_ip
        self.sport, self.dport = sport, dport
        self.segments = {}
        self.timeseries = {}
        self.time_diff = 0
        self.last_ts = first_seen
        self.inflight = 0
        self.acknowledged = 0

    def send(self, ts, tcp):
        opts = parse_opts(tcp)
        datalen = len(tcp.data)
        key = (tcp.seq + datalen, opts['tsval']) if 'tsval' in opts else (tcp.seq + datalen, -1)
        self.segments[key] = {
            'send_time': float(ts),
            'data_size': datalen,
            'ack_time': 1e10
        }
        self.inflight += datalen

    def recv(self, ts, tcp):
        opts = parse_opts(tcp)
        key = (tcp.ack, opts['tsecr']) if 'tsecr' in opts else (tcp.ack, -1)
        if key not in self.segments:
            return
        self.segments[key]['ack_time'] = float(ts)
        rtt = ts - self.segments[key]['send_time']
        snd_throughput = self.inflight / (ts - self.last_ts)
        self.inflight = 0
        self.last_ts = ts
        # the throughput can be calculated as the acknowledged data
        self.timeseries[ts] = (ts, rtt, snd_throughput)

    def process(self, ts, tcp, ack):
        if ack:
            self.recv(ts, tcp)
        else:
            self.send(ts, tcp)

    def size(self):
        return len(self.segments)

    def time_series(self):
        return self.timeseries

def analyze_tcp(f, src_ip, dst_ip):
    pcap = dpkt.pcap.Reader(f)
    conn = {}
    for ts, packet in pcap:
        eth = dpkt.ethernet.Ethernet(packet)
        ip = eth.data
        tcp = ip.data

        if not isinstance(ip, dpkt.ip.IP):
            continue

        if not isinstance(tcp, dpkt.tcp.TCP):
            continue

        saddr = socket.inet_ntoa(ip.src)
        daddr = socket.inet_ntoa(ip.dst)
        if saddr == src_ip and daddr == dst_ip:
            tuple4, ack = (src_ip, dst_ip, tcp.sport, tcp.dport), False
        elif daddr == src_ip and saddr == dst_ip:
            tuple4, ack = (src_ip, dst_ip, tcp.dport, tcp.sport), True
        else:
            continue

        if tuple4 not in conn:
            if ack:
                continue
            conn[tuple4] = TcpAnalyzer(src_ip, dst_ip, tcp.sport, tcp.dport, ts)

        conn[tuple4].process(ts, tcp, ack)

    dataflow = reduce(lambda x,y: x if x.size() > y.size() else y, conn.values())
    timeseries = sorted(dataflow.time_series().values(), key=lambda x: float(x[0]))
    for ts, rtt, snd in timeseries:
        print ts, rtt, snd

def config_cmdline():
    cmdline = argparse.ArgumentParser(description='TCP Metric Analysis')
    cmdline.add_argument('pcap_file',
                         help='The pcap file to be analyzed')
    cmdline.add_argument('src_ip',
                         help='The source IP address of the TCP flow')
    cmdline.add_argument('dst_ip',
                         help='The destination IP address of the TCP flow')
    return cmdline

if __name__ == '__main__':
    import sys

    cmdline = config_cmdline()
    config = cmdline.parse_args(sys.argv[1:])

    with open(config.pcap_file) as f:
        analyze_tcp(f, config.src_ip, config.dst_ip)
