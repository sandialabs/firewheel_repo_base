from netaddr import EUI, mac_unix_expanded
from base_objects import VMEndpoint

from firewheel.control.experiment_graph import AbstractPlugin


class CreateMACAddrs(AbstractPlugin):
    """
    This plugin ensures that each VM has a unique MAC address by keeping a global
    counter and incrementing it. For simplicity, this plugin uses :py:class:`netaddr.EUI`.
    More information can be found
    `in the netaddr documentation <https://netaddr.readthedocs.io/en/latest/tutorial_02.html>`_.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the global MAC counter and the set of existing MAC addresses.

        Args:
            *args: Arguments are not used for this object.
            **kwargs: Keyword arguments are not used for this object.
        """
        super().__init__(*args, **kwargs)

        self.starting_mac = 1
        self.current_mac = self.starting_mac
        self.existing_macs = set()

    def _increment_mac(self):
        """
        Increments the current MAC address by one and does wrap around checking.
        """
        self.current_mac += 1
        if self.current_mac > 0xFFFFFFFFFFFF:
            # Ran out of addresses, wrap around
            self.current_mac = 1

    def _convert_int_to_mac(self, numeric):
        """
        Converts an integer to a MAC string in the format: ``"xx:xx:xx:xx:xx:xx"``.

        Args:
            numeric (int): The integer to have converted to the MAC representation.

        Returns:
            str: MAC address string in the format: ``"xx:xx:xx:xx:xx:xx"``.
        """
        assert isinstance(numeric, int)
        mac = EUI(numeric, version=48)

        # Set the representation to the standard MAC 'xx:xx:xx:xx:xx:xx' format.
        mac.dialect = mac_unix_expanded
        return str(mac)

    def get_unique_mac(self):
        """
        Make sure that the current MAC hasn't been assigned outside of
        this plugin. If it has, increment the MAC and check again.

        Returns:
            str: A MAC address that (at this point in the graph walk) is unique.
        """
        # Make sure the current MAC hasn't already been assigned outside of
        # this plugin.
        while self._convert_int_to_mac(self.current_mac) in self.existing_macs:
            self._increment_mac()
        mac = self.current_mac
        self._increment_mac()
        return self._convert_int_to_mac(mac)

    def _find_existing_macs(self):
        """
        Iterate over the graph and add any existing MAC addresses to the
        global set.
        """
        for vm in self.g.get_vertices():
            if vm.is_decorated_by(VMEndpoint):
                try:
                    for iface in vm.interfaces.interfaces:
                        if "mac" in iface:
                            self.existing_macs.add(iface["mac"])
                except AttributeError:
                    pass

    def _assign_macs(self):
        """
        Iterate over the graph and add a MAC address for each interface that
        does not have one yet.
        """
        for vm in self.g.get_vertices():
            if vm.is_decorated_by(VMEndpoint):
                try:
                    for iface in vm.interfaces.interfaces:
                        if "mac" not in iface:
                            iface["mac"] = self.get_unique_mac()
                            assert len(iface["mac"]) == 17
                            self.existing_macs.add(iface["mac"])
                except AttributeError:
                    self.log.warning(
                        'No interfaces found on VM "%s". Cannot create any mac addresses.',
                        vm.name,
                    )

    def run(self, mac_addr_start=""):
        """
        See the starting MAC address and call subsequent functions which ensure that
        all VM interfaces have a unique MAC address.

        Args:
            mac_addr_start (str, optional): A seed value for the initial MAC address.
                Must be convertible to :obj:`int`. Defaults to ``""``.

        Raises:
            ValueError: If the passed in value is not valid.
        """
        if mac_addr_start:
            try:
                self.mac_addr_start = int(mac_addr_start, 0)
                if self.mac_addr_start < 1 or self.mac_addr_start > 0xFFFFFFFFFFFF:
                    raise ValueError("Specified starting MAC address out of range.")
            except ValueError:
                self.log.critical(
                    "Invalid starting MAC address. "
                    "Must be an integer in the range 1-0xFFFFFFFFFFFF."
                )
                raise

        # Walk the vertices to find and note any existing MACs.
        # A full walk here is needed so we know the first address we assign
        # is unique.
        self._find_existing_macs()
        self.log.info("Found %d existing mac addresses.", len(self.existing_macs))

        # Now begin assigning new MACs where needed.
        self._assign_macs()
        self.log.info(
            "After creating macs, know of %d mac addresses.", len(self.existing_macs)
        )
