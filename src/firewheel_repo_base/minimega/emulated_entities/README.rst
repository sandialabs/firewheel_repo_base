.. _minimega.emulated_entities_mc:

##########################
minimega.emulated_entities
##########################

This MC provides the :py:class:`MinimegaEmulatedVM <minimega.emulated_entities.MinimegaEmulatedVM>` object which has methods for generating a large dictionary of parameters which can be eventually
passed to minimega to start the experiment.

*************
Sample Output
*************

The :py:meth:`generate_minimega_config() <minimega.emulated_entities.MinimegaEmulatedVM.generate_minimega_config>` method is used to generate a large dictionary which contains all necessary information to start a minimega experiment.
Below is an example dictionary from this method for the ``host.root.net`` VM which is created by the :ref:`tests.router_tree_mc` model component.

.. code-block:: json

    {
        "aux": {
            "qemu_append": {},
            "control_ip": "",
            "power_state": "running",
            "nic": [
                {
                    "name": "nic",
                    "id": "if0",
                    "switch_name": "switch-host-ospf.root.net",
                    "type": "tap",
                    "driver": "virtio-net-pci",
                    "mac": "00:00:00:00:00:01",
                    "qos": {
                        "loss": null,
                        "delay": null,
                        "rate": null
                    },
                    "ip": "10.0.0.2/24"
                }
            ],
            "disks": [
                {
                    "name": "drive",
                    "id": "drv0",
                    "file": "ubuntu-16.04.4-server-amd64.qcow2",
                    "path": "images/ubuntu-16.04.4-server-amd64.qcow2",
                    "db_path": "ubuntu-16.04.4-server-amd64.qcow2.xz",
                    "interface": "virtio",
                    "cache": "writeback"
                }
            ],
            "qemu_append_str": "",
            "qga_config": {
                "name": "serial",
                "id": "minimegaqga",
                "path": "/tmp/minimega/namespaces/firewheel/8c993d3a-2cf7-4429-8e98-75b16c2cd26c/virtio-serial0"
            },
            "minimegaqmp": {
                "name": "qmp",
                "id": "minimegaqmp",
                "path": "/tmp/minimega/namespaces/firewheel/8c993d3a-2cf7-4429-8e98-75b16c2cd26c/qmp"
            },
            "handler_process": {
                "type": "Process",
                "engine": "QemuVM",
                "uuid": "e5dce01d-ce00-4fe4-a84b-3569ef007a57",
                "vm_name": "host.root.net",
                "vm_uuid": "8c993d3a-2cf7-4429-8e98-75b16c2cd26c",
                "binary_name": "/opt/firewheel/src/firewheel/vm_resource_manager/vm_resource_handler.py",
                "path": "/tmp/minimega/namespaces/firewheel/8c993d3a-2cf7-4429-8e98-75b16c2cd26c/virtio-serial0"
            }
        },
        "vm": {
            "uuid": "8c993d3a-2cf7-4429-8e98-75b16c2cd26c",
            "type": "QemuVM",
            "architecture": "x86_64",
            "name": "host.root.net",
            "image": "ubuntu1604server",
            "vcpu_model": "qemu64",
            "smp_name": "smp",
            "smp_id": "smp",
            "smp_sockets": 1,
            "smp_cores": 1,
            "smp_threads": 1,
            "memory": "256",
            "vga_model": "std"
        },
        "coschedule": -1,
        "tags": {}
    }

********************
VM Host Distribution
********************

There may be times where the performance of some VMs is particularly important, and resource contention can cause problems with experiments.
The number of VMs that share a host with a particular VM can be controlled using the :py:attr:`coschedule <base_objects.VMEndpoint.coschedule>` attribute.
Setting this value to ``0`` means that the VM is run on its own host.
Setting this value to ``-1`` (default) means run the default scheduling (no limit on how many other VMs are on the same host).

*****************
Available Objects
*****************

.. automodule:: minimega.emulated_entities
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__

