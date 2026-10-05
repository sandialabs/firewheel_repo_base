import os
import uuid

import firewheel.vm_resource_manager.vm_resource_handler
from firewheel.config import config as fw_config
from firewheel.control.experiment_graph import require_class


class MinimegaEmulatedEntity:
    """
    This object adds a UUID to the :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
    """

    def __init__(self):
        """Adding a new UUID and casting it to a string."""
        self.uuid = str(uuid.uuid4())


@require_class(MinimegaEmulatedEntity)
class MinimegaEmulatedVM:
    """
    An object which adds methods to a
    :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` to collect all
    configuration options needed to launch the VM with minimega.

    Attributes:
        interface_defaults (dict): A dictionary
            containing default values for interfaces.
            This includes the type of interface and the required driver.
        drive_defaults (dict): A dictionary
            containing default values for VM drives.
            This includes the drive interface and cache type.
        cpu_defaults (dict): A dictionary
            containing default values for VM CPUs. This includes the model type, and number
            of sockets, cores, and threads.
    """

    interface_defaults = {"type": "tap", "driver": "virtio-net-pci"}
    drive_defaults = {
        "interface": "virtio",
        "cache": "writeback",
    }
    cpu_defaults = {
        "model": "qemu64",
        "sockets": 1,
        "cores": 1,
        "threads": 1,
    }

    def _generate_nic_configs(self, config):
        """Create a finished configuration for each NIC.

        The finished config for a NIC resembles:

        .. code-block:: python

            {
                "name": "nic",
                "id": "unique",
                "type": "tap",
                "interface": "tap0",
                "driver": "virtio-net-pci",
                "bus": "pci.0",
                "bus_addr": "5",
                "mac": "00:00:00:00:00:00"
            }

        Where the fields are described as:

            * *name* - minimega device name. (e.g. ``"nic"``).
            * *id* - Some value unique within the scope of this VM.
            * *type* - Type of interface. Supported: ``"tap"``. This corresponds to both
              a QEMU type and a mapping to a minimega port object.
            * *interface* - Name of the tap interface on the underlying host system.
              This must meet the restrictions placed by Linux on the
              naming of network interfaces.
            * *bus* - PCI bus number.
            * *bus_addr* - PCI bus address.
            * *mac* - MAC address for this interface.

        Args:
            config (dict): The configuration for the VM.

        Raises:
            RuntimeError: If a required configuration key is missing from an interface.
        """
        config_list = []
        try:
            for interface in self.interfaces.interfaces:
                iface_conf = {
                    "name": "nic",
                    "id": f"if{len(config_list)}",
                }

                # Apply defaults.
                for default_key, value in self.interface_defaults.items():
                    try:
                        interface[default_key]
                    except KeyError:
                        interface[default_key] = value

                # Finish building the config.
                iface_conf["switch_name"] = interface["switch"].name
                keys = ["type", "driver", "mac", "qos"]
                for k in keys:
                    try:
                        iface_conf[k] = interface[k]
                    except KeyError as exc:
                        self.log.error(
                            'Missing required key "%s" on VM "%s". Have: %s',
                            k,
                            self.name,
                            interface,
                        )
                        raise RuntimeError(
                            f'Required key "{k}" not found on interface for VM "{self.name}".'
                        ) from exc

                try:
                    iface_conf["ip"] = str(interface["network"])
                except KeyError:
                    pass

                config_list.append(iface_conf)
        except AttributeError:
            # There's nothing that says a VM must have NICs.
            pass

        self.log.debug('VM "%s" generated %s NIC configs.', self.name, len(config_list))
        config["aux"]["nic"] = config_list

    def _generate_drive_configs(self, config):
        """Create a finished configuration for each drive.

        Note:
            The first disk is assumed to be the image for the VM.

        Args:
            config (dict): The configuration for the VM.

        Returns:
            list: A list of drives for the VM.

        Raises:
            RuntimeError: If a required configuration key is missing from an interface.

        """
        config_list = []

        for drive in self.vm["drives"]:
            conf = {
                "name": "drive",
                "id": f"drv{len(config_list)}",
                "file": drive["file"],
                "path": os.path.join(self.vm["image_store"]["name"], drive["file"]),
                "db_path": drive["db_path"],
            }

            # Apply defaults.
            for default_key, value in self.drive_defaults.items():
                try:
                    drive[default_key]
                except KeyError:
                    drive[default_key] = value

            # Finish building the config
            keys = ["interface", "cache"]
            for k in keys:
                try:
                    conf[k] = drive[k]
                except KeyError as exc:
                    raise RuntimeError(
                        f'Required key "{k}" not found on drive for VM "{self.name}".'
                    ) from exc

            config_list.append(conf)

        config["aux"]["disks"] = config_list
        self.log.debug(
            'VM "%s" generated %s drive configs.', self.name, len(config_list)
        )
        return config_list

    def _generate_vcpu_config(self, config):
        """Create a finished configuration for the VMs vCPUs.

        Args:
            config (dict): The configuration for the VM.

        Returns:
            list: A list containing the ``cpu_config``, the ``smp_config``, and the modified
            VM config.
        """
        cpu_config = {
            "name": "cpu",
            "id": "cpu",
        }
        smp_config = {
            "name": "smp",
            "id": "smp",
        }

        try:
            cpu_config["model"] = self.vm["vcpu"]["model"]
        except KeyError:
            self.log.debug(
                'Using default VCPU model ("%s") for VM "%s".',
                self.cpu_defaults["model"],
                self.name,
            )
            cpu_config["model"] = self.cpu_defaults["model"]
            if "vcpu" not in self.vm:
                self.vm["vcpu"] = {}
            self.vm["vcpu"]["model"] = self.cpu_defaults["model"]

        config["vm"]["vcpu_model"] = self.vm["vcpu"]["model"]

        def __handle_smp_key(key, default_value):
            """Set the value for a single SMP key on the VM if it has not been configured.

            Args:
                key (str): Which SMP value to change (e.g. "sockets", "cores", "threads", etc.)
                default_value (int): The value for the SMP key.
            """
            try:
                smp_config[key] = self.vm["vcpu"][key]
            except KeyError:
                self.log.debug(
                    'Using default value %d for SMP parameter "%s" on VM "%s".',
                    default_value,
                    key,
                    self.name,
                )
                smp_config[key] = default_value
                if "vcpu" not in self.vm:
                    self.vm["vcpu"] = {}
                self.vm["vcpu"][key] = default_value

        __handle_smp_key("sockets", self.cpu_defaults["sockets"])
        __handle_smp_key("cores", self.cpu_defaults["cores"])
        __handle_smp_key("threads", self.cpu_defaults["threads"])

        for smp_key, smp_val in smp_config.items():
            full_key = f"smp_{smp_key}"
            config["vm"][full_key] = smp_val

        return [cpu_config, smp_config, config]

    def _generate_mem_config(self, config):
        """Create a finished configuration for the VMs memory.

        Args:
            config (dict): The configuration for the VM.
        """
        try:
            memory = str(self.vm["mem"])
        except KeyError:
            memory = "512"
        config["vm"]["memory"] = memory

    def _generate_vga_config(self, config):
        """Create a finished configuration for the VMs VGA display.

        Args:
            config (dict): The configuration for the VM.
        """
        default_vga_model = "std"
        vga_config = {
            "name": "vga",
            "id": "minimegavga",
        }

        try:
            vga_config["model"] = self.vm["vga"]
        except KeyError:
            vga_config["model"] = default_vga_model
            self.vm["vga"] = default_vga_model

        config["vm"]["vga_model"] = self.vm["vga"]

    def _generate_vm_resource_handler_communication_config(self, config, minimega_type):
        """Create the configuration used by the :ref:`vm-resource-handler` to communicate
        with the VM.

        Args:
            config (dict): The configuration for the VM.
            minimega_type (str): The VM type, e.g. ``QemuVM`` or ``android``.

        Returns:
            dict: Driver communication configuration.
        """
        try:
            if not self.vm_resource_schedule:
                return {}
        except AttributeError:
            return {}

        if minimega_type == "QemuVM":
            virtio_serial_path = os.path.join(
                fw_config["minimega"]["base_dir"],
                "namespaces",
                fw_config["minimega"]["namespace"],
                self.uuid,
                "virtio-serial0",
            )

            qga_config = {
                "name": "serial",
                "id": "minimegaqga",
                "path": virtio_serial_path,
            }

            self.log.debug("new qga path is %s", qga_config["path"])
            config["aux"]["qga_config"] = qga_config
            return qga_config

        if minimega_type == "android":
            adb_options = self.vm.get("adb", {})
            android_options = self.vm.get("android", {})

            android_console_port = adb_options.get(
                "android_console_port",
                android_options.get("android-console-base-port"),
            )

            if android_console_port in {0, "0", ""}:
                android_console_port = None

            adb_config = {
                "require_root": adb_options.get("require_root", True),
            }

            # Optional pre-launch hint. This will be overwritten after
            # minimega launch's the VM using the actual `android_serial``.
            if adb_options.get("adb_serial"):
                adb_config["adb_serial"] = adb_options["adb_serial"]

            # Optional requested/hinted console port. This will be overwritten after
            # minimega launch's the VM using the actual ``android_console_port``.
            if android_console_port is not None:
                adb_config["android_console_port"] = android_console_port

            # Optional; This is typically `android_console_port` + 1 but is
            # normally unknown/unset until after minimega launch.
            if "android_adb_port" in adb_options:
                adb_config["android_adb_port"] = adb_options["android_adb_port"]

            config["aux"]["adb_config"] = adb_config
            return adb_config

        return {}

    def _generate_vm_resource_handler_process_config(self, config):
        """
        Create a configuration for launching a :ref:`vm-resource-handler` process
        for each VM. This method assumes that FIREWHEEL has been installed in the same
        location on all :ref:`cluster-compute-nodes`.

        Args:
            config (dict): The configuration for the VM.

        Returns:
            dict: The configuration to launch a new a new :ref:`vm-resource-handler` process,
            or None if no handler should be launched.
        """
        try:
            if not self.vm_resource_schedule:
                return None
        except AttributeError:
            return None

        process_config = {
            "type": "Process",
            "uuid": str(uuid.uuid4()),
            "vm_name": config["vm"]["name"],
            "vm_uuid": config["vm"]["uuid"],
            "binary_name": firewheel.vm_resource_manager.vm_resource_handler.__file__,
        }

        driver_type = config["vm"]["type"]

        if driver_type == "QemuVM":
            qga_config = config["aux"].get("qga_config")
            if not qga_config:
                return None

            process_config["engine"] = "QemuVM"
            process_config["path"] = qga_config["path"]

        elif driver_type == "android":
            adb_config = config["aux"].get("adb_config")
            if not adb_config:
                return None

            process_config["engine"] = "ADB"
            process_config["vm_type"] = "android"
            process_config["require_root"] = adb_config.get("require_root", True)

            if "adb_serial" in adb_config:
                process_config["adb_serial"] = adb_config["adb_serial"]

            if "android_console_port" in adb_config:
                process_config["android_console_port"] = adb_config[
                    "android_console_port"
                ]

            if "android_adb_port" in adb_config:
                process_config["android_adb_port"] = adb_config["android_adb_port"]
        else:
            self.log.debug(
                'VM "%s" has unsupported VM Resource Handler driver type "%s".',
                config["vm"]["name"],
                driver_type,
            )
            return None

        config["aux"]["handler_process"] = process_config
        return process_config

    def _generate_bios_config(self, config):
        """Create a finished configuration for the VMs BIOS.

        Args:
            config (dict): The configuration for the VM.
        """
        bios = self.vm.get("bios", None)
        if bios:
            config["aux"]["qemu_append"]["bios"] = os.path.join(
                self.vm["image_store"]["path"], bios
            )

    def _generate_qemu_append_str(self, config):
        """
        Some QEMU arguments are not natively supported by minimega's vm config function.
        To set those arguments, we can use the ``qemu_append`` option for the VM config.

        In this method, we take all of the ``qemu_append`` mappings and parse them into a string
        to be used by minimega.

        For example, BIOS can currently only be set in this way. In
        :py:meth:`_generate_bios_config <minimega.emulated_entities.MinimegaEmulatedVM._generate_bios_config>`,
        we grab the value for BIOS from ``self.vm`` and set it in the ``qemu_append`` dictionary.
        Then this parses: ``{"bios" : "seabios_rel-1.14.0.0"}`` into ``-bios seabios_rel-1.14.0.0``.

        Args:
            config (dict): The configuration for the VM.
        """
        append_str = " ".join(
            [f"-{k} {v}" for k, v in config["aux"]["qemu_append"].items()]
        )
        config["aux"]["qemu_append_str"] = append_str

    def generate_minimega_config(self):
        """Generate a minimega VM config based on this
        :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.

        Returns:
            dict: The minimega configuration dictionary with all required information.

        Raises:
            KeyError: Every VM must define an architecture.
        """

        config = {}
        config["aux"] = {}
        config["aux"]["qemu"] = self.vm.get("qemu")
        config["aux"]["qemu_append"] = self.vm.get("qemu_append", {})
        config["vm"] = {}
        config["vm"]["uuid"] = self.uuid
        config["vm"]["type"] = self.vm.get("vm_type", "QemuVM")
        is_android = config["vm"]["type"] == "android"
        config["aux"]["android_config"] = self.vm.get("android", {})

        config["coschedule"] = self.coschedule
        self.log.debug('VM "%s" has UUID %s.', self.name, self.uuid)

        try:
            config["aux"]["control_ip"] = str(self.control_ip)
        except AttributeError:
            self.control_ip = ""
            config["aux"]["control_ip"] = ""
        self.log.debug(
            'VM "%s" has control_ip %s.', self.name, config["aux"]["control_ip"]
        )
        try:
            config["vm"]["architecture"] = self.vm["architecture"]
        except KeyError:
            self.log.critical("VM %s must define an architecture.", self.name)
            raise
        config["vm"]["name"] = self.name

        if is_android:
            config["vm"]["image"] = self.vm.get("image", "")
            config["aux"]["disks"] = []
        else:
            config["vm"]["image"] = self.vm["image"]

        if "initial_power_state" in self.vm:
            config["aux"]["power_state"] = self.vm["initial_power_state"]
        else:
            config["aux"]["power_state"] = "running"

        self._generate_nic_configs(config)
        if not is_android:
            self._generate_bios_config(config)
            self._generate_drive_configs(config)
            self._generate_vga_config(config)
        else:
            config["vm"]["vga_model"] = self.vm.get("vga", "")

        self._generate_vcpu_config(config)
        self._generate_mem_config(config)
        self._generate_qemu_append_str(config)
        self._generate_vm_resource_handler_communication_config(
            config, config["vm"]["type"]
        )

        try:
            config["aux"]["raw_device_configs"] = self.vm["raw_device_configs"]
            self.log.debug('Including raw device configs for VM "%s".', self.name)
        except KeyError:
            pass

        # We must have a QMP socket.
        default_qmp_id = "minimegaqmp"
        qmp_dev = {
            "name": "qmp",
            "id": default_qmp_id,
            "path": os.path.join(
                fw_config["minimega"]["base_dir"],
                "namespaces",
                fw_config["minimega"]["namespace"],
                self.uuid,
                "qmp",
            ),
        }
        config["aux"][default_qmp_id] = qmp_dev
        self.log.debug("new qmp path is %s", qmp_dev["path"])

        try:
            config["tags"] = self.mm_tags
        except AttributeError:
            config["tags"] = {}

        if config["aux"].get("qga_config") or config["aux"].get("adb_config"):
            self._generate_vm_resource_handler_process_config(config)

        return config
