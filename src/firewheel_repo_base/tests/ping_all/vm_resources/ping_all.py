#!/usr/bin/env python3

import os
import sys
import json
import ipaddress
import subprocess
from time import sleep
from pathlib import Path
from subprocess import call


# This class should remain Python 3.5 compatible
class PingAll:
    """
    Provide a class to ping all the passed-in IP addresses and output the success/failure.
    """

    def __init__(self, ip_list):
        """Initialize the class.

        Args:
            ip_list (list): A list of IP addresses to Ping.
        """
        self.ips = ip_list
        # We need a standard path for the status file
+        self.status_file = Path("/tmp/status")  # noqa: S108

    def run(self):
        """
        Attempt to ping all IP address and output a result.
        The original input was a space-separated list of IP addresses to ping.
        If all pings succeed, we pass, otherwise the test fails.
        """
        test_pass = True

        for ip in self.ips:
            ipv6 = bool(ipaddress.ip_address(ip).version == 6)
            if sys.platform == "win32":
                success = self.win_ping(ip, ipv6=ipv6)
            else:
                success = self.linux_ping(ip, ipv6=ipv6)
            attempt = 0
            while not success:
                if attempt > 10:
                    test_pass = False
                    break
                if sys.platform == "win32":
                    success = self.win_ping(ip)
                else:
                    success = self.linux_ping(ip)
                attempt += 1
                print("on attempt: %d, sleeping 5 before trying" % attempt)
                sys.stdout.flush()
                sleep(5)

        self.status_file.parent.mkdir(exist_ok=True)
        with self.status_file.open("w", encoding="utf-8") as fhand:
            if test_pass is True:
                fhand.write("pass")
                print(json.dumps({"test": "pass"}))
            else:
                fhand.write("fail")
                print(json.dumps({"test": "fail"}))

    def linux_ping(self, ip, ipv6=False):
        """
        Issue a Unix-specific ping command to send one ping packet.
        This will also timeout in 2 seconds if no response is received.

        Args:
            ip (str): The IP address to ping.
            ipv6 (bool): Is the IP address a version 6 address.

        Returns:
            bool: Wether of not the ping was successful.
        """
        if ipv6:
            ping_cmd = ["ping6", "-c1", "-W2", ip]
        else:
            ping_cmd = ["ping", "-c1", "-W2", ip]
        ret = call(ping_cmd)  # nosec
        return bool(not ret)

    def win_ping(self, ip, ipv6=False):
        """
        Issue a Windows-specific ping command to send one ping packet.

        Args:
            ip (str): The IP address to ping.
            ipv6 (bool): Is the IP address a version 6 address.

        Returns:
            bool: Wether of not the ping was successful.
        """
        if ipv6:
            cmd = ["ping", "-6", "-n", "1", ip]
        else:
            cmd = ["ping", "-n", "1", ip]

        output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]  # nosec

        if ("unreachable" in output) or ("timeout" in output):
            return False

        return True


if __name__ == "__main__":
    ips = []
    if len(sys.argv) >= 2:
        ips = sys.argv[1:]

    agent = PingAll(ips)
    agent.run()
