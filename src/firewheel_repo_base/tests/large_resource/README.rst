.. _tests.large_resource_mc:

####################
tests.large_resource
####################


This MC generates a new binary file, gets its hash, and then drop both the binary and the ``hash_compare.py`` VMR on every VM in the experiment.
The size of the generated binary can be passed in (using bytes), but the default is ``1048576`` (i.e. 1 MB).
This MC is mainly useful for functional testing of FIREWHEEL.

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`base_objects_mc`

******
Plugin
******

.. automodule:: tests.large_resource_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
