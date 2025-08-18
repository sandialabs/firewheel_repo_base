import os
import sys
import json
import math
import pickle

import netaddr
from rich.console import Console

from firewheel.control.experiment_graph import Edge
from firewheel.vm_resource_manager.schedule_entry import ScheduleEntry


class AbstractWindowsEndpoint:
    """
    This class is used to identify the generic OS for a
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` which can be useful
    for knowing what kinds of VM Resources (VMRs) can run on the system. Decoration with this
    object is mutually exclusive from being decorated with
    :py:class:`base_objects.AbstractUnixEndpoint`.
    """

    def __init__(self):
        """Check for possible conflicts.

        Raises:
            TypeError: If the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
                is already decorated with :py:class:`base_objects.AbstractUnixEndpoint`.
        """
        if self.is_decorated_by(AbstractUnixEndpoint):
            raise TypeError(
                "AbstractUnixEndpoint cannot be decorated with AbstractWindowsEndpoint!"
            )


class AbstractUnixEndpoint:
    """
    This class is used to identify the generic operating system (OS) for a
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` which can be useful
    for knowing what kinds of VMRs can run on the system. Decoration with this
    object is mutually exclusive from being decorated with
    :py:class:`base_objects.AbstractWindowsEndpoint`.
    """

    def __init__(self):
        """Check for possible conflicts.

        Raises:
            TypeError: If the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
                is already decorated with :py:class:`base_objects.AbstractWindowsEndpoint`.
        """
        if self.is_decorated_by(AbstractWindowsEndpoint):
            raise TypeError(
                "AbstractWindowsEndpoint cannot be decorated with AbstractUnixEndpoint!"
            )


class AbstractServerEndpoint:
    """
    This class is used to identify the generic type ``{server, desktop}`` for a
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
    which can be useful for knowing what kinds of VMRs can run on the system.
    Decoration with this object is mutually exclusive from being decorated with
    :py:class:`base_objects.AbstractDesktopEndpoint`.
    """

    def __init__(self):
        """Check for possible conflicts.

        Raises:
            TypeError: If the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
                is already decorated with :py:class:`base_objects.AbstractDesktopEndpoint`.
        """
        if self.is_decorated_by(AbstractDesktopEndpoint):
            raise TypeError(
                "AbstractDesktopEndpoint cannot be decorated with AbstractServerEndpoint!"
            )


class AbstractDesktopEndpoint:
    """
    This class is used to identify the generic type ``{server, desktop}`` for a
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
    which can be useful for knowing what kinds of VMRs can run on the system.
    Decoration with this object is mutually exclusive from being decorated with
    :py:class:`base_objects.AbstractServerEndpoint`.
    """

    def __init__(self):
        """Check for possible conflicts.

        Raises:
            TypeError: If the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
                is already decorated with :py:class:`base_objects.AbstractServerEndpoint`.
        """
        if self.is_decorated_by(AbstractServerEndpoint):
            raise TypeError(
                "AbstractServerEndpoint cannot be decorated with AbstractDesktopEndpoint!"
            )


class FalseEdge:
    """This class is intended to indicate that an
    :py:class:`Edge <firewheel.control.experiment_graph.Edge>` is a "false"
    :py:class:`Edge <firewheel.control.experiment_graph.Edge>` in the graph.
    That is, the :py:class:`Edge <firewheel.control.experiment_graph.Edge>`
    exists in the graph but won't be used when the graph is instantiated.
    This is useful when using complex graph algorithms.
    """

    def __init__(self):
        """Creates ``self.false`` and sets it to :py:data:`True`."""
        self.false = True


class QoSEdge:
    """
    This class can be used to add quality of service (QoS) attributes to a given
    :py:class:`Edge <firewheel.control.experiment_graph.Edge>`. It is important to note
    that these QoS constraints are only applied directionally
    on the egress side (e.g. transmitting) due to a limitation in
    `minimega <https://sandia-minimega.github.io/#header_5.47>`_.
    """

    def __init__(self):
        """
        Initialize the ``qos`` property for the
        :py:class:`Edge <firewheel.control.experiment_graph.Edge>`.
        """
        self.qos = {}

    def add_delay(self, delay):
        """
        Set the :py:class:`Edge's <firewheel.control.experiment_graph.Edge>`
        egress delay (e.g. latency).

        Note:
            For emulation-based models, due to limitations of
            `tc <https://linux.die.net/man/8/tc>`_ you can only add rate OR loss/delay to a VM.
            Enabling loss or delay will disable rate and vice versa.

        Args:
            delay (str): The amount of egress delay to add for the link. This should be
                formatted like ``<delay><unit of delay>``. For example, ``100ms``.
        """
        self.qos["delay"] = delay

    def add_rate_limit(self, rate, unit=None):
        """
        Set the :py:class:`Edge's <firewheel.control.experiment_graph.Edge>`
        egress rate (e.g. bandwidth).
        The rate is set as a multiple of bits **not** bytes.
        That is, a rate of ``1 kbit`` would equal 1000 bits, not 1000 bytes.
        For bytes, multiply the rate by 8 (e.g. 64 KBytes = 8 * 64 = 512 kbit).

        Note:
            For emulation-based models, due to limitations of
            `tc <https://linux.die.net/man/8/tc>`_ you can only add rate OR loss/delay to a VM.
            Enabling loss or delay will disable rate and vice versa.

        Args:
            rate (int): The requested maximum bandwidth as a multiple of bits.
            unit (str): The bandwidth unit (one of ``{"kbit", "mbit", "gbit"}``).
                Defaults to ``"mbit"``.

        Raises:
            TypeError: If the passed in unit is invalid.
        """
        unit_types = ["kbit", "mbit", "gbit"]
        if unit is None:
            unit = "mbit"
        elif unit not in unit_types:
            raise TypeError(f"Invalid rate type. Expected one of: {unit_types}")
        self.qos["rate"] = (rate, unit)

    def add_packet_loss_percent(self, packet_loss):
        """
        Set the :py:class:`Edge's <firewheel.control.experiment_graph.Edge>`
        amount of egress packet loss (as a percentage).

        Note:
            For emulation-based models, due to limitations of
            `tc <https://linux.die.net/man/8/tc>`_ you can only add rate OR loss/delay to a VM.
            Enabling loss or delay will disable rate and vice versa.

        Args:
            packet_loss (int): The packet loss as a percentage. For example,
                ``packet_loss = 25`` is 25% packet loss.
        """
        self.qos["loss"] = packet_loss


