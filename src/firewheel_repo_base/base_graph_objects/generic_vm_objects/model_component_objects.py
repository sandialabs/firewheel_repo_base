"""
This module contains MC objects representing generic capability interfaces
that may be realized by multiple concrete/image MC objects.

A good example of this is routers. Different types of routers may realize BGP
and OSPF connections, so the GenericRouter object is located here.
"""

import netaddr
from base_objects import Switch, VMEndpoint

from firewheel.control.experiment_graph import require_class


@require_class(VMEndpoint)
class GenericRouter:
    """
    This MC object represents interfaces common to many/all router
    platforms. This mostly takes the form of defining routing protocol connections,
    where the interconnection between routers is formed by a
    ``<protocol>_connect()`` method that takes the place of the typical
    :py:meth:`connect() <base_objects.VMEndpoint.connect>` method.

    Currently supported protocols are:

    * :term:`OSPF <Open Shortest Path First>`
    * :term:`BGP <Border Gateway Protocol>`

    By default, routes from one protocol will not propagate to peers using
    other protocols. However, this object supports explicit definition of route redistribution.
    "In a router, route redistribution allows a network that uses one routing protocol
    to route traffic dynamically based on information learned from another routing protocol." [#]_
    Currently supported redistributions include:

    - :term:`OSPF <Open Shortest Path First>` into :term:`BGP <Border Gateway Protocol>`
    - :term:`BGP <Border Gateway Protocol>` into :term:`OSPF <Open Shortest Path First>`
    - Connected into :term:`OSPF <Open Shortest Path First>`

    .. [#] https://en.wikipedia.org/wiki/Route_redistribution
    """

    def __init__(self, name=None):
        """Initialize common attributes for all routers.
        For example, routers need a name and a routing dictionary.

        Args:
            name (str, optional): The name of the router. This is typically
                created with the creation of a new
                :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`,
                but this parameter also provides that ability. Defaults to :py:data:`None`.

        Raises:
            RuntimeError: Occurs if the router does not have a name.

        Attributes:
            name (str): The hostname of this router.
            routing (dict): The routing configuration for this router, including protocol
                configurations.
        """

        # Set the Vertex type
        self.type = "router"

        # A name must be specified when using a GenericRouter.
        if (self.name := getattr(self, "name", name)) is None:
            raise RuntimeError("Name must be specified for router!")

        # Overwrite the Vertex name if one is provided
        if name:
            self.name = name

        # Sanity check that this Vertex attribute has not been created.
        self.routing = getattr(self, "routing", {})

    def redistribute_bgp_into_ospf(self):
        """
        Enable redistributing routes from BGP peers to OSPF peers.

        Raises:
            Exception: If some unknown error occurs while trying to redistribute routes.
        """
        try:
            try:
                self.routing["ospf"]["redistribution"] = {"bgp": {}}
            except AttributeError:
                self.routing = {"ospf": {"redistribution": {"bgp": {}}}}
            except KeyError:
                if "ospf" not in self.routing:
                    self.routing["ospf"] = {}
                if "redistribution" not in self.routing["ospf"]:
                    self.routing["ospf"]["redistribution"] = {}
                self.routing["ospf"]["redistribution"]["bgp"] = {}
        except Exception:
            self.log.exception(
                "Cannot redistribute OSPF into BGP (%s)",
                self.name,
            )
            raise

    def redistribute_ospf_into_bgp(self):
        """
        Enable redistributing routes from OSPF peers to BGP peers.

        Raises:
            Exception: If some unknown error occurs while trying to redistribute routes.
        """
        try:
            try:
                self.routing["bgp"]["redistribution"] = {"ospf": {}}
            except AttributeError:
                self.routing = {"bgp": {"redistribution": {"ospf": {}}}}
            except KeyError:
                if "bgp" not in self.routing:
                    self.routing["bgp"] = {}
                if "redistribution" not in self.routing["bgp"]:
                    self.routing["bgp"]["redistribution"] = {}
                self.routing["bgp"]["redistribution"]["ospf"] = {}
        except Exception:
            self.log.exception(
                "Cannot redistribute BGP into OSPF (%s)",
                self.name,
            )
            raise

    def redistribute_ospf_connected(self):
        """
        Redistribute routes for directly connected subnets to OSPF peers.
        """
        try:
            if "ospf" not in self.routing:
                self.log.warning(
                    "OSPF not yet defined for: %s. Creating it now.",
                    self.name,
                )
                self.routing["ospf"] = {}

        except AttributeError:
            self.log.exception(
                "No routing block defined for: %s. Must specify routing protocols "
                "before redistribution",
                self.name,
            )
            return

        if "redistribution" not in self.routing["ospf"]:
            self.routing["ospf"]["redistribution"] = {}

        self.routing["ospf"]["redistribution"]["connected"] = {}

    def ospf_connect(
        self,
        switch,
        ip,
        netmask,
        delay=None,
        rate=None,
        rate_unit=None,
        packet_loss=None,
        area="0",
    ):
        """Connect this router to a switch, and define OSPF on the connection.

        Note:
            The rate is set as a multiple of bits **not** bytes.
            That is, a rate of ``1 kbit`` would equal 1000 bits, not 1000 bytes.
            For bytes, multiply the rate by 8 (e.g. 64 KBytes = 8 * 64 = 512 kbit).

        Args:
            switch (base_objects.Switch): Switch instance to connect to.
            ip (str or netaddr.IPAddress): IP address to use on the connecting interface.
            netmask (str or netaddr.IPAddress): The netmask for the connecting interface.
                The netmask can either be in Dotted Decimal or CIDR (without the slash) notation.
                That is, both ``"255.255.255.0"`` and ``"24"`` would represent the same netmask.
            delay (str): The amount of egress delay to add for the link. This should be
                formatted like ``<delay><unit of delay>``. For example, ``100ms``.
                You must add this in the opposing direction if you want it to be bidirectional.
            rate (int): The maximum egress transmission rate (e.g. bandwidth of this link)
                as a multiple of bits. The ``rate_unit`` should also be set if the unit
                is not ``mbit``.
            rate_unit (str): The bandwidth unit (one of ``{'kbit', 'mbit', 'gbit'}``).
                Defaults to ``"mbit"``.
            packet_loss (int): Percent of packet loss on the link. For example,
                ``packet_loss = 25`` is 25% packet loss.
            area (str): The OSPF area. Defaults to ``"0"``.
        """
        self.routing = getattr(self, "routing", {})
        if "parameters" not in self.routing or not self.routing["parameters"]:
            self.routing["parameters"] = {}
        if "ospf" not in self.routing or not self.routing["ospf"]:
            self.routing["ospf"] = {}
        if (
            "interfaces" not in self.routing["ospf"]
            or not self.routing["ospf"]["interfaces"]
        ):
            self.routing["ospf"]["interfaces"] = {}
        if "areas" not in self.routing["ospf"] or not self.routing["ospf"]["areas"]:
            self.routing["ospf"]["areas"] = {}

        net = netaddr.IPNetwork(ip)
        iface_name, _ = self.connect(
            switch,
            ip,
            netmask,
            delay=delay,
            rate=rate,
            rate_unit=rate_unit,
            packet_loss=packet_loss,
        )

        # Add in OSPF information
        self.routing["ospf"]["interfaces"][iface_name] = {
            "dead-interval": "40",
            "hello-interval": "10",
            "area": area,
            "transmit-delay": "1.0",
            "retransmit-interval": "5.0",
        }
        self.routing["ospf"]["areas"][area] = {}
        if (
            "parameters" not in self.routing
            or "router-id" not in self.routing["parameters"]
        ):
            self.routing["parameters"]["router-id"] = str(net.ip)

    def valid_as(self, as_num):
        """
        Validate that a given AS number is valid. The valid AS numbers were pulled from [#]_.

        Note:
            This may not be completely up-to-date.

        Args:
            as_num (str): AS number, convertible to an integer.

        Returns:
            bool: :py:data:`True` if the AS number is valid, :py:data:`False` otherwise.

        .. [#] https://en.wikipedia.org/wiki/Autonomous_system_(Internet)
        """
        try:
            num = int(as_num)
            if 0 < num < 4294967295:
                return True
        except TypeError:
            self.log.error("The AS number %s is not valid", as_num)
        except ValueError:
            self.log.error("The AS number %s is not valid", as_num)
        return False

    def set_bgp_as(self, as_num):
        """
        Set the Autonomous System Number (ASN) used by BGP for this router.

        Args:
            as_num (str): AS number, convertible to an integer. Must be valid according to
                :py:meth:`valid_as() <generic_vm_objects.GenericRouter.valid_as>`.

        Raises:
            RuntimeError: If the ASN is not valid.
        """
        if not self.valid_as(as_num):
            raise RuntimeError(
                f"The ASN={as_num} is NOT valid. Please see "
                "https://en.wikipedia.org/wiki/Autonomous_system_(Internet) "
                " for more details."
            )

        self.routing = getattr(self, "routing", {})
        if "bgp" not in self.routing or not self.routing["bgp"]:
            self.routing["bgp"] = {}
        if (
            "parameters" not in self.routing["bgp"]
            or not self.routing["bgp"]["parameters"]
        ):
            self.routing["bgp"]["parameters"] = {}
        self.routing["bgp"]["parameters"]["router-as"] = as_num

    def get_bgp_as(self):
        """Retrieve the ASN used by BGP on this router.

        Returns:
            str: The AS number or a negative value if an error occurred.
        """
        try:
            return self.routing["bgp"]["parameters"]["router-as"]
        except KeyError:
            self.log.error("Unable to get BGP AS number: unspecified value.")
            return -1
        except AttributeError:
            self.log.error("Unable to get BGP AS number: no routing structure.")
            return -2

    def add_bgp_network(self, network):
        """Add a subnet to be advertised by BGP from this router.

        Args:
            network (str): The subnet to be advertised, this string can also be a
                :obj:`netaddr.IPNetwork`. The format of the string should be in
                the format of ``<Network IP>/<netmask>`` where ``netmask`` can either
                be CIDR or decimal dot notation. (e.g. ``"192.168.0.0/24"`` or
                ``"192.168.0.0/255.255.255.0"``)

        """
        network = netaddr.IPNetwork(network)
        self.routing = getattr(self, "routing", {})

        if "bgp" not in self.routing or not self.routing["bgp"]:
            self.routing["bgp"] = {}
        if "networks" not in self.routing["bgp"] or not self.routing["bgp"]["networks"]:
            self.routing["bgp"]["networks"] = []

        self.routing["bgp"]["networks"].append(network)

    def get_all_bgp_networks(self):
        """Retrieve the list of subnets advertised by BGP on this router.

        Returns:
            list(netaddr.IPNetwork): List of the subnets advertised by BGP.
        """
        try:
            return self.routing["bgp"]["networks"]
        except KeyError:
            return []
        except AttributeError:
            return []

    def link_bgp(self, neighbor, switch, neighbor_switch=None):
        """Connect this router to another as BGP peers.
        ``switch`` and ``neighbor_switch`` are used to determine the IP address of the
        peers by identifying a single interface. This means they should be
        the first-hop for this router and neighbor, respectively, so the IP
        that is on the correct link is addressed in BGP.

        Args:
            neighbor (generic_vm_objects.GenericRouter):
                The :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
                to configure as a BGP peer.
            switch (base_objects.Switch):
                First-hop switch for this router's connection to neighbor.
            neighbor_switch (base_objects.Switch, optional):
                First-hop switch for neighbor's connection to this router.
                Defaults to :py:data:`None`.

        Raises:
            ValueError: Parameters incorrectly typed.
            RuntimeError: Trying to establish a BGP connection without an ASN.
            RuntimeError: Unable to determine IP address for self or peer.
            Exception: Unable to get interfaces for BGP connection.
        """
        # If a neighbor switch was not passed in then use this vertex's switch
        # that was passed in for both
        if not neighbor_switch:
            neighbor_switch = switch

        if not switch.is_decorated_by(Switch):
            raise ValueError("switch must be a decorated by Switch.")
        if not neighbor_switch.is_decorated_by(Switch):
            raise ValueError("neighbor_switch must be a decorated by Switch.")
        if not neighbor.is_decorated_by(GenericRouter):
            raise ValueError("neighbor must be decorated by GenericRouter.")

        # Establish neighbor connections on each side
        self.routing = getattr(self, "routing", {})
        if "bgp" not in self.routing or not self.routing["bgp"]:
            self.routing["bgp"] = {}
        if (
            "neighbors" not in self.routing["bgp"]
            or not self.routing["bgp"]["neighbors"]
        ):
            self.routing["bgp"]["neighbors"] = []
        if (
            "parameters" not in self.routing["bgp"]
            or not self.routing["bgp"]["parameters"]
        ):
            self.routing["bgp"]["parameters"] = {}
        if (
            "router-as" not in self.routing["bgp"]["parameters"]
            or not self.routing["bgp"]["parameters"]["router-as"]
        ):
            raise RuntimeError(
                f"Trying to establish bgp connection without a set AS on {self.name}"
            )

        neighbor.routing = getattr(neighbor, "routing", {})
        if "bgp" not in neighbor.routing or not neighbor.routing["bgp"]:
            neighbor.routing["bgp"] = {}
        if (
            "neighbors" not in neighbor.routing["bgp"]
            or not neighbor.routing["bgp"]["neighbors"]
        ):
            neighbor.routing["bgp"]["neighbors"] = []
        if (
            "parameters" not in neighbor.routing["bgp"]
            or not neighbor.routing["bgp"]["parameters"]
        ):
            neighbor.routing["bgp"]["parameters"] = {}
        if (
            "router-as" not in neighbor.routing["bgp"]["parameters"]
            or not neighbor.routing["bgp"]["parameters"]["router-as"]
        ):
            raise RuntimeError(
                "Trying to establish bgp connection without a set"
                f" AS on neighbor {neighbor.name}"
            )

        v_as = self.routing["bgp"]["parameters"]["router-as"]
        n_as = neighbor.routing["bgp"]["parameters"]["router-as"]

        try:
            v_ip = None
            n_ip = None
            for i in self.interfaces.interfaces:
                if i["switch"] == switch:
                    v_ip = i["address"]
                    break
            for i in neighbor.interfaces.interfaces:
                if i["switch"] == neighbor_switch:
                    n_ip = i["address"]
                    break
            if not v_ip or not n_ip:
                raise RuntimeError(
                    f"Unable to find IP address. Have {v_ip!s} for self "
                    f"and {n_ip!s} for neighbor."
                )
        except Exception:
            self.log.exception("Unable to get interfaces for BGP connection")
            raise

        self.routing["bgp"]["neighbors"].append({"remote-as": n_as, "address": n_ip})
        neighbor.routing["bgp"]["neighbors"].append(
            {"remote-as": v_as, "address": v_ip}
        )

    def enable_dhcp_server(self, switch):
        """Enable a DHCP server listening on the interface to the specified Switch.

        Args:
            switch (base_objects.Switch): The switch representing the network
                which will have DHCP.
        """
        for iface in self.interfaces.interfaces:
            if iface["switch"] == switch:
                iface["dhcp"] = True
