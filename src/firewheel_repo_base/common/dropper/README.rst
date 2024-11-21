.. _common.dropper_mc:

##############
common.dropper
##############

.. warning::

    This Model Component is **DEPRECATED** and will be removed in a future release!

Provides the ``dropper.py`` VM resource.

**************
``dropper.py``
**************
Dropper is written in using the FIREWHEEL v1.0 style and can be used with the :py:meth:`base_objects.VMEndpoint.add_vm_resource` method.
This has largely been replaced with :py:meth:`base_objects.VMEndpoint.drop_content` and :py:meth:`base_objects.VMEndpoint.drop_file` but remains for backwards compatibility.

It will drop an arbitrary number of ASCII (i.e. text content) files and a single binary tarball.
A list of dictionaries is passed in as the ``dynamic_arg`` to describe what and where to drop files.
Additionally, the ``dynamic_arg`` content *must* be pickled.

The ``dynamic_arg`` input data structure:

.. code-block:: python

    [
        # Example dictionary for dropping a binary file
        {
            'binary_path': <directory of where to write the binary file>,
            'decompress': <True or False>
            'mode': <optionally give permissions for file as an integer, i.e. 0644>,
            'user': <optionally specify the user and group as a tuple, i.e. (1000,1000)>,
            'blocking': <optionally specify a directory that must exist before dropping files>
        },
    ]
    [
        # Example dictionary for dropping ASCII file
        {
            'contents': <contents of the ASCII file to be written to the VM>,
            'path': <path for where to write the content, including the filename)>,
            'mode': <optionally give permissions for file as an integer, i.e. 0644>,
            'user': <optionally specify the user and group as a tuple, ie. (1000,1000)>,
            'blocking': <optionally specify a directory that must exist before dropping files>
        }
        ...
    ]