class Switch:
    """Decorate a :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` as a Switch.
    Switches represent a `Layer 2 <https://en.wikipedia.org/wiki/Data_link_layer>`_ network.
    VMs will appear like they are connected directly to a
    `network switch <https://en.wikipedia.org/wiki/Network_switch>`_. In order to connect
    two (or more) VMs, users must first create a switch to facilitate connection.

    Switches will not appear as VMs, but rather as Open vSwitch bridges. To use a physical VM
    as a "switch" users should refer to :ref:`layer2.ovs_mc` or :ref:`layer2.tap_mc`.
    """

    def __init__(self, name=None):
        """
        Initialize the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
        as ``type=switch``.

        Args:
            name (str, optional): The name of the switch. Defaults to :py:data:`None`.
                This is typically set at the time of
                :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` creation.

        Raises:
            NameError: If the switch doesn't have a name.
        """
        self.type = "switch"

        self.name = getattr(self, "name", name)
        if self.name is None:
            raise NameError("Name must be specified for switch!")


class VmResourceSchedule:
    """This object defines a VM resource schedule which will be used to keep track
    of all scheduled VM resources for a given VM. It provides methods to add new
    :py:class:`Schedule entries <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry>`,
    retrieve the :ref:`vm-resource-schedule`, and serialize the schedule for use by the
    :ref:`vm-resource-handler`.
    """

    def __init__(self):
        """
        Create a new list to store
        :py:class:`schedule entries <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry>`.
        """
        self.schedule_list = []

    def add_vm_resource(self, new_entry):
        """Add a new
        :py:class:`ScheduleEntry <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry>`
        to the list.

        Args:
            new_entry (firewheel.vm_resource_manager.schedule_entry.ScheduleEntry): The new VMR
                schedule entry. This type can also be any sub class of
                :py:class:`firewheel.vm_resource_manager.schedule_entry.ScheduleEntry`.

        Raises:
            ValueError: If ``new_entry`` is not a subclass of
                :py:class:`firewheel.vm_resource_manager.schedule_entry.ScheduleEntry`.
        """
        if not issubclass(type(new_entry), ScheduleEntry):
            raise ValueError(
                "Can only add children of ScheduleEntry to the VM resource schedule."
            )
        self.schedule_list.append(new_entry)

    def get_schedule(self):
        """Retrieve the schedule, but first walk through the schedule entries
        looking for any that place ``content`` into a VM. Because the ``content``
        field can actually be a callable (see
        :py:class:`DropContentScheduleEntry <base_objects.DropContentScheduleEntry>` and
        :py:meth:`VMEndpoint's drop_content() <base_objects.VMEndpoint.drop_content>` for
        more details), this method will check to see if any ``content`` is callable, and if so,
        invoke it in order to generate the string-based content to be used by the VM resource.
        Lastly, this method modifies all
        :py:class:`ScheduleEntries <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry>`
        to ensure that their class is a
        :py:class:`ScheduleEntry <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry>`
        rather than any subclass type. This facilitates the :ref:`vm-resource-handler` to unpickle
        the objects correctly.

        Returns:
            list: The full list of schedule entries.
        """
        # If the schedule is being asked for then walk through the
        # schedule entries looking for content to be loaded into a VM.
        # If the content is actually a callable, then call it in order
        # to generate the string content to be used by the vm_resource.
        for entry in self.schedule_list:
            try:
                for data in entry.data:
                    if "content" in data and callable(data["content"]):
                        # Replace the content value with the string that results
                        # from using the callback that was passed to the
                        # schedule entry
                        data["content"] = data["content"]()
            except AttributeError:
                continue

            # Flip all schedule entries back to the parent class
            # so the resource handler can unpickle them
            entry.__class__ = ScheduleEntry

        return self.schedule_list

    def get_serialized_schedule(self):
        """Serialize the schedule by pickling each schedule entry and then returning
        a tuple of pickled schedule entries.

        Returns:
            tuple: A tuple of pickled schedule entries.
        """
        return (pickle.dumps(entry) for entry in self.schedule_list)

    def __str__(self):
        """Create a human readable string representation of this object.

        Returns:
            str: A string representation of :py:class:`base_objects.VmResourceSchedule`.
        """
        ret = "[\n"

        for entry in self.get_schedule():
            ret += f"{entry!s},\n"
        ret += "]"

        return ret


class Interfaces:
    """This object represents a VMs network interfaces.
    It largely consists of a list of interfaces which are a dictionary
    of interface-related properties.
    """

    def __init__(self, prefix="eth"):
        """Initialize the list of interfaces.

        Args:
            prefix (str, optional): The default name of the interface
                (e.g. ``ens``, ``eth``, etc.). Defaults to ``"eth"``.
        """
        self.interfaces = []
        self.prefix = prefix
        self.counter = 0

    def add_interface(
        self,
        address,
        netmask,
        qos=None,
        switch=None,
        control_network=False,
        l2_connection=False,
    ):
        """Add a new interface to the list of interfaces.

        Args:
            address (str or netaddr.IPAddress): The IP address for the interface. An IP address
                is not strictly required in the case where a new interface is needed but it is
                not a Layer-3 connection.
            netmask (str or netaddr.IPAddress): The netmask for the connecting interface.
                The netmask can either be in dotted decimal or CIDR (without the slash) notation.
                That is, both ``"255.255.255.0"`` and ``"24"`` would represent the same netmask.
            qos (dict, optional): A dictionary of QoS-specific parameters. It can include any
                of the following keys: ``{"loss", "delay", "rate"}``. Defaults to :py:data:`None`.
            switch (base_objects.Switch, optional): The switch which will be connected to
                the interface. Defaults to :py:data:`None`.
            control_network (bool, optional): Identify if the interface will be part of the
                control network. Defaults to :py:data:`False`.
            l2_connection (bool): Identify if the interface should be a Layer-2 interface.
                Defaults to :py:data:`False`.

        Returns:
            dict: A new interface dictionary containing the interface name,
            address, netmask, network, switch, and QoS dictionary.
        """
        name = f"{self.prefix}{self.counter}"
        # If this is only a L2 link then the address might
        # not be populated
        if address:
            address = netaddr.IPAddress(address)

            # We can improve performance if we pass in a tuple to create the
            # netaddr.IPNetwork. The tuple is the integer value for the IPAddress
            # and the Integer CIDR netmask.
            if isinstance(netmask, netaddr.IPAddress):
                netmask = netmask.netmask_bits()
            else:
                try:
                    netmask = int(netmask)
                except ValueError:
                    netmask = netaddr.IPAddress(netmask)
                    netmask = netmask.netmask_bits()
            network = netaddr.IPNetwork((address.value, netmask))
        else:
            network = None
        qos_dict = {"loss": None, "delay": None, "rate": None}
        if qos:
            qos_dict.update(qos)

        interface = {
            "name": name,
            "address": address,
            "netmask": netmask,
            "network": network,
            "switch": switch,
            "qos": qos_dict,
            "control_network": control_network,
            "l2_connection": l2_connection,
        }

        if control_network:
            self.interfaces.insert(0, interface)
        else:
            self.interfaces.append(interface)
        self.counter += 1
        return interface

    def del_interface(self, name):
        """Delete an interface based on the Interfaces name.

        Args:
            name (str): The name of an interface.
        """
        self.interfaces = [
            interface
            for interface in self.interfaces
            if "name" in interface and interface["name"] != name
        ]

    def get_interface(self, name):
        """Retrieve the interface dictionary with the given name.

        Args:
            name (str): The name of the interface to return.

        Returns:
            dict: The requested interface dictionary.
        """
        for interface in self.interfaces:
            if "name" in interface and interface["name"] == name:
                return interface
        return None

    def rekey_interfaces(self):
        """A method to re-key the list of interfaces.
        That is, assuming the counter is 0, rename the interfaces in the list.
        This is useful after deleting an interface.
        """
        tmp_list = []
        counter = 0
        for interface in self.interfaces:
            tmp_int = interface
            tmp_int["name"] = f"{self.prefix}{counter}"
            tmp_list.append(tmp_int)
            counter += 1
        self.interfaces = tmp_list
        self.counter = counter

    def __str__(self):
        """
        A custom string method for Interface Objects.

        Returns:
            str: A string representation of an :py:class:`base_objects.Interfaces`.
        """
        ret = []
        for interface in self.interfaces:
            new_int = dict(interface)
            new_int["address"] = str(new_int["address"])
            new_int["netmask"] = str(new_int["netmask"])
            new_int["network"] = str(new_int["network"])
            new_int["switch"] = new_int["switch"].name
            ret.append(new_int)
        return json.dumps(ret)


