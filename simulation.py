#!/usr/bin/env python2.7

import sys
import argparse

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, OVSController
from mininet.link import TCLink
from mininet.cli import CLI

def create_bottleneck_link(net, n1, n2, config):
    return net.addLink(n1, n2,
                       bw=config.bw,
                       delay=config.delay,
                       max_queue_size=config.queue_size)

def create_access_link(net, n1, n2, config):
    return net.addLink(n1, n2,
                       bw=1000, # 1000 Mbps = 1 Gbps
                       delay="2us", # 2us
                       max_queue_size=10000) # sufficiently large queue size

SND_CMD = "iperf3 -c %s -i 0.1 -t %d -C %s> %d.log"

def eval_arsa(N, config):
    """
    Evaluate ARSA in the following topology:

        src0 --                -- dst0
               \              /
                s0 -------- s1
               /              \
        srcN --                -- dstN
    """

    net = Mininet(switch=OVSKernelSwitch, link=TCLink)
    ctl = net.addController("c1", controller=OVSController)

    # Configure the core switches

    core = [net.addSwitch("core%d" % i, protocol='OpenFlow13') for i in range(2)]
    create_bottleneck_link(net, core[0], core[1], config)

    # create hosts
    sources = [net.addHost('source%s' % i, ip='10.0.1.%d' % (i+1)) for i in range(N)]
    sinks = [net.addHost('sink%s' % i, ip='10.0.2.%d' % (i+1)) for i in range(N)]

    for host in sources:
        create_access_link(net, core[0], host, config)
    for host in sinks:
        create_access_link(net, core[1], host, config)

    net.build()

    ctl.start()
    for sw in core:
        sw.start([ctl])

    net.start()

    # configure hosts
    for sink in sinks:
        sink.cmd('iperf3 -s -D')

    for i in range(N):
        send_cmd = SND_CMD % ('10.0.2.%d' % (i+1), config.duration, config.tcp, i)
        sources[i].cmd('sleep %d && %s &' % (i * config.gap + 1, send_cmd))

    CLI(net)
    net.stop()

if __name__ == '__main__':
    cmdline = argparse.ArgumentParser(description='TCP Evaluation.')
    cmdline.add_argument('n_source', metavar='N', type=int,
                         help='The number of source/sink pairs.')
    cmdline.add_argument('--tcp', dest='tcp', action='store',
                         default="reno",
                         help='TCP version to be used (default: reno).')
    cmdline.add_argument('--duration', dest='duration', action='store',
                         default='100', type=int,
                         help='Duration of each transfer (default: 100 (s)))')
    cmdline.add_argument('--bw', dest='bw',
                         default='1', type=int,
                         help ='Bottleneck bandwidth (in Mbps, default: 1)')
    cmdline.add_argument('--delay', dest='delay',
                         default='20ms',
                         help ='Bottleneck link delay (default: 20ms)')
    cmdline.add_argument('--queue-size', dest='queue_size',
                         default='10', type=int,
                         help ='Bottleneck queue size (default: 10)')
    cmdline.add_argument('--gap', dest='gap',
                         default='10', type=int,
                         help ='Gap between two flows (default 10 (s))')

    config = cmdline.parse_args(sys.argv[1:])
    eval_arsa(config.n_source, config)
