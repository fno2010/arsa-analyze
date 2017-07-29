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
        self.report()

    def report(self):
        info('=' * 25 + ' Report ' + '=' * 25 + '\n')

        info('=' * 20 + ' Config ' + '=' * 20 + '\n')
        for tcp in self.json:
            info(str(tcp) + '\n')

        info('=' * 20 + ' Result ' + '=' * 20 + '\n')
        cnt = 0
        for tcp in self.json:
            for i in range(tcp['num']):
                info('\n===> %s flow #%d: <===\n\n' % (tcp['tcp'], i))
                for l in open('%d.log' % cnt, 'r').readlines()[-5:-2]:
                    info(l)
                cnt += 1

        info('=' * 58 + '\n')


class LinearMixTCPTest(Case):
    """
    Evaluate bandwidth allocation of mixed TCP flows in a linear topology.

    Require advanced JSON configuration file.

    Example settings.json:

    [
      {"tcp": "vegas", "from": 0, "to": 1},
      {"tcp": "vegas", "from": 1, "to": 2},
      {"tcp": "bbr", "from": 0, "to": 2}
    ]

    Example advanced-settings.json:

    {
      "capacity": [2, 1],
      "flow": [
        {"tcp": "vegas", "from": 0, "to": 1},
        {"tcp": "vegas", "from": 1, "to": 2},
        {"tcp": "reno", "from": 0, "to": 2}
      ]
    }
    """

    def __init__(self, config):
        self.config = config
        self.json = json.load(config.json)
        if type(self.json) == list:
            self.flow = self.json
            self.capacity = []
        else:
            self.flow = self.json['flow']
            self.capacity = self.json['capacity']
        self.N = max([max(x['from'], x['to']) for x in self.flow]) + 1
        self.F = len(self.flow)
        if not self.capacity:
            self.capacity = [self.config.bw] * self.N
        Case.__init__(self)

    def create_nodes(self):
        self.core = [self.net.addSwitch("core%d" % i, protocol="OpenFlow13")
                     for i in range(self.N)]
        self.host = [
            {
                'tcp': self.flow[i]['tcp'],
                'src': self.net.addHost('s%s%d' % (self.flow[i]['tcp'][:5], i),
                                        ip='10.0.1.%d' % (i+1)),
                'dst': self.net.addHost('d%s%d' % (self.flow[i]['tcp'][:5], i),
                                        ip='10.0.2.%d' % (i+1))
            } for i in range(self.F)
        ]

    def config_nodes(self):
        for i in range(self.N - 1):
            create_bottleneck_link(self.net, self.core[i], self.core[i + 1],
                                   self.config, bw=self.capacity[i])

        for i in range(self.F):
            create_access_link(self.net, self.core[self.flow[i]['from']],
                               self.host[i]['src'], self.config)
            create_access_link(self.net, self.core[self.flow[i]['to']],
                               self.host[i]['dst'], self.config)

        Case.config_nodes(self)

    def test(self):
        for i in range(self.F):
            self.host[i]['dst'].cmd('iperf3 -s -D')

        info('Collecting data...\n')
        self.waiting_time = self.config.duration + 2

        for i in range(self.F):
            send_cmd = SND_CMD % ('10.0.2.%d' % (i+1), self.config.duration,
                                  self.config.tcp, self.config.mss, i)
            self.host[i]['src'].cmd('sleep %d && %s &' % (2, send_cmd))

        Case.test(self)
        self.report()

    def report(self):
        info('=' * 25 + ' Report ' + '=' * 25 + '\n')

        info('=' * 20 + ' Config ' + '=' * 20 + '\n')
        info('===> Capacity <===\n')
        for i in range(self.N-1):
            info('capacity of link (%d -> %d): %d Mbps\n' % (i, i+1,
                                                             self.capacity[i]))
        info('===> Flow <===\n')
        for tcp in self.flow:
            info(str(tcp) + '\n')

        info('=' * 20 + ' Result ' + '=' * 20 + '\n')
        for i in range(self.F):
            info('\n===> flow #%d (%s, %d -> %d): <===\n\n' % (i,
                                                               self.flow[i]['tcp'],
                                                               self.flow[i]['from'],
                                                               self.flow[i]['to']))
            for l in open('%d.log' % i, 'r').readlines()[-5:-2]:
                info(l)

        info('=' * 58 + '\n')


