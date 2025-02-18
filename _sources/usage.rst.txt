.. _submission:

Submitting a job
----------------

Using ``splash``, you can easily submit an ``ORCA`` job to `Nimbus` using only an ``ORCA`` input file and a single terminal command.

.. code-block:: console

    splash submit <input_file>

Example Submission
==================

In the following example, we submit a geometry optimisation calculation for a benzene molecule.

First, prepare the input file.

.. code-block::
   :caption: ``benzene.inp``

    !BP86 def2-svp OPT
    %PAL NPROCS 16 END
    %maxcore 2000
    *xyzfile 0 1 benzene.xyz

In this example the structure is located in a separate ``.xyz`` file - ``benzene.xyz``.

.. code-block::
   :caption: ``benzene.xyz``

    12
    Benzene
    H      1.2194     -0.1652      2.1600
    C      0.6825     -0.0924      1.2087
    C     -0.7075     -0.0352      1.1973
    H     -1.2644     -0.0630      2.1393
    C     -1.3898      0.0572     -0.0114
    H     -2.4836      0.1021     -0.0204
    C     -0.6824      0.0925     -1.2088
    H     -1.2194      0.1652     -2.1599
    C      0.7075      0.0352     -1.1973
    H      1.2641      0.0628     -2.1395
    C      1.3899     -0.0572      0.0114
    H      2.4836     -0.1022      0.0205

To submit a job for this calculation, simply run

.. code-block:: console

    splash submit benzene.inp


You should then see an message informing you that a submission script was created and subsequently submitted.

The job will be given the same name as your input file, and the output file for this calculation should appear in the current directory when the job starts running - for example

.. code-block:: console

    user@nimbus-1-login-1 ~/benzene $ ls
    benzene.6718675.e  benzene.6718675.o  benzene.inp  benzene.out  benzene.slm  benzene.xyz


When the calculation has finished, been evicted, timed-out, or otherwise halted, you should see a new directory in the same location as your input and ``.xyz`` files.
This directory will be named ``<jobname>_results`` and will contain all of the files that ``ORCA`` has created. 

.. code-block:: console

    user@nimbus-1-login-1 ~/benzene $ ls
    benzene.6718675.e  benzene.6718675.o  ... benzene.xyz  benzene_results

Submitting multiple jobs
========================

You can submit more than one calculation at once by providing more than one input file to ``splash``. For example ::

    splash submit input_1.inp input_2.inp

You can even use a wildcard to submit jobs without typing each filename out ::

    splash submit input_*.inp

Note that this will run all jobs in the current directory, and so can produce a large number of files in the same directory.


Coordinates within ``.inp`` files
=================================

Instead of providing a separate ``.xyz`` file, it is possible to specify coordinates within the ``ORCA`` input file.

This feature is supported by ``splash`` and requires no additional effort on the part of the user.

Providing input orbitals
========================

To provide ``ORCA`` with a set of orbitals, make sure you have both the ``MORead`` keyword and the ``%moinp "<gbw_filename>"`` line in
your input file. Note that ``ORCA`` will not allow your specified file to have the same name-stem as the input file.

For the benzene example in the previous section, a correct input file would be

.. code-block::
   :caption: ``benzene.inp`` with input orbitals specified

    !BP86 def2-svp OPT FREQ MORead
    %moinp "new_orbs.gbw"
    %PAL NPROCS 16 END
    %maxcore 2000
    *xyzfile 0 1 benzene.xyz


The file ``<gbw_filename>`` must be in the same directory as the input file, and cannot contain any path information.

.. _instances :

Selecting a compute instance
============================

Specific `Nimbus` compute instances can be requested using the ``--instance`` option.

The full list of ``ORCA`` compatible instances currently known to ``splash`` are ::

    spot-fsv2-2
    spot-fsv2-4
    spot-fsv2-8
    spot-fsv2-16
    spot-fsv2-32
    spot-hc-44
    spot-hbv2-120
    spot-hbv3-120
    paygo-fsv2-2
    paygo-fsv2-4
    paygo-fsv2-8
    paygo-fsv2-16
    paygo-fsv2-32
    paygo-hc-44
    paygo-hbv3-120


.. note::

    You can only use instances to which you have been granted access.
    This is usually indicated by a ``QOS`` error at submission time. To resolve this, modify your access
    on the `RCAM <https://rcam.bath.ac.uk/>`_ portal.

By default, ``splash`` submits to ``spot-fsv2-16`` which has 16 cores and 2GB RAM per core, to change this default for your account
add the following to your ``~/.bash_rc`` file, where ``<instance>`` is one of those given above ::

    export SPLASH_DEFAULT_INSTANCE=<instance>

Selecting an ORCA version
=========================

Several versions of ORCA are available on `Nimbus` - use ``module check <INSTANCE_NAME> ORCA`` to see the ORCA versions available for a given instance.

.. note::

    You might get an error about ``termcolor`` when using ``module check``. If you do, run ``pip install termcolor`` and then try again!


.. warning::

    Beware: Not all `Nimbus` instances have access to the same ``ORCA`` versions.

``splash`` contains its own internal list of ORCA modules which can be printed with the ``splash orca_modules`` command. This list is periodically updated when new 
versions of ORCA are installed on `Nimbus`, please raise a `GitHub Issue <https://github.com/jonkragskow/nimbus_splash/issues>`_ to have new modules added to ``splash``'s list.

By default, ``splash`` will use the most recent version of ORCA (``6.0.1``), but a different version can be selected with
the ``--orca_version <VALUE>`` optional argument.

Alternatively, to select a new default ORCA version and avoid having to enter this optional argument constantly,
add the following to your ``~/.bash_rc`` file, where ``<version>`` is the version number, e.g.  ``6.0.0`` ::

    export SPLASH_ORCA_VERSION=<version>

More
====

Additional command line arguments for ``splash submit`` can be listed by running ::

    splash submit -h