class VMEndpoint:
    """This class is the base class for all VM-based model components.
    It creates any necessary VM-based attributes and adds a
    :py:class:`base_objects.VmResourceSchedule` to the
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.

    This class also provides methods which are useful for all VM objects.
    """

    def __init__(self, name=None):
        """Initialize the :py:class:`VMEndpoint` and its associated attributes.

        Args:
            name (str, optional): The name of the VM. This can also be set on
                :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` creation.
                Defaults to :py:data:`None`.

        Raises:
            NameError: The :py:class:`VMEndpoint` does not have a name.
            ValueError: The name contains illegal characters (e.g. underscores, spaces, or commas).

        Attributes:
            name (str): Every VM must have a unique name. Names must follow conventions
                of valid hostnames (e.g. cannot contain underscores, spaces, or commas).
            vm (dict): A dictionary of VM-related properties. These will be used by other
                model components to instantiate the graph (e.g.
                :ref:`minimega.parse_experiment_graph_mc`). Most of these properties will be
                filled out be other model components either explicitly, or if not defined, a default
                value is provided. Common VM properties include

                .. code-block:: python
                    :caption: An example VM property dictionary.

                    {
                        'image_store': {            # Location of where minimega should find the images
                            'path': '/tmp/minimega/files/images',
                            'name': 'images'
                        },
                        'architecture': 'x86_64',   # The CPU architecture
                        'vcpu': {
                            'model': 'qemu64',      # The QEMU vCPU model number
                            'sockets': 1,           # The number of vCPU sockets
                            'cores': 1,             # The number of vCPU cores
                            'threads': 1            # The number of vCPU threads
                        },
                        'mem': 256,                 # The amount of memory for the VM
                        'drives': [                 # Information about the disk image
                            {
                                'db_path': 'ubuntu-16.04.4-server-amd64.qcow2.xz',
                                'file': 'ubuntu-16.04.4-server-amd64.qcow2',
                                'interface': 'virtio',
                                'cache': 'writeback'
                            }
                        ],
                        'vga': 'std',               # The type of VGA display to use
                        'image': 'ubuntu1604server' # A general image name.
                    }

            type (str): The type of the VM. It should be one of ``{"host", "router", "switch"}``.
                Defaults to ``"host"``.
            coschedule (int): The number of other VMs allowed to be schedule on the
                same host as this VM. A value of ``0`` means this VM will have its own
                host, and ``-1`` (default) means there is no limit.
            vm_resource_schedule (base_objects.VmResourceSchedule): A new VMR schedule for the
                :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
        """
        self.name = getattr(self, "name", name)
        if self.name is None:
            raise NameError("VMEndpoint must have a name!")

        if "_" in self.name or " " in self.name or "," in self.name:
            raise ValueError(
                f"Cannot set VM name: {self.name}.\n"
                "VM names must not contain underscores, spaces, or commas "
                "since those characters are not valid in hostnames!"
            )

        self.vm = getattr(self, "vm", {})
        self.type = getattr(self, "type", "host")

        # Set the coschedule attribute, how many VMs are allowed to be on the
        # same host as this VM. -1 means unlimited, 0 means the VM will get its
        # own host
        self.coschedule = getattr(self, "coschedule", -1)

        self.vm_resource_schedule = VmResourceSchedule()

    def set_image(self, image_name):
        """
        Add an image property to the VM dictionary.
        The name of the image is used by :ref:`minimega.resolve_vm_images_mc`
        to verify that the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` has
        a bootable image. This property should be set by all MCs which add an image to
        a given model component.

        .. seealso::

            See the :ref:`image-creation-tutorial` for more details.

        Args:
            image_name (str): A generic name for the VM's image (e.g. ``"ubuntu1604server"``).
        """
        try:
            self.vm["image"] = image_name
        except AttributeError:
            self.vm = {"image": image_name}

    def add_vm_resource(
        self, start_time, vm_resource_name, dynamic_arg=None, static_arg=None
    ):
        """
        This method adds a :py:class:`base_objects.VmResourceScheduleEntry` object to a
        :py:class:`Vertex's <firewheel.control.experiment_graph.Vertex>`
        :py:class:`base_objects.VmResourceSchedule`. This provides backwards compatibility for
        VMRs that were written for pre-2.0 versions of FIREWHEEL.

        For VMRs which use this method, they should expect to be passed three file names:
        ``dynamic``, ``static``, and ``reboot``. The first two files contain the content described
        in the ``dynamic_arg`` and ``static_arg``. Finally, the VMR gets passed the path to a
        ``reboot`` file as their last argument on the command line. If the VMR creates that
        ``reboot`` file then the *VM Resource Manager* will restart the VM upon completion of
        the VMR (see :ref:`vmr-rebooting` for more details).

        Args:
            start_time (int): The start time for the VMR. (See :ref:`start-time` for more details).
            vm_resource_name (str): The name of the VMR that should be executed.
            dynamic_arg (str, optional): Any is content that is dependent on the
                configuration of the graph which should be passed to the VMR.
                This information can change from experiment to experiment.
                It generally takes the form of an ASCII string or a serialized object
                (i.e. a dictionary dumped into JSON format via :py:func:`json.dumps`).
                This content gets written into a file inside the VM and the filename is then
                passed to the VMR as the first command line parameter.
                Defaults to :py:data:`None`. However if it is not specified, an empty
                ``dynamic`` file path is still passed to the VMR.
            static_arg (str, optional): The name of a file that needs to be loaded into the VM.
                That filename is then passed to the VMR as its second command line option.
                Static content generally takes the form of an installer or other binary blob
                that the VMR requires in order to accomplish its purpose.
                This is something that does not change regardless of the experiment that
                is using it. Defaults to :py:data:`None`. However if it is not specified, an
                empty ``static`` file path is still passed to the VMR.

        Returns:
            base_objects.VmResourceScheduleEntry: The newly created schedule entry.

        Examples:
            The following is a skeleton of an VMR which can use this method.
            It should be noted that there is no requirement that the VMR is a Python script.
            It can be any executable as long as it accepts and understands the three command line
            arguments explained above.

            .. code-block:: python
                :caption: Example VMR which can be used with the ``add_vm_resource()`` method.
                :linenos:

                #!/usr/bin/env python3
                import sys

                class VmResource(object):

                    def __init_(self, dynamic_content_filename,
                            static_filename, reboot_filename):
                        self.dynamic_content_filename = dynamic_content_filename
                        self.static_filename = static_filename
                        self.reboot_filename = reboot_filename

                    def run(self):
                        # VmResource logic implemented here
                        return 0

                if __name__ == '__main__':
                    if len(sys.argv) != 4:
                        print("VmResource did not receive expected arguments")
                        sys.exit(1)

                    dynamic_content_filename = sys.argv[1]
                    static_filename = sys.argv[2]
                    reboot_file = sys.argv[3]

                    vm_resource = VmResource(dynamic_content_filename, static_filename, reboot_file)
                    # Return with the result of the run method
                    sys.exit(vm_resource.run())

            Scheduling this example VMR on a
            :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`
            only requires that we pass the required information to the ``add_vm_resource()``
            method for the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
            In this particular
            case, we're assuming that the example VMR above is in a file called
            ``ex_vm_resource.py`` and the requirements in :ref:`using-vm-resources` have been
            satisfied. Since this is just a example, it doesn't use the arguments passed in, so
            there is no need to include them in the call to ``add_vm_resource()``.

            .. code-block:: python

                host = Vertex(self.g, "host")
                host.decorate(VMEndpoint)
                host.add_vm_resource(-10, 'ex_vm_resource.py')

            This will run the example VMR at configuration time ``-10`` and it will do nothing
            but return ``0``.
        """
        # This is the default vm_resource
        vm_resource = VmResourceScheduleEntry(
            vm_resource_name, start_time, dynamic_arg, static_arg
        )
        self.vm_resource_schedule.add_vm_resource(vm_resource)
        return vm_resource

    def drop_content(
        self, start_time, location, content, executable=False, preload=True
    ):
        r"""
        This method is intended to take any string and write it to a specified
        location on a VM.
        This method adds a :py:class:`base_objects.DropContentScheduleEntry` object to a
        :py:class:`Vertex's <firewheel.control.experiment_graph.Vertex>`
        :py:class:`base_objects.VmResourceSchedule`.

        There are some use cases where ``content`` needs to be written to a file inside a VM, but
        the ``content`` can not be generated until all topology changes to the graph have been
        completed. To handle this situation, ``content`` can point to a callback function that
        returns a string instead of containing the string directly.

        Router configuration is a good example of this. The router needs to look at the networks
        that are connected to it and its routing peers in order to know what must be included in
        its configuration. Since a router can be created in one model component, but the topology
        can change in subsequent model components, the router does not have all its required
        information at creation time. In the case of the ``VyOS`` router, its plugin drops a
        configuration file where the ``content`` argument points at a function that will return
        a string.

        All callback functions are executed as part of the
        :py:meth:`base_objects.VmResourceSchedule.get_schedule` method (see
        :ref:`vm-resource-schedule`). The :ref:`vm_resource.schedule_mc` model component calls
        :py:meth:`base_objects.VmResourceSchedule.get_schedule` for each
        :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` in the graph.

        Args:
            start_time (int): The schedule time (positive or negative) of
                when to perform the content write. (See :ref:`start-time` for more details).
            location (str): The absolute Unix-style path (including filename) on the
                VM to write the content. For example, to write content to
                ``C:\Users\Administrator\Desktop\test.txt`` inside a Windows VM, the ``location``
                would need to be ``/Users/Administrator/Documents/test.txt``.
            content (str): The content to write out. This can be either a string, a
                serialized object (via :py:mod:`json` or :py:mod:`pickle`), or a function pointer.
                Function pointers can be passed in the content field for delayed content generation
                (see the examples below).
            executable (bool, optional): Should the file be made executable.
                This flag is ignored for Windows VMs. Defaults to :py:data:`False`.
            preload (bool, optional): If set, instead of dropping the content directly
                into ``location`` at ``start_time``, the content will be preloaded into a
                temporary location prior to any schedule entries running and then moved
                to ``location`` at ``start_time``. Defaults to :py:data:`True`.
                This is particularly useful for placing files into directories which will be
                created by another VMR.

        Returns:
            base_objects.DropContentScheduleEntry: The newly created schedule entry.

        Examples:
            **Drop Content Example with a Callback Function**

            The following is an example of using ``drop_content()`` with a callback function.
            This is taken from the :ref:`vyos_mc` model component.
            The callback function is implemented in the model component and is called
            ``self._configure_vyos``. It returns a string containing the configuration file
            for the router. That string is then written to
            ``/opt/vyatta/etc/config/firewheel-config.sh``.

            .. code-block:: python

                # Path to write the configuration file inside the router
                configuration_location = '/opt/vyatta/etc/config/firewheel-config.sh'

                # Drop the configuration file on the router.
                # This is done by supplying a callback to the ScheduleEntry.
                # This will be called when the schedule is being generated to be uploaded
                self.drop_content(-100, configuration_location, self._configure_vyos,
                    executable=True)

            **Drop Content Example with a String**

            The following example is a bit more straightforward.
            In this case the ``drop_content()`` function is provided a string to be written to a
            file in the VM. Since this example is using a Windows VM, the ``location`` for the
            content is a Unix-style path that translates to ``C:\Users\User\Desktop\hello.txt``
            in the VM.

            .. code-block:: python

                host = Vertex(self.g, "host")
                host.decorate(WindowsHost)

                content = f"Hello World! My hostname is: {self.name}"
                host.drop_content(-200, "/Users/User/Desktop/hello.txt", content)
        """
        if not os.path.splitext(location)[-1]:
            self.log.warning(
                "The drop_content location '%s' does not have "
                "a file extension. The drop_content method requires "
                "that you provide the full destination path to the "
                "file (including file name).",
                location,
            )
        if preload:
            if self.is_decorated_by(AbstractWindowsEndpoint):
                preload_move_cmd = "move"
            else:
                preload_move_cmd = "mv"
        else:
            preload_move_cmd = None
        vm_resource = DropContentScheduleEntry(
            start_time, location, content, executable, preload_move_cmd
        )
        self.vm_resource_schedule.add_vm_resource(vm_resource)
        return vm_resource

    def drop_file(self, start_time, location, filename, executable=False, preload=True):
        """
        This method is intended to take a file and load it on to a VM at a
        specified location.
        This method adds a :py:class:`base_objects.DropFileScheduleEntry` object to a
        :py:class:`Vertex's <firewheel.control.experiment_graph.Vertex>`
        :py:class:`base_objects.VmResourceSchedule`.

        Note:
            If the file happens to already exist on the VM, it will be overwritten.

        Args:
            start_time (int): The schedule time (positive or negative) of
                when to execute the dropping of the file.
                (See :ref:`start-time` for more details).
            location (str): The absolute path (including filename) on the
                VM to write the file.
            filename (str): The local name of the file (i.e. the name of
                the file within the model component).
                Since the file must live in the model component, the ``filename`` is not a path.
                Therefore, it should not include any directories in its name.
            executable (bool, optional): Should the file have its executable flag set.
                This flag is ignored for Windows VMs. Defaults to :py:data:`False`.
            preload (bool, optional): If set, instead of dropping the file directly
                into ``location`` at ``start_time``, the file will be preloaded into a
                temporary location prior to any schedule entries running and then moved
                to ``location`` at ``start_time``. Defaults to :py:data:`True`.
                This is particularly useful for placing files into directories which will be
                created by another VMR.

        Returns:
            base_objects.DropFileScheduleEntry: The newly created schedule entry.

        Examples:
            The following example shows dropping a static file on a VM.
            In this case, a ``vimrc`` file is being loaded onto a VM.
            This example assumes that the model component containing this code has declared
            ``vimrc`` as a VMR in its ``MANIFEST`` file and the ``vimrc`` file is located
            within the model component's directory.

            .. code-block:: python

                host = Vertex(self.g, "host")
                host.decorate(Ubuntu1604Server)
                host.drop_file(-200, "/home/ubuntu/.vimrc", "vimrc")
        """
        if not os.path.splitext(location)[-1]:
            self.log.warning(
                "The drop_file location '%s' for file %s does not have "
                "a file extension. The drop_file method requires "
                "that you provide the full destination path to the "
                "file (including file name).",
                location,
                filename,
            )
        if preload:
            if self.is_decorated_by(AbstractWindowsEndpoint):
                preload_move_cmd = "move"
            else:
                preload_move_cmd = "mv"
        else:
            preload_move_cmd = None
        vm_resource = DropFileScheduleEntry(
            start_time, location, filename, executable, preload_move_cmd
        )
        self.vm_resource_schedule.add_vm_resource(vm_resource)
        return vm_resource

    def run_executable(self, start_time, program, arguments=None, vm_resource=False):
        r"""
        This method allows a user to specify an executable to run and the arguments to pass to it
        on the command line. It supports both programs that are natively included in the VM
        (e.g. ``/sbin/ip`` or ``C:\windows\system32\ipconfig.exe``) as well as VM resources.
        This method adds a :py:class:`base_objects.RunExecutableScheduleEntry` object to a
        :py:class:`Vertex's <firewheel.control.experiment_graph.Vertex>`
        :py:class:`base_objects.VmResourceSchedule`.

        Args:
            start_time (int): The schedule time (positive or negative) of when to execute
                the specified program. (See :ref:`start-time` for more details).
            program (str): The name of the program or script to run.
                In general, it's safer to provide absolute paths for program
                names instead of relying on the environment of the VM to resolve
                the name.
            arguments (str or list, optional): This field allows a user to provide
                arguments for the program as either a single string or a list of strings.
                These get passed to the program on the command line. Defaults to :py:data:`None`.
            vm_resource (bool, optional): This parameter indicates if program is
                the name of a script that needs to be loaded on to the VM before
                execution. If ``vm_resource`` is :py:data:`True` then the specified program
                name is assumed to be the local filename of the file
                (i.e. not the full path, just the filename) to load on to the VM.
                That is, the file will be located within a model component.
                Defaults to :py:data:`False`.

        Returns:
            base_objects.RunExecutableScheduleEntry: The newly created schedule entry.

        Examples:
            **Native Executable Example**

            To run a program that is native to the VM, specify the Unix-style absolute path to
            the executable and optionally include arguments. For example, the ``ipconfig``
            executable on a Windows VM is located at ``C:\Windows\system32\ipconfig.exe``.
            The required Unix-style path for ``ipconfig`` would be
            ``/windows/system32/ipconfig.exe``. The path being absolute is not strictly required,
            but it is generally safer than assuming the program is part of the VM's ``PATH``.
            For example, the following runs the ``hostname`` command on a Linux VM at negative
            time ``-100``, passing in the name of the host as an argument.

            .. code-block:: python

                host = Vertex(self.g, "host")
                host.decorate(LinuxHost)
                host.run_executable(-100, '/sbin/hostname', host.name)


            **VM Resource Executable Example**

            Running a VMR file on a VM where arguments can be passed to it via the command line
            is very similar. The ``program`` needs to be the name of the VMR file and the
            ``vm_resource`` flag needs to be set to :py:data:`True`. For example, instead of calling
            the ``hostname`` command directly, let's run a VMR that calls the ``hostname`` command
            and adds the hostname to the ``/etc/hosts`` file. The VMR file will be called
            ``set_hostname.sh``:

            .. code-block:: bash

                echo $1 > /etc/hostname
                sed -i '/127.0.0.1/127.0.0.1    localhost '$1 /etc/hosts

            Standard VMR requirements for model components apply (see :ref:`using-vm-resources`).
            Executing the ``set_hostname.sh`` VMR on a
            :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` at time ``-100``
            passing in the name of the host as an argument is as follows:

            .. code-block:: python

                host = Vertex(self.g, "host")
                host.decorate(LinuxHost)
                host.run_executable(-100, 'set_hostname.sh', host.name, vm_resource=True)
        """
        exec_vm_resource = RunExecutableScheduleEntry(
            start_time, program, arguments, vm_resource
        )
        self.vm_resource_schedule.add_vm_resource(exec_vm_resource)
        return exec_vm_resource

    def file_transfer(self, location, interval=60, start_time=1, destination=None):
        """
        This method facilitates pulling a file or directory off of
        a VM at a regular time interval. If the VM is a Linux host then files only get
        pulled when they have changed (after the initial pull). If the VM is a
        Windows host then the file/directory will get pulled at every interval.

        Note:
            If specifying a destination, the FIREWHEEL group (if any) must have
            permissions to modify and write to that directory. See the
            :ref:`config-system` configuration options to add FIREWHEEL group permissions.

        Args:
            location (str): Absolute path inside the VM to the file or directory
                to be monitored and pulled off the VM.
            interval (int, optional): Time interval in seconds to pull
                file or directory from the VM.
            start_time (int, optional): The schedule time to transfer
                the file or directory out of the VM.
            destination (str, optional): Absolute path on compute node of the
                directory where transferred files are to be placed:
                ``<destination>/<vm_name>/<location>``. If no destination is provided,
                files will be written to ``<logging.root_dir>/transfers/``. See
                :py:meth:`_transfer_data <firewheel.vm_resource_manager.vm_resource_handler.VMResourceHandler._transfer_data>`
                for more details.

        Returns:
            base_objects.FileTransferScheduleEntry: The newly created schedule entry.
        """  # noqa: E501,W505
        transfer_vm_resource = FileTransferScheduleEntry(
            location, interval, start_time, destination
        )
        self.vm_resource_schedule.add_vm_resource(transfer_vm_resource)
        return transfer_vm_resource

    def file_transfer_once(self, location, start_time=-1, destination=None):
        """
        This method facilitates pulling a file or directory off of
        a VM in an experiment a single time.

        Note:
            If specifying a destination, the FIREWHEEL group (if any) must have
            permissions to modify and write to that directory. See the
            :ref:`config-system` configuration options to add FIREWHEEL group permissions.

        Args:
            location (str): Absolute path inside the VM to the file or directory
                to be monitored and pulled off the VM.
            start_time (int, optional): The schedule time to transfer
                the file or directory out of the VM
            destination (str, optional): Absolute path on compute node of the
                directory where transferred files are to be placed:
                ``<destination>/<vm_name>/<location>``. If no destination is provided,
                files will be written to ``<logging.root_dir>/transfers/``. See
                :py:meth:`_transfer_data <firewheel.vm_resource_manager.vm_resource_handler.VMResourceHandler._transfer_data>`
                for more details.

        Returns:
            base_objects.FileTransferScheduleEntry: The newly created schedule entry.
        """  # noqa: E501,W505
        # An interval of None indicates that no looping should happen
        # and therefore the file only gets pulled once
        transfer_vm_resource = FileTransferScheduleEntry(
            location, None, start_time, destination
        )
        self.vm_resource_schedule.add_vm_resource(transfer_vm_resource)
        return transfer_vm_resource

    def set_pause(self, start_time, duration=0):
        """
        Create a
        :py:attr:`PAUSE <firewheel.vm_resource_manager.schedule_event.ScheduleEventType.PAUSE>`
        event for a VM at a given start time for the given duration.
        Primarily, pausing will only stop a given VM's schedule for the specified
        duration which will enable users to inspect VM's at a certain point within
        the experiment. Once the pause is complete, the schedule will proceed as expected.
        More information about pausing can be found in :ref:`vm-resource-schedule`.

        Args:
            start_time (int): The time where the pause should happen. This should be
                one of negative :py:data:`math.inf`, 0, or any positive time.
            duration (int): The length of the pause.

        Returns:
            ScheduleEntry: The created schedule entry.
        """
        if duration == 0:
            Console().print(
                f"[b yellow]Pause duration set at 0 seconds for [cyan]{self.name}[/cyan] "
                f"at start time [cyan]{start_time}[/cyan]; it will have no effect"
                "on the experiment timing!"
            )
        pause_vm_resource = PauseScheduleEntry(start_time, duration)
        self.vm_resource_schedule.add_vm_resource(pause_vm_resource)
        return pause_vm_resource

    def set_break(self, start_time):
        """
        Create a break event for a VM at a given start time.
        A break event is an indefinitely long
        :py:attr:`PAUSE <firewheel.vm_resource_manager.schedule_event.ScheduleEventType.PAUSE>`
        event. Primarily, pausing will only stop a given VM's schedule until a
        :py:attr:`RESUME <firewheel.vm_resource_manager.schedule_event.ScheduleEventType.RESUME>`
        event is processed. To enable a user to trigger a resume (and thereby end the break),
        FIREWHEEL has a :ref:`helper_vm_resume` Helper.

        Breaks are useful for enabling users to inspect VMs at a certain point within
        the experiment. Once the break is complete, the schedule will proceed as expected.
        More information about breaking and pausing can be found in :ref:`vm-resource-schedule`.

        Args:
            start_time (int): The time where the break should happen. This should be
                one of negative :py:data:`math.inf`, 0, or any positive time.

        Returns:
            ScheduleEntry: The created schedule entry.
        """
        pause_vm_resource = PauseScheduleEntry(start_time, math.inf)
        self.vm_resource_schedule.add_vm_resource(pause_vm_resource)
        return pause_vm_resource

    def set_default_gateway(self, interface):
        """This method sets the ``default_gateway`` attribute for VMs associated with the given
        router's interface. If the VM host has a router as a neighbor than that router will become
        the VM's default gateway. This can be used by other MCs to add the gateway
        to the VMs interface.

        Args:
            interface (dict): An interface dictionary (see :py:class:`base_objects.Interfaces`).
        """
        for neighbor in interface["switch"].get_neighbors():
            # Looking for hosts
            if not neighbor.type == "host":
                continue
            try:
                for iface in neighbor.interfaces.interfaces:
                    if iface["address"] in interface["network"]:
                        neighbor.default_gateway = interface["address"]
                        break
            except AttributeError:
                self.log.debug("No interfaces on host: %s", neighbor.name)
                continue

    def connect(
        self,
        switch,
        ip,
        netmask,
        delay=None,
        rate=None,
        rate_unit=None,
        packet_loss=None,
        control_network=False,
    ):
        """Create a link between this VM and the given :py:class:`base_objects.Switch` using the
        given IP address.
        This method mostly relies on :py:meth:`_connect <base_objects.VMEndpoint._connect>` for the
        primary logic.

        Note:
            For emulation-based models, due to limitations of
            `tc <https://linux.die.net/man/8/tc>`_ you can only add rate OR loss/delay to a VM.
            Enabling loss or delay will disable rate and vice versa.

        Note:
            The rate is set as a multiple of bits **not** bytes.
            That is, a rate of ``1 kbit`` would equal 1000 bits, not 1000 bytes.
            For bytes, multiply the rate by 8 (e.g. 64 KBytes = 8 * 64 = 512 kbit).

        Args:
            switch (base_objects.Switch): The Switch object to connect to.
            ip (str or netaddr.IPAddress): IP address to use on the connecting interface. This will
                eventually become the IP address on the VM's interface.
            netmask (str or netaddr.IPAddress): The netmask for the connecting interface.
                The netmask can either be in dotted decimal or CIDR (without the slash) notation.
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
            control_network (bool): Is this connection to the control network.
                Defaults to :py:data:`False`.

        Returns:
            tuple(str, firewheel.control.experiment_graph.Edge): A tuple containing the name of the
            newly created VM interface and the
            :py:class:`Edge <firewheel.control.experiment_graph.Edge>` which connects the VM to
            a :py:class:`Switch <base_objects.Switch>`.
        """

        (interface, edge) = self._connect(
            switch,
            ip,
            netmask,
            delay,
            rate=rate,
            rate_unit=rate_unit,
            packet_loss=packet_loss,
            control_network=control_network,
        )

        return (interface["name"], edge)

    def _connect(
        self,
        switch,
        ip,
        netmask,
        delay,
        rate=None,
        rate_unit=None,
        packet_loss=None,
        control_network=False,
    ):
        """Create a link between this host and the given :py:class:`base_objects.Switch` using the
        given IP address.

        Note:
            For emulation-based models, due to limitations of
            `tc <https://linux.die.net/man/8/tc>`_ you can only add rate OR loss/delay to a VM.
            Enabling loss or delay will disable rate and vice versa.

        Note:
            The rate is set as a multiple of bits **not** bytes.
            That is, a rate of ``1 kbit`` would equal 1000 bits, not 1000 bytes.
            For bytes, multiply the rate by 8 (e.g. 64 KBytes = 8 * 64 = 512 kbit).

        Args:
            switch (base_objects.Switch): The switch object to connect to.
            ip (str or netaddr.IPAddress): IP address to use on the connecting interface. This will
                eventually become the IP address on the VM's interface.
            netmask (str or netaddr.IPAddress): The netmask for the connecting interface.
                The netmask can either be in dotted decimal or CIDR (without the slash) notation.
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
            control_network (bool): Is this connection to the control network.
                Defaults to :py:data:`False`.

        Raises:
            TypeError: If the switch is not of type :py:class:`base_objects.Switch`.

        Returns:
            tuple(str, firewheel.control.experiment_graph.Edge): A tuple containing the name
            of the newly created VM interface and the
            :py:class:`Edge <firewheel.control.experiment_graph.Edge>` which connects the VM to
            a :py:class:`Switch <base_objects.Switch>`.
        """
        if not switch.is_decorated_by(Switch):
            raise TypeError("switch parameter must be (decorated by) a Switch.")

        try:
            interface = self.interfaces.add_interface(
                ip, netmask, None, switch, control_network
            )
        except AttributeError:
            self.interfaces = Interfaces()
            interface = self.interfaces.add_interface(
                ip, netmask, None, switch, control_network
            )

        edge = Edge(self, switch)
        edge.dst_ip = interface["address"]
        edge.dst_network = interface["network"]
        # Calling decorate is slow, so only apply QoSEdge if we need it.
        if delay is not None or rate is not None or packet_loss is not None:
            edge.decorate(QoSEdge)
            if delay is not None:
                edge.add_delay(delay)
                interface["qos"]["delay"] = delay
            if rate is not None:
                edge.add_rate_limit(rate, rate_unit)
                rate, rate_unit = edge.qos["rate"]
                interface["qos"]["rate"] = rate
                interface["qos"]["unit"] = rate_unit
            if packet_loss is not None:
                edge.add_packet_loss_percent(packet_loss)
                interface["qos"]["loss"] = packet_loss
        return (interface, edge)

    def l2_connect(self, switch, mac=None):
        """Create a Layer 2 link between this host and the given switch using a
        "blank" IP address.

        Args:
            switch (base_objects.Switch): The switch object to connect to.
            mac (str, optional): A specific MAC address for the interface.
                Defaults to :py:data:`None`.

        Raises:
            TypeError: If the switch is not of type :py:class:`base_objects.Switch`.

        Returns:
            tuple(str, firewheel.control.experiment_graph.Edge): A tuple containing the name of the
            newly created VM interface and the
            :py:class:`Edge <firewheel.control.experiment_graph.Edge>` which connects the VM to
            a :py:class:`Switch <base_objects.Switch>`.
        """
        if not switch.is_decorated_by(Switch):
            raise TypeError("switch parameter must be (decorated by) a Switch.")

        try:
            interface = self.interfaces.add_interface(
                None, None, None, switch, l2_connection=True
            )
        except AttributeError:
            self.interfaces = Interfaces()
            interface = self.interfaces.add_interface(
                None, None, None, switch, l2_connection=True
            )

        if mac:
            interface["mac"] = mac

        edge = Edge(self, switch)
        edge.dst_ip = "0.0.0.0"  # noqa: S104

        return (interface, edge)


