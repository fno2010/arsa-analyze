#!/usr/bin/env python2.7

import os
from time import sleep

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, OVSController
from mininet.link import TCLink
from mininet.log import info
from mininet.cli import CLI

from util.cmd import CLEAR_LINE

class Case(object):
    """
    Object for the testcase.
    """

    def __init__(self):
        self.waiting_time = 0
        self.setup_network()
        self.create_nodes()
        self.config_nodes()
        self.test()
        self.clean_up()

    def setup_network(self):
        """
        Setup mininet instance.
        """
        self.net = Mininet(switch=OVSKernelSwitch, link=TCLink)
        self.net.addController("c1", controller=OVSController)

    def create_nodes(self):
        """
        Create hosts and switches.
        """
        pass

    def config_nodes(self):
        """
        Configure links between hosts or switches.
        """
        self.net.build()
        self.net.start()

    def test(self):
        """
        Override it by your own test program.
        """
        while self.waiting_time > 0:
            info(CLEAR_LINE)
            info('Please wait for %d s' % (self.waiting_time))
            sleep(1)
            self.waiting_time -= 1
        info(CLEAR_LINE)
        info(u'Done \u2714\n')
        CLI(self.net)

    def clean_up(self):
        """
        Clean up the environment and exit.
        """
        info('Stoping all backend tasks...\n')
        os.system('pkill "iperf3*"')
        os.system('pkill "tcpdump*"')
        info('Exiting mininet...\n')
        self.net.stop()
