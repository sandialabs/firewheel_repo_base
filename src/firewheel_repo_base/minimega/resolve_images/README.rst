.. _minimega.resolve_vm_images_mc:

##########################
minimega.resolve_vm_images
##########################

This MC ensures that all VMs have an image available.
That is, if any VMs have not had an image assigned explicitly, this MC will assign a default image.
Additionally, it will decorate all VMs with :py:class:`minimega.emulated_entities.MinimegaEmulatedVM`.

The default image types are:

* If the VM type is ``host`` is: :py:class:`Ubuntu1604Server <linux.ubuntu1604.Ubuntu1604Server>`.
* If the VM type is ``router`` is: :py:class:`Helium118 <vyos.helium118.Helium118>`.
* If the VM type is ``switch`` is: :py:class:`Ubuntu1604Server <linux.ubuntu1604.Ubuntu1604Server>`.

.. note::
    Most :py:class:`Switches <base_objects.Switch>` are **not** decorated with :py:class:`VMEndpoint <base_objects.VMEndpoint>` and are not launched as a VM.

**Attribute Provides:**
    * ``vm_image_details``

**Attribute Depends:**
    * ``topology``

**Model Component Dependencies:**
    * :ref:`linux.ubuntu1604_mc`
    * :ref:`vyos.helium118_mc`
    * :ref:`minimega.emulated_entities_mc`

******
Plugin
******

.. automodule:: minimega.resolve_vm_images_plugin
    :members:
    :undoc-members:
    :special-members:
    :private-members:
    :show-inheritance:
    :exclude-members: __dict__,__weakref__,__module__
