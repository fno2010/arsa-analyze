#!/usr/bin/env python2.7

import sys
import argparse

from mininet.log import error, setLogLevel

from testcase import SingleBottleneckLinkTest, SimpleLinearTest, SingleLinkMixTCPTest

def eval_arsa(N, config):
    """
    Evaluate ARSA.
    """
    if config.test == 'single':
        SingleBottleneckLinkTest(N, config)
    elif config.test == 'simple':
        SimpleLinearTest(N, config)
    elif config.test == 'single-mix':
        SingleLinkMixTCPTest(config)
    else:
        error('Unknown testcase is specified.\n')

def parse_argument():
    cmdline = argparse.ArgumentParser(description='TCP Evaluation.')
    cmdline.add_argument('n_source', metavar='N', type=int,
                         help='The number of source/sink pairs.')
    cmdline.add_argument('--tcp', dest='tcp', action='store',
                         default="reno",
                         help='TCP version to be used (default: reno).')
    cmdline.add_argument('--test', dest='test', action='store',
                         default="single",
                         help='Testcase to be evaluated (default: single).')
    cmdline.add_argument('--duration', dest='duration', action='store',
                         default='100', type=int,
                         help='Duration of each transfer (default: 100 (s)))')
    cmdline.add_argument('--mss', dest='mss', action='store',
                         default='1460', type=int,
                         help='TCP/SCTP maximum segment size (default: 1460 (bytes)))')
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
    cmdline.add_argument('--json', dest='json', type=argparse.FileType('r'),
                         help = 'Extra configuration parameters in json file format')
    cmdline.add_argument('-v', '--verbose', action='store_true',
                         help ='Increase verbosity to trace import statements')
    return cmdline


if __name__ == '__main__':
    setLogLevel('info')
    cmdline = parse_argument()
    config = cmdline.parse_args(sys.argv[1:])

    if config.verbose:
        setLogLevel('debug')
    eval_arsa(config.n_source, config)
