from base_objects import VMEndpoint
from generic_vm_objects import GenericRouter

from firewheel.control.experiment_graph import AbstractPlugin


class PingAll(AbstractPlugin):
    """
    Intended for use with functionality tests. Assumes the presence
    of a topology with a fully-connected network.

    Populates a schedule where all nodes in the experiment will run the ``ping_all.py``
    VMR at time 30. The VMR will attempt to ping every IP address in the experiment
    from every node within the experiment. If ``include_routers`` is ``"False"``, then routers
    will be excluded from the test; they will not be pinged or pinging.

    There is no handling of unusual or unexpected conditions in the graph, such
    as disjoint subgraphs, unsupported (by ``ping_all.py``) OSes, etc.
    """

    def run(self, include_routers="false"):
        """
        Executes the plugin. Calls the function to build the list of IPs and
        then build the schedule for all nodes.

        Args:
            include_routers (str): Whether to include routers in the test.
        """
        self.include_routers = bool(
            include_routers and include_routers.lower() == "true"
        )
        ips = self._build_ip_list()
        self._populate_schedule(ips)

    def _build_ip_list(self):
        """
        Build a list of the IP address(es) for all hosts in the experiment.

        Returns:
            list: A list of strings, where each string is an IP address.
        """
        ip_list = []

        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(VMEndpoint):
                if not self.include_routers and vertex.is_decorated_by(GenericRouter):
                    continue

                for interface in vertex.interfaces.interfaces:
                    ip_list.append(interface["address"])

        return ip_list

    def _populate_schedule(self, ip_list):
        """
        Add the ``ping_all.py`` VM Resource to the schedule of every VM
        in the experiment. Ignore OS and other potential conflicts.

        Args:
            ip_list (list): A list of IP addresses as strings. This is sent as a
                string and passed into ``ping_all.py``.
        """
        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(VMEndpoint):
                if not self.include_routers and vertex.is_decorated_by(GenericRouter):
                    vertex.run_executable(
                        5, "ping_all.py", arguments=" ", vm_resource=True
                    )
                else:
                    vertex.run_executable(
                        5,
                        "ping_all.py",
                        arguments=" ".join(str(ip) for ip in ip_list),
                        vm_resource=True,
                    )
