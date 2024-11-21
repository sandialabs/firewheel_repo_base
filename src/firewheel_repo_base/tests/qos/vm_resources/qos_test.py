#!/usr/bin/env python3

import sys
import subprocess
from time import sleep


# This class should remain Python 2 compatible
class QosTest(object):
    """
    Enable checking for QoS parameters including dropped packets and delay.
    This class requires at least two parameters:

    1. The type of QoS to measure. It should be either "drops" or "delay".
    2. Any number of IP addresses. This module assumes that any parameters past
       the first one are IP addresses.

    """

    def __init__(self, parse_type, ips):
        """
        Add some class variables based on our VMR inputs.

        Args:
            parse_type (str): The QoS parameter which is being measured.
            ips (list): A list of IP addresses for which we should analyze QoS.
        """
        self.parse_type = parse_type
        self.ips = ips
        self.status_file = "/tmp/status"  # noqa: S108

    def linux_ping(self, ip):
        """
        Issue a ping command which will send 100 packets to the given IP address.

        Args:
            ip (str): An IP address to ping.

        Returns:
            str: The output from the ping command.
        """
        ping_cmd = ["ping", "-c100", ip]
        return subprocess.check_output(ping_cmd)  # nosec

    def parse_drops(self, output):
        """
        Parse the percent of dropped packets.

        Args:
            output (str): The string output that should be parsed.

        Returns:
            str: The percentage of dropped packets.
        """
        lines = output.split("\n")

        loss_line = ""
        for line in lines:
            if "packet loss" in line:
                loss_line = line

        percent = 0
        for words in loss_line.split():
            if "%" in words:
                percent = words.strip("%")
        return percent

    def parse_delay(self, output):
        """
        Parse the amount of packet delay.

        Args:
            output (str): The string output that should be parsed.

        Returns:
            str: The amount of packet delay.
        """
        lines = output.split("\n")

        avg_line = ""
        for line in lines:
            if "min/avg/max" in line:
                avg_line = line
        return avg_line.split("/")[-3]

    def run(self):
        """
        The main function for pinging IPs, getting the output, and writing the result
        to the status file.
        """
        for ip in self.ips:
            success = ""
            attempt = 0
            while not success and attempt < 10:
                success = self.linux_ping(ip)
                if success:
                    break
                attempt += 1
                print("On attempt: %d, sleeping 5 before trying again" % attempt)
                print(success)
                sys.stdout.flush()
                sleep(5)

            output = None
            if self.parse_type == "drops":
                output = self.parse_drops(success)
            elif self.parse_type == "delay":
                output = self.parse_delay(success)
            else:
                output = "Unknown parse type"

            with open(self.status_file, "a", encoding="utf-8") as f_hand:
                f_hand.write(output)


if __name__ == "__main__":
    ip_list = []
    if len(sys.argv) >= 3:
        ip_list = sys.argv[2:]
    else:
        print("Not enough arguments.\nusage: qos_test.py [delay | drops] [ip] [ip]...")
        sys.exit(1)

    agent = QosTest(sys.argv[1], ip_list)
    agent.run()
