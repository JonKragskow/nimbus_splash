.. _file_formats:

File Formats
============

.. _xyz_file_format:

``.xyz`` files
--------------

Splash expects a specific standard for ``.xyz`` files, and will exit with an error message if this standard is not followed.

A ``.xyz`` file should be formatted as follows

.. code-block::
   :caption: ``.xyz`` file format supported by ``nimbus_splash``

    NUMBER OF ATOMS (INTEGER)
    COMMENT LINE (CAN BE EMPTY)
    ATOMLABEL1 XCOORD YCOORD ZCOORD
    ATOMLABEL2 XCOORD YCOORD ZCOORD
    ATOMLABEL3 XCOORD YCOORD ZCOORD
    ...

Where the atom label consists only of letters, and all coordinates are in Angstrom.