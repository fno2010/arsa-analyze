#!/usr/bin/env python2.7

from __future__ import print_function
import sys, json, os, re
from util.arsaconf import parse_argument

ns2file = 'clos.tcl'

def configure_node(sw, f):
    print('set %s [$ns node]' % sw, file=f)

def configure_core_link(sw1, sw2, config, f, bw=None, delay=None):
    bw = bw or '1000Mb'
    delay = delay or '5us'
    print('$ns duplex-link $%s $%s %s %s DropTail'
          % (sw1, sw2, bw, delay), file=f)

def configure_bottleneck_link(sw1, sw2, config, f, bw=None, delay=None):
    bw = bw or '%dMb' % config.bw
    delay = delay or config.delay
    print('$ns duplex-link $%s $%s %s %s DropTail'
          % (sw1, sw2, bw, delay), file=f)

def configure_tcp(idx, src, dst, tcp, config, f):
    # set up tcp connection
    print('set s%d [new Agent/TCP/%s]' % (idx, tcp.capitalize()), file=f)
    print('set d%d [new Agent/TCPSink]' % (idx), file=f)
    print('$ns attach-agent $%s $s%d' % (src, idx), file=f)
    print('$ns attach-agent $%s $d%d' % (dst, idx), file=f)
    print('$ns connect $s%d $d%d' % (idx, idx), file=f)
    print('$s%d set fid_ %d' % (idx, idx), file=f)

    # set up FTP
    print('set f%d [new Application/FTP]' % (idx), file=f)
    print('$f%d attach-agent $s%d' % (idx, idx), file=f)
    print('$f%d set type_ FTP' % (idx), file=f)
    print('$ns at 1.0 \"$f%d start\"' % (idx), file=f)
    print('$ns at %.2f \"$f%d stop\"' % (config.duration + 1, idx), file=f)

    # set up monitor app
    print('set t%d [new TraceApp]' % (idx), file=f)
    print('$t%d attach-agent $d%d' % (idx, idx), file=f)
    print('$ns at 0.0 \"$t%d start\"' % (idx), file=f)
    print('$ns at 0.0 \"plotThroughput %d $t%d $trace_file\"' %(idx, idx), file=f)

def configure_ns2(trace_file, config, f):
    print('set trace_file [open \"arsa/%s\" w]' % (trace_file), file=f)
    print('$ns at %.2f \"finish\"' % (config.duration + 10), file=f)

def generate_ns2(K, flows, config, trace_file, f):
    configure_ns2(trace_file, config, f)
    # create nodes
    K2 = K / 2

    # nodes
    core = {(i, j): 'core%d%d' % (i, j) for i in range(K2) for j in range(K2)}
    aggr = {(i, j): 'aggr%d%d' % (i, j) for i in range(K) for j in range(K2)}
    edge = {(i, j): 'edge%d%d' % (i, j) for i in range(K) for j in range(K2)}
    host = {(i, j, k): 'host%d%d%d' % (i, j, k)
            for i in range(K) for j in range(K2) for k in range(K2)}

    for sid in core:
        configure_node(core[sid], f)
    for sid in aggr:
        configure_node(aggr[sid], f)
    for sid in edge:
        configure_node(edge[sid], f)
    for hid in host:
        configure_node(host[hid], f)

    # links
    core2aggr = [(core[(i, j)], aggr[(k, i)])
                 for i in range(K2) for j in range(K2) for k in range(K)]
    aggr2edge = [(aggr[(i, j)], edge[(i, k)])
                 for i in range(K) for j in range(K2) for k in range(K2)]
    edge2host = [(edge[(i, j)], host[(i, j, k)])
                 for i in range(K) for j in range(K2) for k in range(K2)]

    for c, a in core2aggr:
        configure_core_link(c, a, config, f)
    for a, e in aggr2edge:
        configure_core_link(a, e, config, f)
    for e, h in edge2host:
        configure_bottleneck_link(e, h, config, f)

    # tcp connections
    for i in range(len(flows)):
        flow = flows[i]
        si, sj, sk = flow['from']
        di, dj, dk = flow['to']
        src, dst, tcp = host[(si, sj, sk)], host[(di, dj, dk)], flow['tcp']
        configure_tcp(i, src, dst, tcp, config, f)

def execute_ns2(trace_file, thpt_file):
    cmd = ['docker', 'run', '--rm', '-it', '-v', '$PWD:/ns2/ns-2.35/arsa',
           'ekiourk/ns2:latest', 'ns', 'arsa/ns2arsa.tcl']
    os.system(' '.join(cmd))
    throughputs = []
    with open(trace_file, 'r') as f:
        for l in f.readlines():
            m = re.search('(\d+) 22 (.+)', l)
            if m is None:
                continue
            throughputs += [float(m.group(2))]

    with open(thpt_file, 'w') as f:
        for bw in throughputs:
            print(bw, file=f)
    return throughputs

if __name__ == '__main__':
    cmd = parse_argument()

    K, flow_file, trace_file, thpt_file = sys.argv[1:5]
    K = int(K)
    config = cmd.parse_args(sys.argv[5:])

    with open(flow_file, 'r') as f:
        flows = json.load(f)

    with open(ns2file, 'w') as f:
        generate_ns2(K, flows, config, trace_file, f)

    execute_ns2(trace_file, thpt_file)