class ClosTopologyTest(Case):
    """
    Evaluate ARSA in a Clos topology

    Example parameters.json:

    [
    {"tcp": "vegas", "from": [0,0,0], "to": [0,0,1], "time": 50},
    {"tcp": "vegas", "from": [0,1,0], "to": [0,0,1]}
    ]
    """

    def __init__(self, K, config):
        self.K = K / 2 * 2
        self.config = config
        self.json = json.load(config.json)

        Case.__init__(self)

    def create_nodes(self):
        K = self.K
        K2 = self.K / 2
        # (k/2)^2 core switches
        self.core = [[self.net.addSwitch('core%d%d' % (i,j), protocol='OpenFlow13')
                      for j in range(K2)]
                     for i in range(K2)]

        self.aggr = [[self.net.addSwitch('aggr%d%d' % (i,j), protocol='OpenFlow13')
                      for j in range(K2)]
                     for i in range(K)]
        self.edge = [[self.net.addSwitch('edge%d%d' % (i,j), protocol='OpenFlow13')
                      for j in range(K2)]
                     for i in range(K)]

        self.hosts = {}
        # hosts are added as switches to avoid iperf3 port conflicts
        for i in range(K): # pod
            for j in range(K2): # edge switch
                for k in range(K2): # port
                    self.hosts[(i,j,k)] = self.net.addSwitch('h%d%d%d' % (i,j,k),
                                                             protocol='OpenFlow13')

        # set up the links
        for i in range(K2):
            for j in range(K2):
                for k in range(K):
                    create_access_link(self.net,
                                       self.core[i][j],
                                       self.aggr[k][i],
                                       self.config)

        for i in range(K):
            for j in range(K2):
                for k in range(K2):
                    create_access_link(self.net,
                                       self.aggr[i][j],
                                       self.edge[i][k],
                                       self.config)

        for i in range(K):
            for j in range(K2):
                for k in range(K2):
                    create_bottleneck_link(self.net,
                                           self.edge[i][j],
                                           self.hosts[(i,j,k)],
                                           self.config)

        self.flows = []
        self.delay = 0
        for i in range(len(self.json)):
            tcp = self.json[i]['tcp']
            si, sj, sk = self.json[i]['from']
            print si, sj, sk
            di, dj, dk = self.json[i]['to']
            print di, dj, dk
            delay = self.json[i]['time'] if 'time' in self.json[i] else 5
            sip = '10.%d.%d.%d' % (si, sj * K2 + sk, i+1)
            dip = '10.%d.%d.%d' % (di, dj * K2 + dk, i+1)
            sender = self.net.addHost('s%s%d' % (tcp, i), ip=sip)
            receiver = self.net.addHost('d%s%d' % (tcp, i), ip=dip)
            self.flows += [(sender, receiver, sip, dip, tcp, delay)]
            self.delay = max(self.delay, delay)

            create_access_link(self.net,
                               self.hosts[(si, sj, sk)],
                               sender,
                               self.config)
            create_access_link(self.net,
                               self.hosts[(di, dj, dk)],
                               receiver,
                               self.config)

    def config_nodes(self):
        Case.config_nodes(self)

    def test(self):
        info('Collecting data...\n')
        self.waiting_time = self.config.duration + self.delay + 2

        cnt = 0
        for sender, receiver, sip, dip, tcp, delay in self.flows:
            recv_cmd = 'iperf3 -s -D'
            send_cmd = SND_CMD % (dip, self.config.duration,
                                  tcp, self.config.mss, cnt)
            cnt += 1
            print sip, dip, send_cmd

            receiver.cmd(recv_cmd)
            sender.cmd('sleep %d && %s &' % (delay, send_cmd))

        Case.test(self)
        self.report()

    def report(self):
        info('=' * 25 + ' Report ' + '=' * 25 + '\n')

        info('=' * 20 + ' Config ' + '=' * 20 + '\n')
        for tcp in self.json:
            info(str(tcp) + '\n')

        cnt = 0
        for sender, receiver, sip, dip, tcp, delay in self.flows:
            info('\n=== #%d flow: %s, %s -> %s ===\n\n' % (cnt, tcp, sip, dip))
            for l in open('%d.log' % cnt, 'r').readlines()[-5:-2]:
                info(l)
            cnt += 1

        info('=' * 58 + '\n')
