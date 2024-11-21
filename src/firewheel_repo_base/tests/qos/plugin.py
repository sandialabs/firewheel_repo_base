from base_objects import Switch
from linux.ubuntu1604 import Ubuntu1604Server

from firewheel.control.experiment_graph import Vertex, AbstractPlugin


class Plugin(AbstractPlugin):
    """
    Enable testing the quality of service (QoS) for edges.
    Currently, we verify that both ``"delay"`` and ``"dropped packets"`` are correctly handled.
    Additionally, default values are provided for both. The delay adds 10,000 ms delay
    and the packet loss is 50%.
    """

    def run(self, test="delay"):
        """
        Construct a simple topology with two VMs and connect them with a
        :py:class:`Switch <base_objects.Switch>`. Then add the specified QoS parameter to the edge.
        This serves as an example of *how* QoS can be implemented
        in FIREWHEEL and is used in our functional test suite.

        Args:
            test (str, optional): The type of QoS to measure. Should be one of
                ``{"delay", "drops"}``. Defaults to ``"delay"``.

        Note:
            The QoS parameters will only impact the **egress** traffic for the given edge.

        Raises:
            RuntimeError: If the test is not one of ``{"delay", "drops"}``.
        """

        # Create our two hosts and the switch
        host1 = Vertex(self.g, "host1")
        host1.decorate(Ubuntu1604Server)

        host2 = Vertex(self.g, "host2")
        host2.decorate(Ubuntu1604Server)

        switch = Vertex(self.g, "qos.switch")
        switch.decorate(Switch)

        # Create the IP addresses
        ip_1 = "192.168.1.1"
        ip_2 = "192.168.1.2"
        netmask = "255.255.255.0"

        # Add the necessary QoS attributes to the egress for host1
        if test == "delay":
            host1.connect(switch, ip_1, netmask, delay="10000ms")
        elif test == "drops":
            host1.connect(switch, ip_1, netmask, packet_loss=50)
        else:
            raise RuntimeError(
                f"Unknown test case '{test}'. Expect 'delay' or 'drops'."
            )

        # Connect the second host to the switch
        host2.connect(switch, ip_2, netmask)

        # Add a VMR which will execute the testing of the QoS parameter
        host1.run_executable(5, "qos_test.py", arguments=[test, ip_2], vm_resource=True)
        host2.run_executable(5, "qos_test.py", arguments=[test, ip_1], vm_resource=True)
