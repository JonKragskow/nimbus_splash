Installation
============

The ``nimbus_splash`` package and its command line interface can be installed using the ``pip`` package manager ::

    pip install nimbus_splash

Unfortunately, the copy of ``python 3.8`` that comes as default on Nimbus is too old for ``nimbus_splash``, so instead 
it's better to use a newer version of ``python`` in an Anaconda ``conda`` environment.

A ``conda`` environment contains a sandboxed installation of ``python`` that is separate from the system version, so if anything bad happens you can just delete the environment and start again without affecting anything.

Loading Anaconda
----------------

First add the Anaconda module load to ``~/.bashrc``.

Open your ``~/.bashrc`` file in ``nano`` using the following command ::

    nano ~/.bashrc


Then go to the bottom of the file using your arrow keys or mouse, and paste in the following lines ::

    module load  Anaconda3/2021.05


Then save and exit nano using ``ctrl+o``, ``enter``, then ``ctrl+x``, and then run the command ::

    source ~/.bashrc


to reload your ``bashrc`` file.

Creating a conda environment
----------------------------

Now create a conda environment called ``nimbus_base``, this is a sandboxed copy of ``python`` that you can use as a default and are free to mess around with in the knowledge that it can just be deleted if something breaks!

Run the following command ::

    conda create -n nimbus_base


answering ``Y`` to any questions.

You'll probably get a message about initialising your shell for conda, so run ::

    conda init bash


This adds some configuration information to your ``~/.bashrc``, to make sure it works properly, exit your ssh window (close the connection), and then reconnect to ``Nimbus``.

Upon reconnection, you should see the word ``(base)`` at the start of your terminal prompt. This is the ``base`` conda environment which we don't want to use.
To stop this ``base`` environment loading every time you open a shell, run the following command ::

    conda config --set auto_activate_base false


and then deactivate this environment using ::

    conda deactivate


Now ``(base)`` should be gone.

To instead start your new ``nimbus_base`` environment every time you connect, open ``~/.bashrc`` with
``nano``, and add the following to the bottom of the file. ::

    conda activate nimbus_base


then save and exit ``nano``, and run the command ::

    source ~/.bashrc


in your terminal.

If everything is working correctly, ``(nimbus_base)`` will appear at the start of your prompt.

You now have a(n) (updatable) conda environment to use!

Now, to set up this environment and install ``python``, run the command ::

    conda install pip


answering ``Y`` to any questions.

And finally, install any ``python`` package you like using ::

    pip install NAME


e.g. ::

    pip install nimbus_splash


installs ``nimbus_splash``.

Setting your Research Allocation ID
-----------------------------------

To select your Research Allocation ID, add the following environment variable in your nimbus
``~/.bash_rc`` file and replace ``<name_here>`` with your Research Allocation ID ::

    export CLOUD_ACC=<name_here>


If you don't do this, ``nimbus_splash`` will tell you to.