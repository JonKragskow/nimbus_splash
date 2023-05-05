Submitting a Job
================

Using ``splash``, you can submit an ORCA job on Nimbus using only an ORCA input file, a ``.xyz`` file, and a single command.

First, prepare your input file. As an example, this is an input file for a geometry optimisation and frequency calculation of benzene

.. code-block::
   :caption: ``benzene.inp``

    !PBE def2-svp OPT FREQ
    %PAL NPROCS 16 END
    %maxcore 2000
    *xyzfile 0 1 benzene.xyz


Notice, the number of cores and maximum per-core memory have been specified.
Additionally, the structure cannot be present in the input, but is instead located in a separate file, in this case ``benzene.xyz``

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


To submit a job for this calculation, simply run ::
    
    splash gen_job benzene.inp

You should then see an message informing you that a submission script was created and subsequently submitted.

The job will be given the same name as your input file, and output file for this calculation should appear in the current directory when the job starts running.

When the calculation has finished, been evicted, timed-out, or otherwise halted, you should see a new directory named in the same location as your input and ``.xyz`` files.
This directory will be named ``<jobname>_results`` and will contain all the files ORCA creates. 


Providing Input Orbitals
------------------------

When resuming a job, ORCA automatically searches for a ``.gbw`` file with the same name as your input file.
To support this, ``splash`` checks for a ``<jobname>_results`` directory whenever you run ``splash gen_job`` and
copies the ``<jobname>.gbw`` file to the compute node's scratch space. This feature can be disabled with the 
``--no_guess`` argument, e.g. ::

    splash gen_job benzene.inp --no_guess


To provide a different set of orbitals to ORCA, make sure you have both the ``MORead`` keyword, and ``%moinp "<gbw_filename>"`` line in
your input file. Note that ORCA will not allow ``<gbw_filename>`` have the same name head as the input file.

For the benzene example above, a correct input file would be

.. code-block::
   :caption: ``benzene.inp`` with specified orbital file

    !PBE def2-svp OPT FREQ MORead
    %moinp "new_orbs.gbw"
    %PAL NPROCS 16 END
    %maxcore 2000
    *xyzfile 0 1 benzene.xyz


The file ``<gbw_filename>`` can be located either in ``<jobname>_results`` or in the same directory as the input file.


Submitting multiple jobs
------------------------

You can submit more than one calculation at once by providing more than one input file to splash. For example ::

    splash gen_job input_1.slm input_2.slm


You can even use a wildcard to submit jobs without typing each filename out ::

    splash gen_job input_*.slm

Compute instances
-----------------

Different compute instances can be requested using the ``--node_type`` option.

The full list of instances currently known to splash are ::

    spot-fsv2-2
    spot-fsv2-4
    spot-fsv2-8
    spot-fsv2-16
    spot-fsv2-32
    paygo-fsv2-2
    paygo-fsv2-4
    paygo-fsv2-8
    paygo-fsv2-16
    paygo-fsv2-32
    paygo-hb-60
    paygo-hbv2-120
    paygo-hbv3-120
    paygo-hc-44
    paygo-ncv3-12
    paygo-ncv3-24
    paygo-ncv3-6
    paygo-ncv3r-24
    paygo-ndv2-40
    spot-hb-60
    spot-hbv2-120
    spot-hbv3-120
    spot-hc-44
    spot-ncv3-12
    spot-ncv3-24
    spot-ncv3-6
    spot-ncv3r-24
    spot-ndv2-40
    vis-ncv3-12
    vis-ncv3-24
    vis-ncv3-6
    vis-ndv2-4

Note, you can only use instances to which you have been granted access.
If you get a ``QOS`` error, please check your account on the RCAM portal.

More
----

Additional command line arguments for ``splash gen_job`` can be listed by running ::

    splash gen_job -h