from firewheel.control.experiment_graph import AbstractPlugin


class ConfigureIps(AbstractPlugin):
    """
    This Plugin ensures that default gateways are set and then, if any VM types
    have a special method of configuring their IP addresses, those actions should
    be scheduled immediately.
    """

    def run(self):
        """
        For each :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` in the graph,
        set any default gateway information and then
        call the ``configure_ips`` method and ignore possible attribute errors.
        """
        for vm in self.g.get_vertices():
            # Add in default gateway information if it can be determined
            if vm.type == "router":
                try:
                    vm.interfaces.interfaces  # noqa: B018
                except AttributeError:
                    continue
                for interface in vm.interfaces.interfaces:
                    if (
                        not interface["control_network"]
                        and not interface["l2_connection"]
                    ):
                        vm.set_default_gateway(interface)

        for vm in self.g.get_vertices():
            if vm.type == "host":
                try:
                    vm.configure_ips()
                except AttributeError:
                    pass
