from base_objects import VMEndpoint

from firewheel.control.experiment_graph import AbstractPlugin


class CheckTimes(AbstractPlugin):
    """
    Intended for use with the check_times functional test. It adds the ``check_time.sh``
    VM resource to all VMs in the experiment. It outputs the current time within the
    experiment.

    The ``check_time.sh`` VMR will run at time=30.
    """

    def run(self):
        """
        Executes the plugin and adds the ``check_time.sh`` at time=30 to all VMs.
        This ignores OS and other potential conflicts.
        """
        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(VMEndpoint):
                vertex.run_executable(
                    30, "check_time.sh", arguments=None, vm_resource=True
                )