class VmResourceScheduleEntry(ScheduleEntry):
    """
    This class provides backwards compatibility for VMRs that were written for
    pre-2.0 versions of FIREWHEEL.

    Each VMR is provided with three command line arguments:
    ``dynamic_content``, ``static_content``, and a reboot file.
    """

    def __init__(
        self, vm_resource_name, start_time, dynamic_contents=None, static_filename=None
    ):
        """
        Create a VmResourceScheduleEntry

        Args:
            vm_resource_name (str): Name of VM resource to run. This VMR
                must be available to the experiment (i.e. must be
                specified in a model component's ``MANIFEST`` file).
            start_time (int): Start time of the VM resource as an integer.
            dynamic_contents (str, optional): Content to be passed to the VM resource.
                Dynamic content gets written to a file and the filename gets passed
                to the VM resource as the first parameter. Defaults to :py:data:`None`.
            static_filename (str, optional): File to be passed to the VM resource. The file
                must be in the VM resource's database (like the VM resource itself). The file is
                loaded into the VM and then the file's path is passed to the VM resource as
                the second parameter. Defaults to :py:data:`None`.
        """

        super().__init__(start_time)

        # The vm_resource needs to be loaded into the VM
        self.add_file(vm_resource_name, vm_resource_name, executable=True)

        arguments = []

        if dynamic_contents:
            self.add_content("dynamic", dynamic_contents)
            arguments.append("dynamic")
        else:
            arguments.append("None")

        if static_filename:
            self.add_file(static_filename, static_filename)
            arguments.append(static_filename)
        else:
            arguments.append("None")

        arguments.append("reboot")

        self.set_executable(vm_resource_name, arguments)


