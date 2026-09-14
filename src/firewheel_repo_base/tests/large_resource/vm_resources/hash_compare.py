#!/usr/bin/env python3

import os
import sys
import json
import hashlib


def hash_file(fname):
    """
    A relatively efficient way of hashing a file
    https://stackoverflow.com/a/3431838.
    Through various performance tests, we found that SHA1 is currently the fastest
    hashlib function. We also found that SHA-1 performance improved by using a
    chunk size of 1048576.

    Args:
        fname (str): The name of the file to hash.

    Returns:
        str: The hash of the file.
    """
    # The following hash is not used in any security context and
    # collisions are acceptable.
    hash_func = hashlib.sha1()  # noqa: S324
    with open(fname, "rb") as fopened:
        for chunk in iter(lambda: fopened.read(1048576), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("This requires a file path and a previous hash.")
        sys.exit(1)

    PATH = sys.argv[1]
    PREV_HASH = sys.argv[2]

    # We need a standard path for the status file
    STATUS_FILE = "/tmp/status"  # noqa: S108

    CURR_HASH = hash_file(PATH)

    TEST_PASS = False
    if CURR_HASH == PREV_HASH:
        TEST_PASS = True

    if not os.path.exists(os.path.dirname(STATUS_FILE)):
        os.makedirs(os.path.dirname(STATUS_FILE))

    with open(STATUS_FILE, "w", encoding="utf-8") as fhand:
        if TEST_PASS is True:
            fhand.write("pass")
            print(json.dumps({"test": "pass"}))
        else:
            fhand.write("fail")
            print(json.dumps({"test": "fail"}))
