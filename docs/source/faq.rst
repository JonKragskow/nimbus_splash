.. _faq:

FAQ
---

This page contains some frequently asked questions. Please consult this page before raising a GitHub issue!

Errors ...
^^^^^^^^^^

... ``ValueError: .xyz file length/format is incorrect``

    Check your xyz file - and see :ref:`here <xyz_file_format>` for the format that splash expects.

... ``Please set $SPLASH_RAID environment variable``

    You need to set your Research Allocation ID environment variable - see :ref:`here <raid>`.

... ``Cannot open file '/apps/x86_64/modules/all/Anaconda3/2021.05' for 'reading'``

    Edit your ``~/.bashrc`` file and change ``module load Anaconda3/2021.05`` to ``module load Anaconda3/2022.10``
    Run ``source ~/.bashrc``, then ``conda init bash``. Finally, exit your session, and ``ssh`` into ``nimbus`` - you should now
    be able to use ``splash``.

I want to ...
^^^^^^^^^^^^^

... change my default compute instance

    See :ref:`here <instances>` for instructions.

... receive emails about my jobs

    See :ref:`here <email>` for instructions.
