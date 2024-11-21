.. _tests.qos_mc:

#########
tests.qos
#########

This model component bundles together the tools necessary to test the QoS (Quality of Service) parameters that can be set in FIREWHEEL to affect network link performance.
It will construct a simple topology with two VMs and connect them with a :py:class:`Switch <base_objects.Switch>`.
Then, depending on the input to the plugin, the specified QoS parameter is added to the edge.
This serves as an example of *how* QoS can be implemented in FIREWHEEL and is used in our functional test suite.

It includes two types of tests:

  * *delay* - This test sets the ``"delay"`` QoS parameter to add a 10 second delay to network traffic leaving a node.
    This is detectable via ping which is also called on each of the VMs as a part of of the ``qos_test.py`` VMR.
  * *drops* - This test sets the ``"packet_loss"`` QoS parameter to 50%.
    As such it is expected that about 50% of packets will be dropped.
    This too can be verified via ping which is called on each of the VMs as a part of the VMR.

.. note::
    The ``"throughput"`` QoS parameter is not demonstrated/tested with this MC.
    It may be added in the future.


**Attribute Provides:**
    * ``topology``

**Attribute Depends:**
    * ``graph``


**Model Component Dependencies:**
    * :ref:`base_objects_mc`
    * :ref:`linux.ubuntu1604_mc`
    * :ref:`vyos.helium118_mc`


******
Plugin
******

.. automodule:: tests.qos_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__


