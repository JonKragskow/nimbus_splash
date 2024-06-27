.. _installation:

Installation
============

The ``nimbus_splash`` package and its command line interface are designed to be installed on Bath's `Nimbus` HPC system.

Unfortunately, the copy of ``python 3.8`` that comes as default on `Nimbus` is too old for ``nimbus_splash``, so instead 
it's better to use a newer version of ``python`` in an Anaconda ``conda`` environment.

Depending on your level of python knowledge, follow either the short instructions or the long instructions.

Short Instructions
------------------

1. Load Anaconda ``module load Anaconda3/2022.10`` - Optionally add this to your ``~/.bashrc`` file for automatic loading.
2. Create a ``conda`` environment or ``pyenv`` - Optionally set this to automatically load every time you log in using ``~/.bashrc``.
3. Install ``pip`` with ``conda install pip``.
4. Install ``nimbus_splash`` using ``pip``
5. Check your installation was sucessful with ``splash -h``. You should see a help screen.
6. Set the ``SPLASH_RAID`` environment variable to your Research Allocation ID in ``~/.bashrc`` - ``export SPLASH_RAID=<RA_ID_HERE>``
7. Optional: Set the ``SPLASH_EMAIL`` environment variable to your email address to get job updates ``~/.bashrc`` - ``export SPLASH_EMAIL=<Email_Here>``

Long Instructions
-----------------

To install ``splash``, you will need to create a ``conda`` environment. This contains a sandboxed installation of ``python``
that is separate from the system version, so if anything bad happens you can just delete the environment
and start again without affecting anything. You will then install ``splash`` to this environment.

Enabling Anaconda
^^^^^^^^^^^^^^^^^

First, log into `Nimbus`, and add the Anaconda ``module load`` command to ``~/.bashrc`` by doing the following.

Open your ``~/.bashrc`` file in ``nano`` using the following command

.. code-block::

    nano ~/.bashrc


Then go to the bottom of the file using your arrow keys or mouse, and paste in the following lines

.. code-block::

    module load Anaconda3/2022.10


Then save and exit nano using ``ctrl+o``, ``enter``, then ``ctrl+x``, and then run the command

.. code-block::

    source ~/.bashrc


to reload your ``bashrc`` file.

Creating a conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now create a ``conda`` environment called ``nimbus_base``, this is a sandboxed copy of ``python`` that you can use as a default and are free to mess around with in the knowledge that it can just be deleted if something breaks!

Run the following command

.. code-block::

    conda create -n nimbus_base


answering ``Y`` to any questions.

You'll probably get a message about initialising your shell for conda, so run

.. code-block::

    conda init bash


This adds some configuration information to your ``~/.bashrc``, to make sure it works properly, exit your ssh window (close the connection), and then reconnect to ``Nimbus``.

Upon reconnection, you should see the word ``(base)`` at the start of your terminal prompt. This is the ``base`` ``conda`` environment which you don't want to use.
To stop this ``base`` environment loading every time you open a shell, run the following command

.. code-block::

    conda config --set auto_activate_base false


and then deactivate this environment using

.. code-block::

    conda deactivate


Now ``(base)`` should be gone.

To instead start your new ``nimbus_base`` environment every time you connect, open ``~/.bashrc`` with
``nano``, and add the following to the bottom of the file.

.. code-block::

    conda activate nimbus_base


then save and exit nano using ``ctrl+o``, ``enter``, then ``ctrl+x``, and then run the command

.. code-block::

    source ~/.bashrc


in your terminal.

If everything is working correctly, ``(nimbus_base)`` will appear at the start of your prompt.

You now have a(n) (updatable) conda environment to use!

Now, to set up this environment and install ``python``, run the command

.. code-block::

    conda install pip


answering ``Y`` to any questions.

Installing ``nimbus_splash``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install ``nimbus_splash`` with

.. code-block::

    pip install nimbus_splash

installs ``nimbus_splash``.

Now, set your Research Allocation ID using the instructions below.

.. _raid :

Setting your Research Allocation ID
-----------------------------------

To select your Research Allocation ID, add the following environment variable in your nimbus
``~/.bashrc`` file and replace ``<name_here>`` with your Research Allocation ID.

.. code-block::

    export SPLASH_RAID=<name_here>

save and exit, and then run

.. code-block::

    source ~/.bashrc

If you don't do this, ``nimbus_splash`` will tell you to!


.. note::
    If you want to switch over to using a different Research Allocation ID, you'll need to update
    this line in ``~/.bashrc`` and run ``source ~/.bashrc``. Alternatively, you can temporarily change the value 
    for the current session by running ``export SPLASH_RAID=<name_here>`` in your terminal.

You're now ready to use ``nimbus_splash`` - head to :ref:`Usage <guide>` to get started.

.. _email :

Optional: Setting your notification email
-----------------------------------------

To recieve emails on your job status, add the following environment variable in your nimbus
``~/.bashrc`` file and replace ``<email_here>`` with your email address.

.. code-block::

    export SPLASH_EMAIL=<email_here>

