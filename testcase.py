#!/usr/bin/env python2.7

import json

from mininet.log import info

from util.link import create_access_link, create_bottleneck_link
from util.cmd import SND_CMD, MON_CMD
from util.case import Case

class SingleBottleneckLinkTest(Case):
    """
    Evaluate ARSA in the following topology:

        src0 --                -- dst0
          .    \              /    .
          .     s0 -------- s1     .
          .    /              \    .
        srcN --                -- dstN
    """

    def __init__(self, N, config):
        self.N = N
        self.config = config
        Case.__init__(self)

    def create_nodes(self):
        self.core = [self.net.addSwitch("core%d" % i, protocol='OpenFlow13')
                     for i in range(2)]
        self.sources = [self.net.addHost('source%s' % i, ip='10.0.1.%d' % (i+1))
                        for i in range(self.N)]
        self.sinks = [self.net.addHost('sink%s' % i, ip='10.0.2.%d' % (i+1))
                      for i in range(self.N)]

    def config_nodes(self):
        create_bottleneck_link(self.net, self.core[0], self.core[1], self.config)
        for host in self.sources:
            create_access_link(self.net, self.core[0], host, self.config)
        for host in self.sinks:
            create_access_link(self.net, self.core[1], host, self.config)

        Case.config_nodes(self)

    def test(self):
        for sink in self.sinks:
            sink.cmd('iperf3 -s -D')

        info('Collecting data...\n')
        self.waiting_time = self.config.duration + 2

        for i in range(self.N):
            send_cmd = SND_CMD % ('10.0.2.%d' % (i+1), self.config.duration,
                                  self.config.tcp, self.config.mss, i)
            self.sources[i].cmd('sleep %d && %s &' % (i * self.config.gap + 1, send_cmd))

        Case.test(self)


class SimpleLinearTest(Case):
    """
    Evaluate ARSA in the following linear topo:

         - - - - - - - - - - - - - - - -
        |              fn               |
         - h1 - - ->h2 - - ->h3 ... hn<-
           |   f1   |   f2   |      |
           |        |        |      |
           s1-------s2-------s3 ... sn
    """

    def __init__(self, N, config):
        self.N = N
        self.config = config
        Case.__init__(self)

    def create_nodes(self):
        self.switch = [self.net.addSwitch("s%d" % i, protocol='OpenFlow13')
                       for i in range(self.N)]
        self.host = [self.net.addHost('h%s' % i, ip='10.0.1.%d' % (i+1))
                     for i in range(self.N)]
        self.extra_host = [self.net.addHost('extra%d' % i, ip='10.0.2.%d' % (i+1))
                           for i in range(2)]

    def config_nodes(self):
        for i in range(self.N - 1):
            create_bottleneck_link(self.net, self.switch[i], self.switch[i + 1],
                                   self.config)
        for i in range(self.N):
            create_access_link(self.net, self.switch[i], self.host[i],
                               self.config)
        for i in range(2):
            create_access_link(self.net, self.switch[i * (self.N-1)],
                               self.extra_host[i], self.config)

        Case.config_nodes(self)

    def test(self):
        info('Collecting data...\n')
        self.waiting_time = self.config.duration + 2

        for i in range(self.N-1):
            mon_cmd = MON_CMD % ('h%s-eth0' % i, 'h%s' % i, '')
            self.host[i].cmd('sleep %d && %s &' % (1, mon_cmd))
            self.host[i+1].cmd('iperf3 -s -D')
            send_cmd = SND_CMD % ('10.0.1.%d' % (i+2), self.config.duration,
                                  self.config.tcp, self.config.mss, i)
            self.host[i].cmd('sleep %d && %s &' % (2, send_cmd))

        for i in range(1):
            mon_cmd = MON_CMD % ('extra%s-eth0' % i, 'e%s' % (i), '')
            self.extra_host[i].cmd('sleep %d && %s &' % (1, mon_cmd))
            self.extra_host[i+1].cmd('iperf3 -s -D')
            send_cmd = SND_CMD % ('10.0.2.%d' % (i+2), self.config.duration,
                                  self.config.tcp, self.config.mss, i + self.N -1)
            self.extra_host[i].cmd('sleep %d && %s &' % (2, send_cmd))

        Case.test(self)


class SingleLinkMixTCPTest(Case):
    """
    Evaluate bandwidth allocation of mixed TCP flows in a single bottleneck link.

    Require advanced JSON configuration file.

    Example parameters.json:

    [
      {"tcp": "vegas", "num": 3},
      {"tcp": "bbr", "num": 2}
    ]
    """

    def __init__(self, config):
        self.config = config
        self.json = json.load(config.json)
        Case.__init__(self)

    def create_nodes(self):
        self.core = [self.net.addSwitch("core%d" % i, protocol='OpenFlow13')
                     for i in range(2)]
        self.sources = [
            {
                'tcp': self.json[t]['tcp'],
                'hosts': [self.net.addHost('s%s%d' % (self.json[t]['tcp'][:5], i),
                                           ip='10.0.%d.%d' % (2*t+1, i+1))
                          for i in range(self.json[t]['num'])]
            } for t in range(len(self.json))
        ]
        self.sinks = [
            {
                'tcp': self.json[t]['tcp'],
                'hosts': [self.net.addHost('d%s%d' % (self.json[t]['tcp'][:5], i),
                                           ip='10.0.%d.%d' % (2*t+2, i+1))
                          for i in range(self.json[t]['num'])]
            } for t in range(len(self.json))
        ]

    def config_nodes(self):
        create_bottleneck_link(self.net, self.core[0], self.core[1], self.config)
        for tsource in self.sources:
            for host in tsource['hosts']:
                create_access_link(self.net, self.core[0], host, self.config)
        for tsink in self.sinks:
            for host in tsink['hosts']:
                create_access_link(self.net, self.core[1], host, self.config)

        Case.config_nodes(self)

    def test(self):
        for tsink in self.sinks:
            for sink in tsink['hosts']:
                sink.cmd('iperf3 -s -D')

        info('Collecting data...\n')
        self.waiting_time = self.config.duration + 2

        cnt = 0
        for t in range(len(self.sources)):
            for i in range(len(self.sources[t]['hosts'])):
                send_cmd = SND_CMD % ('10.0.%d.%d' % (2*t+2, i+1), self.config.duration,
                                      self.sources[t]['tcp'], self.config.mss, cnt)
                self.sources[t]['hosts'][i].cmd('sleep %d && %s &'
                                                % (i * self.config.gap + 1, send_cmd))
                cnt += 1

        Case.test(self)