class DropContentScheduleEntry(ScheduleEntry):
    """
    This class facilitates writing content to a file within
    the VM. This content is generally dynamically generated based off the
    current graph.
    """

    def __init__(
        self, start_time, location, content, executable=False, preload_move_cmd=None
    ):
        """
        Create a DropContentScheduleEntry.

        Args:
            start_time (int): Start time of the schedule entry as an integer.
            location (str): Absolute, Unix-style path inside the VM to write
                the provided content, including filename. If the VM is Windows
                then omit the drive letter. (e.g. ``/windows/system32``)
            content (str): Either the content to be written as a string or a
                :obj:`Callable <collections.abc.Callable>` object (e.g. a function pointer to a
                function) that returns a string. The callback function gets called during the
                :py:meth:`base_objects.VmResourceSchedule.get_schedule` method.
                The :ref:`vm_resource.schedule_mc` model component which then calls
                :py:meth:`get_schedule() <base_objects.VmResourceSchedule.get_schedule>` for every
                :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` in the graph.
            executable (bool, optional): Set the new file's executable flag.
                Default is :py:data:`False`.
            preload_move_cmd (str, optional): If set, instead of dropping the content directly
                into ``location`` at ``start_time``, the content will be preloaded into a
                temporary location prior to any schedule entries running and then moved
                to ``location`` at ``start_time`` with ``preload_move_cmd``.
                Defaults to :py:data:`None`.
                This is particularly useful for placing content into directories which will be
                created by another VMR.
        """

        super().__init__(start_time)

        if preload_move_cmd:
            self.set_executable(preload_move_cmd, f"preloaded_content {location}")
            self.add_content("preloaded_content", content, executable)
            return

        self.add_content(location, content, executable)


