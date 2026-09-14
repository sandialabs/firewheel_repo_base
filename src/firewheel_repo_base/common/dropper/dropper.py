#!/usr/bin/env python
import os
import sys
import pickle
import tarfile
import zipfile
from time import sleep
from shutil import copy2

try:
    import grp
    import pwd
except ImportError:
    print("Using `dropper.py` on Windows, cannot import `grp` or `pwd`.")


# This class should remain Python 2 compatible
class Dropper(object):
    """
    VM Resource that will drop an arbitrary number of ASCII
    files and a single binary tarball. A list of dictionaries
    is passed in to describe what and where to drop files.

    ASCII input data structure:

    [
        # Example dictionary for dropping binary file
        {
            'binary_path': <directory of where to write the binary file>,
            'decompress': <True or False>
            'mode': <optionally give permissions for file as an integer, i.e. 0644>,
            'user': <optionally specify the user and group as a tuple, ie. (1000,1000)>,
            'blocking': <optionally specify a directory that must exist before dropping files>
        },
    ]

    [
        # Example dictionary for dropping ASCII file
        {
            'contents': <contents of the ASCII file to be written to the VM>,
            'path': <path for where to write the ASCII
                (this path should include filename)>,
            'mode': <optionally give permissions for file as an integer, i.e. 0644>,
            'user': <optionally specify the user and group as a tuple, ie. (1000,1000)>,
            'blocking': <optionally specify a directory that must exist before dropping files>
        }
        ...
    ]

    """

    def __init__(self, ascii_file=None, binary_file=None):
        """
        Constructor for the class. Pass in standard vm_resource parameters

        Args:
            ascii_file (str): The path to a file which contains a pickled
                list of dictionaries as specified above.
            binary_file (str): The path to a binary file which has been added to the VM.
        """
        self.ascii_file = ascii_file
        self.binary_file = binary_file
        if binary_file == "None":
            self.binary_file = None

    def run(self):
        """
        Standard vm_resource run function. This performs the work of the vm_resource.
        Requires no parameters, since they are passed into __init__()
        """
        with open(self.ascii_file, "r", encoding="utf-8") as f_hand:
            # Loading data from pickle can be unsafe. However, this will be inside
            # a VM and only passed data as directed via our experiment.
            data = pickle.loads(f_hand.read())

        # Loop over all passed in dictionaries to potentially drop several files
        for file_drop in data:
            # If binary path is in the dictionary, then dropping a binary
            if "binary_path" in file_drop:
                self.drop_binary(file_drop)
            # If contents is in the dictionary, then dropping an ASCII file
            elif "contents" in file_drop:
                self.drop_ascii(file_drop)
            else:
                print("Unrecognized dropper actions for: %s" % file_drop)

    def drop_binary(self, file_drop):
        """
        Function to decompress a binary tarball to a specified directory.

        Args:
            file_drop (dict): Dictionary that was passed in specifying the directory
                to decompress the binary file that was passed into the VM resource.
        """
        if self.binary_file:
            # Read the destination location of the untarred binary
            drop_location = str(file_drop["binary_path"])

            if not os.path.exists(drop_location):
                if file_drop.get("blocking"):
                    while not os.path.exists(file_drop["blocking"]):
                        sleep(10)
                os.makedirs(drop_location)

            # If the binary does not need to be untarred, then just place
            # it at the desired path
            if ("decompress" in file_drop and not file_drop["decompress"]) or (
                "untar_binary" in file_drop and not file_drop["untar_binary"]
            ):
                copy2(self.binary_file, drop_location)
                drop_location = os.path.join(
                    drop_location, os.path.basename(self.binary_file)
                )
            elif tarfile.is_tarfile(self.binary_file):
                # Open the tarball
                with tarfile.open(self.binary_file) as tarball:
                    # Untar to the destination
                    tarball.extractall(path=drop_location)  # noqa: S202
            elif zipfile.is_zipfile(self.binary_file):
                # Open the zipfile
                with zipfile.ZipFile(self.binary_file, mode="r") as ziped:
                    # Unzip to the destination
                    zipfile.ZipFile.extractall(ziped, path=drop_location)  # noqa: S202
            else:
                print(
                    "ERROR: Unsupported archive format for file %s. "
                    "Need tar/gz, tar/bz2, or zip." % (self.binary_file)
                )
                return
            self.set_mode(file_drop, drop_location)
            self.set_user(file_drop, drop_location)
        else:
            print("Unable to drop binary: %s. No binary given" % file_drop)

    def drop_ascii(self, file_drop):
        """
        Function to drop an ASCII file at a specified location.

        Note:
            The path that is passed in via the dictionary should
            contain the name of the destination file for the ASCII text.

        Args:
            file_drop (dict): dictionary specifying what and where to write
                the passed in 'contents' of the ASCII file
        """
        # Path to write the 'contents' to on the VM
        # This path should end with the destination filename
        if "path" in file_drop:
            drop_location = str(file_drop["path"])
        else:
            print("No path specified to drop ascii file")
            return

        # ASCII to the written out the 'path' from above
        if "contents" not in file_drop:
            print("No ascii contents to write to: %s" % drop_location)
            return

        destination_dir = os.path.dirname(drop_location)
        if not os.path.exists(destination_dir):
            if file_drop.get("blocking"):
                while not os.path.exists(file_drop["blocking"]):
                    sleep(10)
            os.makedirs(destination_dir)

        with open(drop_location, "w", encoding="utf-8") as f_hand:
            f_hand.write(file_drop["contents"])

        self.set_mode(file_drop, drop_location)
        self.set_user(file_drop, drop_location)

    def set_mode(self, file_drop, drop_location):
        """
        Set the file mode for the given file placed on the VM.

        Note:
            The mode/user/group are all Linux specific and will not
            work on Windows.

        Args:
            file_drop (dict): The configuration dictionary for the given file.
            drop_location (str): The path of the dropped file.
        """
        if "win32" not in sys.platform.lower():
            # Optionally set the permissions of the file
            if "mode" in file_drop:
                os.chmod(drop_location, int(file_drop["mode"]))

    def set_user(self, file_drop, drop_location):
        """Set the user/group permissions for the given dropped file.

        Note:
            The mode/user/group are all Linux specific and will not
            work on Windows.

        Args:
            file_drop (dict): The configuration dictionary for the given file.
            drop_location (str): The path of the dropped file.
        """
        if "win32" not in sys.platform.lower():
            # Optionally set the user and group
            if "user" in file_drop:
                # Resolve a UID integer if we need to.
                try:
                    uid = int(file_drop["user"][0])
                except ValueError:
                    uid = pwd.getpwnam(file_drop["user"][0]).pw_uid

                # Resolve a GID integer if we need to.
                try:
                    gid = int(file_drop["user"][1])
                except ValueError:
                    gid = grp.getgrnam(file_drop["user"][1]).gr_gid

                os.chown(drop_location, uid, gid)


if __name__ == "__main__":
    dropper = Dropper(sys.argv[1], sys.argv[2])
    dropper.run()
