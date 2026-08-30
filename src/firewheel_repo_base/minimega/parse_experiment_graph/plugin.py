import os
import sys
import json
import subprocess
from time import sleep

from base_objects import VMEndpoint
from minimega.emulated_entities import MinimegaEmulatedEntity

from firewheel.config import config as fw_config
from firewheel.lib.minimega.api import minimegaAPI
from firewheel.lib.discovery.api import discoveryAPI
from firewheel.control.experiment_graph import AbstractPlugin


class Plugin(AbstractPlugin):
    """This Plugin parses the experiment graph to build necessary data structures which
    can be passed to `Discovery <https://github.com/sandia-minimega/discovery>`__.
    Discovery will then generate the necessary minimega commands and this Plugin will
    launch the experiment.
    """

    def insert_vm_endpoint(self, vme_conf):
        """
        For each VM, we will create a dictionary containing all information required to
        launch it. Then pass this to discovery's
        :py:meth:`insert <firewheel.lib.discovery.api.discoveryAPI.insert_endpoint>` endpoint.
        The NIC/interface information is not included as it will be handled with
        :py:meth:`make_endpoint_connections <minimega.parse_experiment_graph_plugin.Plugin.make_endpoint_connections>`.

        Args:
            vme_conf (dict): The generated minimega configuration dictionary created by
                :ref:`minimega.emulated_entities_mc`.

        Raises:
            RuntimeError: If minimega tags are used and a tag name conflicts with
                a required configuration key.

        Returns:
            dict: The newly created endpoint in the discovery graph.
        """
        data = {}
        data["architecture"] = vme_conf["vm"]["architecture"]
        data["name"] = vme_conf["vm"]["name"]
        data["uuid"] = vme_conf["vm"]["uuid"]
        try:
            data["control_ip"] = vme_conf["aux"]["control_ip"]
        except KeyError:
            # A control IP is not necessary
            data["control_ip"] = ""

        data["type"] = "qemu"
        data["cpu_model"] = "host"
        data["memory"] = vme_conf["vm"]["memory"]

        # Setting various CPU values
        for smp_key in ["smp_sockets", "smp_cores", "smp_threads"]:
            data[smp_key] = str(vme_conf["vm"][smp_key])

        # We need to manually set maxcpus to override default of 1
        vcpus = (
            int(data["smp_sockets"]) * int(data["smp_cores"]) * int(data["smp_threads"])
        )
        data["vcpus"] = str(vcpus)

        data["vga_model"] = vme_conf["vm"]["vga_model"]

        # NOTE: we assume the first disk is the image
        data["image"] = vme_conf["aux"]["disks"][0]["file"]
        disk_strs = []
        for drive in vme_conf["aux"]["disks"]:
            disk_str = ",".join([drive["path"], drive["interface"], drive["cache"]])
            disk_strs.append(disk_str)
        data["disks"] = " ".join(disk_strs)

        # Currently, there is only support for a num_serial option
        # we need one for the qga socket
        data["virtio_ports"] = "org.qemu.guest_agent.0"

        # Get all the minimega tags
        for tag_key, tag_value in vme_conf["tags"].items():
            if tag_key in data:
                raise RuntimeError(
                    f"Tag {tag_key} conflicts with required config key."
                    "Please rename your tag."
                )
            data[tag_key] = tag_value

        # Add any other QEMU options here.
        data["qemu_append"] = vme_conf["aux"]["qemu_append_str"]

        # If there's any coscheduling parameters, propagate them
        data["coschedule"] = str(vme_conf["coschedule"])

        # Create the endpoint in the discovery graph.
        mm_endpoint = self.discovery_api.insert_endpoint(mm_node_properties=data)[0]
        return mm_endpoint

    def make_endpoint_connections(self, mm_endpoint, vme_conf, switch_name_to_nid):
        """This method informs discovery about all the connections that need to happen to launch
        the experiment. Due to some limitations with discovery, we are unable to add an edge
        between the VM and a switch containing all of the necessary information in a single
        discovery API call. Instead, we need to do the following:

        1. Create an edge between the VM and the switch via discovery's connect endpoint.
           This returns the updated VM endpoint, which has an empty dictionary added
           to its list of edges.
        2. Create a dictionary containing the edge's attributes. We store this
           dictionary in a local list so that we can update all of the edges for
           this VM in a single update endpoint API call.
        3. Once all edges are initialized in the discovery graph, we update the edges
           contained in our VM endpoint dictionary with the ones from our local edge list.
           We update the edges in discovery by passing this updated VM dictionary to
           discovery's update endpoint.

        Args:
            mm_endpoint (dict): The discovery endpoint dictionary created by
                :py:meth:`insert_vm_endpoint <minimega.parse_experiment_graph_plugin.Plugin.insert_vm_endpoint>`.
            vme_conf (dict): The generated minimega configuration dictionary created by
                :ref:`minimega.emulated_entities_mc`.
            switch_name_to_nid (dict): A dictionary of network IDs which are used by discovery.

        Returns:
            dict: The newly updated endpoint in the discovery graph.
        """

        try:
            assert isinstance(vme_conf["aux"]["nic"], list)
        except KeyError:
            return None

        edges = []
        for nic in vme_conf["aux"]["nic"]:
            # Create an edge between the VM and the switch using the network identifier
            # for that switch that we created earlier with the insert network API call.
            switch_name = nic["switch_name"]
            switch_network_id = switch_name_to_nid[switch_name]
            mm_endpoint = self.discovery_api.connect_endpoint(
                mm_endpoint["NID"], switch_network_id
            )

            # Create a dictionary containing this edge's attributes and hold on to it until
            # we have finished inserting all edges.
            edge_data = {"mac": nic["mac"], "driver": nic["driver"]}
            edge_data["bridge"] = fw_config["minimega"]["control_bridge"]

            # QoS attributes e.g. loss, delay, rate
            for qos_key, qos_value in nic["qos"].items():
                if qos_value:
                    edge_data[qos_key] = str(qos_value)
            edge = {"N": switch_network_id, "D": edge_data}
            edges.append(edge)

        # Now that we have (1) initialized all of the edges and (2) created a local list of updated
        # edges, we can send an updated dictionary for our endpoint containing the updated list
        # of edges to the discovery's update endpoint.
        for eid, edge in enumerate(edges):
            assert mm_endpoint["Edges"][eid]["N"] == edge["N"]
            mm_endpoint["Edges"][eid]["D"] = edge["D"]

        mm_endpoint = self.discovery_api.update_endpoint(mm_node_properties=mm_endpoint)
        return mm_endpoint

    def _ensure_kvm_virtualization_enabled(self):
        """Ensure that KVM virtualization is enabled. Without it, minimega will
        not be able to launch VMs. This function checks
        ``/sys/module/kvm_intel/parameters/nested`` and
        ``/sys/module/kvm_amd/parameters/nested`` to see if it can successfully
        determine that virtualization is enabled. If that check is inconclusive
        (i.e. those files do not exist) it attempts to use the
        ``virst-host-validate`` program to make the determination.

        Raises:
            RuntimeError: If KVM virtualization is not enabled
        """
        exception_msg = "KVM Virtualization not enabled. Enable in BIOS to launch VMs with minimega"
        not_found_msg = "not found when checking for KVM virtualization, continuing check with another method"

        # First, check kvm parameters files
        kvm_params_files = [f"/sys/module/kvm_{arch}/parameters/nested" for arch in ["intel", "amd"]]
        for kvm_params_file in kvm_params_files:
            try:
                with open(kvm_params_file, "r") as params_file:
                    params = params_file.read()
            except FileNotFoundError:
                self.log.debug(f"File {kvm_params_file} {not_found_msg}")
                continue
            params = params.strip()
            if params == "Y":
                return
            else:
                raise RuntimeError(exception_msg)

        # If previous check was inconclusive, try using the `virt-host-validate` command
        output_set = False
        try:
            virt_host_validate = "virt-host-validate"
            output = subprocess.check_output([virt_host_validate], stderr=subprocess.STDOUT)
            output_set = True
        except FileNotFoundError:
            self.log.debug(f"Command {virt_host_validate} {not_found_msg}")
        except subprocess.CalledProcessError as exc:
            # virt-host-validate may return a non-zero exit code, but we only
            # need to check a few fields, so that could still be okay. Ignore
            # this error.
            output = exc.output
            output_set = True

        if output_set:
            output = output.decode("utf-8")
            lines = output.split("\n")
            fields_to_check = [
                ["Checking for hardware virtualization", False],
                ["Checking if device /dev/kvm exists", False],
                ["Checking if device /dev/vhost-net exists", False],
                ["Checking if device /dev/net/tun exists", False]
            ]
            for line in lines:
                try:
                    prgm, msg, result = line.split(":")
                except ValueError:
                    continue
                msg = msg.strip()
                result = result.strip()
                for i in range(len(fields_to_check)):
                    field = fields_to_check[i][0]
                    if msg == field:
                        fields_to_check[i][1] = result == "PASS"

            if all([field[1] for field in fields_to_check]):
                return
            else:
                # If any of the checks failed, raise the Exception
                raise RuntimeError(exception_msg)

        self.log.debug(f"Could not verify that KVM virtualization was enabled")
        raise RuntimeError(exception_msg)


    def run(self):
        """This method contains the primary logic to launch an experiment.
        It has several objectives:

        #. Add all VMs and connections to Discovery's graph.
        #. Invoke discovery to output this data as minimega commands via the ``minemiter`` command.
           See the Discovery source code for more information about
           `minemiter <https://github.com/sandia-minimega/discovery/tree/master/src/cmds/minemiter>`_.

        #. Have minimega read the output to launch the VMs.
        #. Finish setting up the control network (if any exists).
        #. Launch a :ref:`vm-resource-handler` for each VM using minimega to start the process.
        """
        self.discovery_api = discoveryAPI()
        switch_names = set()

        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(MinimegaEmulatedEntity):
                if vertex.is_decorated_by(VMEndpoint):
                    try:
                        for iface in vertex.interfaces.interfaces:
                            switch_name = iface["switch"].name
                            switch_names.add(switch_name)
                    except AttributeError:
                        self.log.debug("%s doesn't have any interfaces.", vertex.name)

        switch_name_to_nid = {}
        switch_names = set(switch_names)
        original_switch_len = len(switch_names)
        # if there is a control network, insert one
        try:
            assert self.g.control_net["name"]
            assert self.g.control_net["host_addr"]
            self.control_net = self.g.control_net["name"]
        except (AttributeError, KeyError, AssertionError):
            self.control_net = False

        if self.control_net and self.control_net in switch_names:
            network_ids = self.discovery_api.insert_network()
            network_id = network_ids[0]["NID"]
            switch_name_to_nid[self.control_net] = network_id
            switch_names.remove(self.control_net)
            assert len(switch_names) == original_switch_len - 1
        for sw_name in switch_names:
            network_ids = self.discovery_api.insert_network()
            network_id = network_ids[0]["NID"]
            switch_name_to_nid[sw_name] = network_id
        num_vms = 0
        vme_confs = {}
        for vertex in self.g.get_vertices():
            if vertex.is_decorated_by(MinimegaEmulatedEntity):
                if vertex.is_decorated_by(VMEndpoint):
                    # For each VM, we will add it to the discovery graph
                    # using the insert_endpoint API call.
                    vme_conf = vertex.generate_minimega_config()
                    vme_confs[vertex.name] = vme_conf
                    num_vms += 1
                    mm_endpoint = self.insert_vm_endpoint(vme_conf)
                    # Then we will insert edges for each of its NICs.
                    mm_endpoint = self.make_endpoint_connections(
                        mm_endpoint, vme_conf, switch_name_to_nid
                    )

        self.discovery_api.set_config("queueing", "true")

        minemiter_path = os.path.join(
            fw_config["discovery"]["install_dir"], "bin", "minemiter"
        )
        template_path = os.path.join(fw_config["discovery"]["install_dir"], "templates")
        minimega_bin_path = os.path.join(
            fw_config["minimega"]["install_dir"], "bin", "minimega"
        )
        fw2mm_path = os.path.join(fw_config["system"]["default_output_dir"], "fw2mm.mm")
        # Note that this uses the FIREWHEEL configuration to launch a new process
        # if there are not access controls on this file or the user accounts there
        # could be security concerns.
        minemiter_ret = subprocess.check_call(  # nosec
            [
                minemiter_path,
                "-path",
                template_path,
                "-w",
                fw2mm_path,
                "-server",
                self.discovery_api.bind_addr,
            ]
        )
        self.log.debug("minemiter_ret=%s", minemiter_ret)
        self._ensure_kvm_virtualization_enabled()
        # Note that this uses the FIREWHEEL configuration to launch a new process
        # if there are not access controls on this file or the user accounts there
        # could be security concerns.
        launch_vms_ret = subprocess.check_call(  # nosec
            [
                minimega_bin_path,
                f"-base={fw_config['minimega']['base_dir']}",
                "-e",
                "read",
                fw2mm_path,
            ]
        )
        self.log.debug("launch_vms_ret=%s", launch_vms_ret)

        # Wait for all VMs to launch.
        vm_map = {}
        mm_api = minimegaAPI()
        all_vms_launched = False
        core_vms = None
        for i in range(100):
            sleep(0.5)
            try:
                core_vms = mm_api.mm_vms()
                found_vms = len(core_vms)
                all_vms_launched = found_vms == num_vms
                self.log.debug(
                    "Iteration num=%s. Waiting for vm configs from minimega: "
                    "found=%s, expected=%s",
                    i,
                    found_vms,
                    num_vms,
                )
            # Unknown errors could be returned from minimega
            # so catch all possibilities.
            except Exception:
                self.log.debug(
                    "Iteration num=%s. Waiting for vm configs from minimega: exception",
                    i,
                )
                self.log.exception()
                continue
            if all_vms_launched:
                break

        assert all_vms_launched

        # If there is a control_net, tap it
        if self.control_net:
            mm_network_name = f"network-{switch_name_to_nid[self.control_net]}"
            mm_api.mm.tap_create_ip(mm_network_name, self.g.control_net["host_addr"])
        for vm_name, vm in core_vms.items():
            vm_map[vm_name] = vm["hostname"]

        def update_socket_path(process_config):
            original_socket_path = process_config["path"]
            socket_filename = os.path.basename(original_socket_path)
            mm_id = core_vms[process_config["vm_name"]]["id"]
            full_socket_path = os.path.join(mm_api.mm_base, mm_id, socket_filename)
            process_config["path"] = full_socket_path

        # Launch the vm_resource_handlers.
        launch_cmds = []
        for vm_name, vme_conf in vme_confs.items():
            try:
                process_config = vme_conf["aux"]["handler_process"]
            except KeyError:
                self.log.debug("no process_config for %s", vm_name)
                continue
            hostname = vm_map[vm_name]

            # Run the VM Resource Handler with the correct python path
            binary_name = sys.executable
            handler_path = process_config["binary_name"]
            update_socket_path(process_config)
            handler_args = json.dumps(process_config, separators=(",", ":"))
            if mm_api.cluster_head_node == hostname:
                # need to escape once on local commands
                handler_args = handler_args.replace('"', '\\"')
                launch_cmd = f"background {binary_name} {handler_path} '{handler_args}'"
            else:
                # need to escape twice on mesh send commands
                handler_args = handler_args.replace('"', '\\\\"')
                launch_cmd = str(
                    f"mesh send {hostname} background {binary_name} "
                    f"{handler_path} '{handler_args}'"
                )
            launch_cmds.append(launch_cmd)
        launch_cmds_path = os.path.join(
            fw_config["system"]["default_output_dir"], "launch_cmds.mm"
        )
        with open(launch_cmds_path, "w", encoding="UTF-8") as f_hand:
            for launch_cmd in launch_cmds:
                f_hand.write(launch_cmd + "\n")
        # Note that this uses the FIREWHEEL configuration to launch a new process
        # if there are not access controls on this file or the user accounts there
        # could be security concerns.
        launch_handlers_ret = subprocess.check_call(  # nosec
            [
                minimega_bin_path,
                f"-base={fw_config['minimega']['base_dir']}",
                "-e",
                "read",
                launch_cmds_path,
            ]
        )
        self.log.debug("launch_handlers_ret=%s", launch_handlers_ret)
