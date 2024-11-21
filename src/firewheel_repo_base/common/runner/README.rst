.. _common.runner_mc:

##############
common.runner
##############

.. warning::

    This Model Component is **DEPRECATED** and will be removed in a future release!

Provides the ``runner.py`` VM resource.

*************
``runner.py``
*************

Runner is written in using the FIREWHEEL v1.0 style and can be used with the :py:meth:`base_objects.VMEndpoint.add_vm_resource` method.
This has largely been replaced with :py:meth:`base_objects.VMEndpoint.run_executable` but remains for backwards compatibility.

This VM Resource will run an arbitrary program with the supplied arguments.
A pickled dictionary is passed in specifying the location of the program to run and the arguments that should be passed to it.

The program name should be passed in as the ``static_arg`` while the pickled dictionary of parameters is passed in as the ``dynamic_arg``.

The ``dynamic_arg`` input data structure:

.. code-block:: python

    # Example dictionary for running a program
    {
        'program_location': <path to program>,
        'arguments': <Optional, can be list or string of arguments that must be passed to the program>,
        'env': <Optional, dictionary with environment variables to pass to Popen>,
        'user': <Optional, username which runs the command>
        'cwd': <Optional, directory to run Popen command from>,
        'blocking': <Optional, specify if the runner should wait and check the error code returned from Popen>,
        'shell': <Optional: Indicate if the Popen process needs the shell>
    }
