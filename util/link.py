#!/usr/bin/env python2.7

def create_bottleneck_link(net, n1, n2, config, bw=None, delay=None):
    return net.addLink(n1, n2,
                       bw=bw or config.bw,
                       delay=delay or config.delay,
                       max_queue_size=config.queue_size)

def create_access_link(net, n1, n2, config, bw=None, delay=None):
    return net.addLink(n1, n2,
                       bw=bw or 1000, # 1000 Mbps = 1 Gbps
                       delay=delay or "2us", # 2us
                       max_queue_size=10000) # sufficiently large queue size

def create_core_link(net, n1, n2, config):
    return net.addLink(n1, n2,
                       bw=1000,
                       delay=config.delay,
                       max_queue_size=config.queue_size)
