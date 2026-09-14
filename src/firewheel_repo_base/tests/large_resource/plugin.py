import os

from base_objects import VMEndpoint, AbstractWindowsEndpoint

from firewheel.lib.utilities import hash_file, strtobool
from firewheel.control.experiment_graph import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Add a newly generated VM resource containing random bytes to each
    VM in the experiment.
    """

    def run(self, size="1048576", location_dir="/tmp", preload="True"):  # noqa: S108
        """
        Generate a new binary file, get its hash, and then drop both the
        binary and the ``hash_compare.py`` VMR on every VM in the experiment.

        Args:
            size (str, optional): The size in bytes. The default is 1048576 (i.e. 1 MB).
            location_dir (str, optional): Where to place the file on the VM. Default is ``"/tmp"``.
            preload (str, optional): Whether of not to push the file into the VM before negative
                time starts. Should be either ``"True"`` or ``"False"``. Defaults to ``"True"``.
        """

        size = int(size)
        preload = bool(strtobool(preload))
        current_module_path = os.path.abspath(os.path.dirname(__file__))
        filename = "test_random_data.bin"
        path = os.path.join(current_module_path, "vm_resources", filename)

        # Create the binary file.
        # Only write 100MB at a time to prevent blocking when creating huge files.
        with open(path, "wb") as fout:
            loop_size = 104857600  # This equals 100MB
            random_bytes = os.urandom(loop_size)
            while True:
                if size < loop_size:
                    fout.write(os.urandom(size))
                    break
                fout.write(random_bytes)
                size -= loop_size

        # Get the hash of the file
        pre_hash = hash_file(path)

        # Add the binary to all VMs
        for v in self.g.get_vertices():
            if v.is_decorated_by(VMEndpoint):
                if v.is_decorated_by(AbstractWindowsEndpoint):
                    location_dir = f"C:{location_dir}"
                v.run_executable(-50, "mkdir", location_dir)
                location = os.path.join(location_dir, filename)
                v.drop_file(-1, location, filename, preload=preload)
                v.run_executable(
                    10,
                    "hash_compare.py",
                    arguments=[location, pre_hash],
                    vm_resource=True,
                )
