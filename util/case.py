#!/usr/bin/env python2.7

import os

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, OVSController
from mininet.link import TCLink
from mininet.log import info
from mininet.cli import CLI

class Case(object):
    """
    Object for the testcase.
    """

    def __init__(self):
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
        Your test program.
        """
        CLI(self.net)

    def clean_up(self):
        """
        Clean up the environment and exit.
        """
        info('Stoping all iperf3 tasks...\n')
        os.system('pkill "iperf3*"')
        os.system('pkill "tcpdump*"')
        info('Exiting mininet...\n')
        self.net.stop()
