#!/usr/bin/env python
import sys
import pickle
from time import sleep
from subprocess import PIPE, Popen  # nosec


# This class should remain Python 2 compatible
class Runner(object):
    """
    VM Resource that will run an arbitrary program with the supplied arguments.
    A pickled dictionary is passed in specifying the location of the program
    to run and the arguments that should be passed to it.

    ASCII input data structure:

    # Example dictionary for running a program
    {
        'program_location': <path to program>,
        'arguments': <Optional, can be list or string of arguments
                that must be passed to the program>,
        'env': {} <Optional, dictionary with environment variables to pass
                    to Popen>,
        'user': <Optional, username which runs the command>
        'cwd': <Optional, directory to run Popen command from>,
        'blocking': <Optional, specify if the runner should wait and check
                    the error code returned from Popen>,
        'shell': <Optional: Indicate if the Popen process needs the shell>
    }

    """

    def __init__(self, ascii_file=None, binary_file=None):
        """
        Constructor for the class. Pass in standard vm_resource parameters

        Args:
            ascii_file (str): The path to a file which contains a pickled
                list of dictionaries as specified above.
            binary_file (str): Unused in this vm_resource
        """
        self.ascii_file = ascii_file
        self.binary_file = binary_file

    def run(self):
        """
        Standard vm_resource run function. This performs the work of the vm_resource.
        Requires no parameters, since they are passed into __init__()
        """
        with open(self.ascii_file, "r", encoding="utf-8") as f_hand:
            # Get the pickled dictionary passed in
            ascii_data = f_hand.read().strip()

        # Unpickle the dictionary
        # Data passed into the VM is considered "safe"
        data = pickle.loads(ascii_data)  # nosec

        arguments = []
        # Get the location of the program to run
        if "program_location" in data:
            arguments.append(data["program_location"])
        else:
            print("No program location specified, unable to run program.")
            return

        # Check if arguments have been passed
        if "arguments" in data:
            if isinstance(data["arguments"], list):
                arguments += data["arguments"]
            elif isinstance(data["arguments"], str):
                arguments += data["arguments"].split()
            else:
                print("Arguments are not a list or a string, skipping arguments")

        # Check if the program should run as a specific user
        if "user" in data:
            # We want the entire command to be one argument passed into su so we
            # are putting the existing arguments in implicit quotes. (as one list entry)
            arguments = ["su", "-", data["user"], "-c", " ".join(arguments)]

        env = None
        if data.get("env"):
            env = data["env"]

        cwd = None
        if data.get("cwd"):
            cwd = data["cwd"]

        shell = False
        if data.get("shell"):
            shell = True

        # Run the program
        run = Popen(  # noqa: DUO116
            arguments,
            stdout=PIPE,
            stderr=PIPE,
            env=env,
            cwd=cwd,
            shell=shell,  # nosec
        )

        # If blocking is set to False then don't check the error code,
        # simply return
        if "blocking" in data and not data["blocking"]:
            count = 0
            while not self.verify_process_running(str(run.pid)):
                sleep(1)
                count += 1
                if count == 5:
                    return
            return

        output = run.communicate()

        # Check for an error
        if run.returncode != 0:
            print("Error: %s" % output[1])

    def verify_process_running(self, pid):
        """Verify that the started process is actually running.

        Args:
            pid (str): The process ID for the started process.

        Returns:
            bool: True if the process is running, False otherwise.
        """
        process = Popen(["/bin/ps", "faux"], stdout=PIPE, stderr=PIPE)

        output = process.communicate()

        stdout = output[0].split("\n")

        for process in stdout:
            if not process:
                continue
            p_pid = process.split()[1]

            try:
                cpu = float(process.split()[2])
            except ValueError:
                continue

            # Check to make sure that the PID is in the
            # process list and make sure that CPU usage
            # is higher than 0 in order to determine that
            # that the process has actually started
            if pid == p_pid and cpu > 0:
                return True

        return False


if __name__ == "__main__":
    # Only takes an ascii file
    runner = Runner(sys.argv[1])
    runner.run()
