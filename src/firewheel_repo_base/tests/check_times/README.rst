.. _tests.check_times_mc:

#################
tests.check_times
#################

This MC is intended for use with the functional test case which verifies that the actual time a VMR is started is approximately the VMRs specified :ref:`start-time`.
It adds the ``check_time.sh`` VM resource to all VMs in the experiment.
This VMR simply prints the current time to a file (which will be retrieved and checked by the test case).
The ``check_time.sh`` VMR will run at time=30.

**Attribute Provides:**
    * ``check_times``

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: tests.check_times_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
