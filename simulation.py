#!/usr/bin/env python2.7

import sys

from mininet.log import error, setLogLevel

from util.arsaconf import parse_argument

from testcase import SingleBottleneckLinkTest, SimpleLinearTest, SingleLinkMixTCPTest, LinearMixTCPTest, ClosTopologyTest

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
    elif config.test == 'linear-mix':
        LinearMixTCPTest(config)
    elif config.test == 'clos':
        ClosTopologyTest(N, config)
    else:
        error('Unknown testcase is specified.\n')

def simulate(args):
    setLogLevel('info')
    cmdline = parse_argument()
    config = cmdline.parse_args(args)

    if config.verbose:
        setLogLevel('debug')
    eval_arsa(config.n_source, config)

if __name__ == '__main__':
    simulate(sys.argv[1:])
