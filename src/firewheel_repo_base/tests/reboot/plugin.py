from base_objects import VMEndpoint

from firewheel.control.experiment_graph import AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Add an VM resource which will reboot the VM and then verify that a reboot has occurred.
    """

    def run(self, reboot_type="exit_code", extra_vrm=""):
        """
        Add a VM resource to each VM in the experiment.

        Args:
            reboot_type (str): Which VM resource to use. It can be one of: {exit_code, flag}.
            extra_vrm (str): The time at which to run a VRM which adds "running" to the status
                file. This will help test the order of reboots and ensure that the schedule
                is maintained. Must be castable to an integer. Defaults to ``""``.
        """

        for v in self.g.get_vertices():
            if v.is_decorated_by(VMEndpoint):
                v.run_executable(-10, f"{reboot_type}.py", vm_resource=True)

                if extra_vrm:
                    time = int(extra_vrm)
                    v.run_executable(time, "echo.sh", vm_resource=True)