class DropFileScheduleEntry(ScheduleEntry):
    """
    This class facilitates loading a given file into the VM.
    """

    def __init__(
        self, start_time, location, filename, executable=False, preload_move_cmd=None
    ):
        """
        Create the DropFileScheduleEntry.

        Args:
            start_time (int): Start time of the schedule entry as an integer.
            location (str): Absolute, Unix-style path inside the VM to write
                the provided content, including filename. If the VM is Windows
                then omit the drive letter. (e.g. ``/windows/system32``)
            filename (str): Name of file to be written. This file needs to be
                available to FIREWHEEL. This only happens when the files
                are included in the list of "vm_resources" that are specified in a model
                component's ``MANIFEST`` file.
            executable (bool, optional): Set the new file's executable flag.
                Default is :py:data:`False`.
            preload_move_cmd (str, optional): If set, instead of dropping the file directly
                into ``location`` at ``start_time``, the file will be preloaded into a
                temporary location prior to any schedule entries running and then moved
                to ``location`` at ``start_time`` with ``preload_move_cmd``.
                Defaults to :py:data:`None`.
                This is particularly useful for placing files into directories which will be created
                by another VMR.
        """

        super().__init__(start_time)

        if preload_move_cmd:
            self.set_executable(preload_move_cmd, f"{filename} {location}")
            self.add_file(filename, filename, executable)
            return

        self.add_file(location, filename, executable)


