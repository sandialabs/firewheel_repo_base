.. _misc.print_graph_mc:

################
misc.print_graph
################

This MC outputs a text or `GEXF <http://gexf.net>`__ representation of the :ref:`experiment-graph`.
If a filename is passed into the plugin, then a custom test representation of the graph will be placed in the file; otherwise, it will print the graph to ``stdout`` using :py:func:`networkx.readwrite.text.write_network_text`.
If the file extension is ``.gexf``, then the resulting output will be in GEXF file format and can then be viewed in a tool such as `Gephi <https://gephi.org/>`__.

This MC can be placed in multiple locations of the experiment pipeline so that users can see different views of how the experiment graph is evolving.

**Attribute Depends:**
    * ``graph``

***********
Text Format
***********

If an unknown file extension is provided, a human-readable text representation is output into that file.
It includes all graph :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` objects and prints the following information:

* All the decorators of that :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
* All neighbors (i.e., connected :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` objects).
* Any :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` attributes.
* All :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` methods.

Each :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` is identified by its ``graph_id`` (an integer).

Example
=======

Below is example output for one of the nodes in our :ref:`tests.router_tree_mc` topology.
You can see similar results by using::

    firewheel experiment tests.router_tree:3 misc.print_graph:out.txt

.. code-block::
    :caption: Partial output from ``misc.print_graph``.

    NODE 12
    DECORATED BY: AbstractUnixEndpoint LinuxHost VMEndpoint
    NEIGHBORS:
        15
    ATTRIBUTES:
        decorators: [<class 'linux.base_objects.LinuxHost'>, <class 'base_objects.VMEndpoint'>, <class 'base_objects.AbstractUnixEndpoint'>]
        skip_list: ['__dict__', '__module__', '__weakref__', '__class__', '__doc__', '__init__']
        g: <firewheel.control.experiment_graph.ExperimentGraph object at 0x7f15986b3eb8>
        graph_id: 12
        valid: True
        log: <Logger ExperimentGraphVertex (DEBUG)>
        name: host.leaf-1.net
        vm: {}
        type: host
        vm_resource_schedule: [
        <class 'firewheel.vm_resource_manager.schedule_entry.ScheduleEntry'>(
        start_time=-250,
        executable=set_hostname.sh,
        arguments=host.leaf-1.net,
        data=[{'location': 'set_hostname.sh', 'filename': 'set_hostname.sh', 'executable': True}]
        ),
        ]
        interfaces: [
        {'address': '10.0.2.2',
        'name': 'eth0',
        'netmask': '255.255.255.0',
        'network': '10.0.2.2/24',
        'qos': {'delay': None, 'loss': None, 'rate': None},
        'switch': 'switch-host-ospf.leaf-1.net'}
        ]
        default_gateway: 10.0.2.1
    METHODS:
        configure_ips
        set_hostname
        _connect
        set_default_gateway
        add_vm_resource
        connect
        drop_content
        drop_file
        file_transfer
        file_transfer_once
        l2_connect
        run_executable
        set_image

***********
GEXF Format
***********
If the passed in file extension is ``.gexf`` than a GEXF file is output.
Each :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` is identified by its ``name`` and the following attributes/information is included:

* Basic node information - Name, Graph ID, etc.
* All the classes which decorated that :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>`.
* Any "important" :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` attributes (e.g. in ``{"vm", "vm_resource_schedule", "host", "type", "interfaces"}``).
* A color/shape attribute depending on the ``type``. The current mapping is: yellow triangle for type ``switch``, fuchsia square for type ``host``, and aqua circle for type ``router``.

  .. note::

    The shape attribute is not currently supported in Gephi.
    See https://github.com/gephi/gephi/issues/1083 for details.

Each :py:class:`Edge <firewheel.control.experiment_graph.Edge>` will contain the following information:

* The source and destination :py:class:`Vertex <firewheel.control.experiment_graph.Vertex>` objects.
* All the classes which decorated that :py:class:`Edge <firewheel.control.experiment_graph.Edge>`.
* Any "important" :py:class:`Edge <firewheel.control.experiment_graph.Edge>` attributes (e.g. in ``{"dst_ip", "dst_network", "qos"}``).
* The network information.


******
Plugin
******

.. automodule:: misc.print_graph_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
