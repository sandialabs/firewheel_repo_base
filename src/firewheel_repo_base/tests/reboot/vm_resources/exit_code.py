#!/usr/bin/env python3

import os
import sys
import json

if __name__ == "__main__":
    # We need a standard path for the status file
    STATUS_FILE = "/tmp/status"  # noqa: S108

    if not os.path.exists(os.path.dirname(STATUS_FILE)):
        os.makedirs(os.path.dirname(STATUS_FILE))

    FIRST_BOOT = "/FIRST_BOOT"
    if not os.path.exists(FIRST_BOOT):
        with open(FIRST_BOOT, "w", encoding="utf-8") as fhand:
            fhand.write("This is the first time the VMR is running.")

        # We can now reboot with exit code 10
        sys.exit(10)
    else:
        with open(STATUS_FILE, "a", encoding="utf-8") as fhand:
            # If we saved any status here, we should add it to the status
            # file.
            VAR_STATUS = "/var/tmp/status"  # noqa: S108
            STATUS = ""
            if os.path.exists(VAR_STATUS):
                with open(VAR_STATUS, "r", encoding="utf-8") as stat_file:
                    STATUS = stat_file.read()
            fhand.write("%spass" % STATUS)
            print(json.dumps({"test": "pass"}))