class RunExecutableScheduleEntry(ScheduleEntry):
    """
    RunExecutableScheduleEntry facilitates specifying a program
    to run within the VM.
    """

    def __init__(self, start_time, program, arguments=None, vm_resource=False):
        """
        Create a :py:class:`base_objects.RunExecutableScheduleEntry` with the given parameters.

        Args:
            start_time (int): Start time of the schedule entry as an integer.
            program (str): The program to run. Unless ``vm_resource`` is set, it
                is safest to specify the absolute path of the program (in case
                the program is not on the system's ``PATH``).
            arguments (str or list, optional): Arguments to pass on the command line to the program.
                Must be a string or list of strings. Defaults to :py:data:`None`.
            vm_resource (bool, optional): If the program is a VM resource,
                then the VM resource file needs to be loaded into the VM before
                it is run. Defaults to :py:data:`False`.
        """

        super().__init__(start_time)
        self.set_executable(program, arguments)

        # If the program is a VM resource, then the vm_resource file needs to be loaded into
        # the VM. Add it as a file with a relative path of just its name
        if vm_resource:
            self.add_file(program, program, executable=True)


class FileTransferScheduleEntry(ScheduleEntry):
    """
    Facilitates programmatically pulling data out of a VM in an experiment.
    This is primarily accomplished by leveraging the
    :py:meth:`add_file_transfer <firewheel.vm_resource_manager.schedule_entry.ScheduleEntry.add_file_transfer>`
    method.
    """

    def __init__(
        self,
        in_vm_location,
        interval=10,
        start_time=-1000000,
        out_host_destination=None,
    ):
        """Schedule extracting a file from a VM at a specified interval.
        If the VM is a Linux host then files only get pulled when they have changed
        (after the initial pull). If the VM is a Windows host then the file/directory
        will get pulled at every interval.

        Note:
            If specifying a destination, the FIREWHEEL group (if any) must have
            permissions to modify and write to that directory. See the
            :ref:`config-system` configuration options to add FIREWHEEL group permissions.

        Args:
            in_vm_location (str): Path inside the VM to the file or directory
                to be monitored and extracted from the VM.
            interval (int, optional): Interval specifying how often to check for
                file or directory updates. Defaults to ``10``. This enables extracting
                files which are constantly updating (e.g. logs).
            start_time (int, optional): When to schedule the transfer. Defaults to ``-1000000``.
                Because of the highly negative start time, this will almost always run immediately.
            out_host_destination (str, optional): Absolute path on compute node of the
                directory where transferred files are to be placed:
                ``<destination>/<vm_name>/<location>``. If no destination is provided,
                files will be written to ``<logging.root_dir>/transfers/``. See
                :py:meth:`_transfer_data <firewheel.vm_resource_manager.vm_resource_handler.VMResourceHandler._transfer_data>`
                for more details.
        """  # noqa: E501,W505
        super().__init__(start_time)
        self.add_file_transfer(in_vm_location, interval, out_host_destination)


