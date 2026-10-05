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

    def _ensure_text(self, output):
        """
        Convert bytes to text for Python 3 while remaining safe on Python 2.

        Args:
            output (str|bytes): The text that needs to be converted

        Returns:
            str: Converting bytes to string in a python2/3 safe way
        """
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="replace")
        return output

    def linux_ping(self, ip):
        """
        Issue a ping command which will send 100 packets to the given IP address.

        Args:
            ip (str): An IP address to ping.

        Returns:
            str: The combined output from the ping command.
        """
        ping_cmd = ["ping", "-c100", ip]
        try:
            return subprocess.check_output(  # nosec
                ping_cmd,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            # Return whatever output ping produced so parsing can still proceed.
            return exc.output

    def parse_drops(self, output):
        """
        Parse the percent of dropped packets.

        Args:
            output (str|bytes): The output string that should be parsed.

        Returns:
            str: The percentage of dropped packets.
        """
        output = self._ensure_text(output)
        lines = output.split("\n")

        loss_line = ""
        for line in lines:
            if "packet loss" in line:
                loss_line = line

        percent = "0"
        for words in loss_line.split():
            if "%" in words:
                percent = words.strip("%")
        return percent

    def parse_delay(self, output):
        """
        Parse the amount of packet delay.

        Args:
            output (str|bytes): The output string that should be parsed.

        Returns:
            str: The average packet delay.
        """
        output = self._ensure_text(output)
        lines = output.split("\n")

        avg_line = ""
        for line in lines:
            if "min/avg/max" in line or "round-trip min/avg/max" in line:
                avg_line = line

        if not avg_line:
            return "0"

        parts = avg_line.split("=")
        if len(parts) < 2:
            return "0"

        stats = parts[1].strip().split("/")
        if len(stats) < 2:
            return "0"

        return stats[1].strip()

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

            if self.parse_type == "drops":
                output = self.parse_drops(success)
            elif self.parse_type == "delay":
                output = self.parse_delay(success)
            else:
                output = "Unknown parse type"

            with open(self.status_file, "a", encoding="utf-8") as f_hand:
                f_hand.write(str(output))


if __name__ == "__main__":
    ip_list = []
    if len(sys.argv) >= 3:
        ip_list = sys.argv[2:]
    else:
        print("Not enough arguments.\nusage: qos_test.py [delay | drops] [ip] [ip]...")
        sys.exit(1)

    agent = QosTest(sys.argv[1], ip_list)
    agent.run()
