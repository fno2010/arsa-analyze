#!/usr/bin/env python2.7

import os

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, OVSController
from mininet.link import TCLink
from mininet.log import info
from mininet.cli import CLI

from util.link import create_access_link, create_bottleneck_link
from util.cmd import SND_CMD

def single_bottleneck_link(N, config):
    """
    Evaluate ARSA in the following topology:

        src0 --                -- dst0
          .    \              /    .
          .     s0 -------- s1     .
          .    /              \    .
        srcN --                -- dstN
    """

    net = Mininet(switch=OVSKernelSwitch, link=TCLink)
    net.addController("c1", controller=OVSController)

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

    net.start()

    # configure hosts
    for sink in sinks:
        sink.cmd('iperf3 -s -D')

    info('Collecting data...\n')
    info('Please wait for %d s\n' % (config.duration + (N - 1) * config.gap))

    for i in range(N):
        send_cmd = SND_CMD % ('10.0.2.%d' % (i+1), config.duration, config.tcp, i)
        sources[i].cmd('sleep %d && %s &' % (i * config.gap + 1, send_cmd))

    CLI(net)
    info('Stoping all iperf3 tasks...\n')
    os.system('pkill "iperf3*"')
    info('Exiting mininet...\n')
    net.stop()

def simple_linear(N, config):
    """
    Evaluate ARSA in the following linear topo:

         - - - - - - - - - - - - - - - -
        |              fn               |
         - h1 - - ->h2 - - ->h3 ... hn<-
           |   f1   |   f2   |      |
           |        |        |      |
           s1-------s2-------s3 ... sn
    """
    net = Mininet(switch=OVSKernelSwitch, link=TCLink)
    net.addController("c1", controller=OVSController)

    # configure switches
    switch = [net.addSwitch("s%d" % i, protocol='OpenFlow13') for i in range(N)]
    for i in range(N - 1):
        create_bottleneck_link(net, switch[i], switch[i + 1], config)

    # create hosts
    host = [net.addHost('h%s' % i, ip='10.0.1.%d' % (i+1)) for i in range(N)]

    for i in range(N):
        create_access_link(net, switch[i], host[i], config)

    net.build()
    net.start()

    # configure hosts
    info('Collecting data...\n')
    info('Please wait for %d s\n' % (config.duration + 1))

    for i in range(N):
        x, y = i, (i + 1) % N
        x, y = min(x, y), max(x, y)
        # a hack to enable multiple iperf3 connections
        port = 5201 + i
        host[y].cmd('iperf3 -s -p %s -D' % (port))
        send_cmd = SND_CMD % ('10.0.1.%d -p %d' % (y+1, port), config.duration, config.tcp, i)
        host[x].cmd('sleep %d && %s &' % (1, send_cmd))

    CLI(net)
    info('Stoping all iperf3 tasks...\n')
    os.system('pkill "iperf3*"')
    info('Exiting mininet...\n')
    net.stop()