class PauseScheduleEntry(ScheduleEntry):
    """
    Create a
    :py:attr:`PAUSE <firewheel.vm_resource_manager.schedule_event.ScheduleEventType.PAUSE>`
    schedule entry for the given VM.
    """

    def __init__(self, start_time, duration=0):
        """
        Create a :py:class:`base_objects.PauseScheduleEntry` with the given parameters.
        While a start time of 0 *is* permitted for this schedule entry, in practice, this
        entry is really converted to the minimum representable positive normalized float
        via `sys.float_info.min <https://docs.python.org/3/library/sys.html#sys.float_info.min>`_.

        Note:
            When support for Python 3.8 is dropped, this could be converted to the
            smallest positive denormalized representable float via :py:func:`math.ulp`
            (e.g., ``math.ulp(0.0)``).

        Args:
            start_time (int): Start time of the schedule entry as an integer.
            duration (int): The length of the pause which should happen. If the
                duration is :py:data:`math.inf` than this counts as a *break*.

        Raises:
            ValueError: If the start time is invalid (i.e., less than 0 and not infinity).
            ValueError: If the duration is not positive.
        """

        valid_start_string = str(
            "Valid start times for pause and break only include "
            "negative infinity or greater than or equal to 0."
        )
        # We need to verify valid start times
        if start_time < 0 and not math.isinf(start_time):
            raise ValueError(f"Invalid start time! {valid_start_string}")

        if start_time == 0:
            self.log.debug("Converting a 0 start time to `sys.float_info.min`.")
            start_time = sys.float_info.min

        super().__init__(start_time)

        # We need to verify valid durations
        if duration < 0:
            raise ValueError("The duration for a pause/break must not be negative.")

        self.add_pause(duration)
