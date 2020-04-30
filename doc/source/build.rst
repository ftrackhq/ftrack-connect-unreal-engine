..
    :copyright: Copyright (c) 2014-2020 ftrack

.. _build:


Build integration and documentation
===================================


Build Integration
-----------------

You can also build manually from the source for more control. First obtain a
copy of the source by either downloading the
`zipball <https://bitbucket.org/ftrack/ftrack-connect-unreal-engine/get/master.zip>`_ or
cloning the public repository::

    git clone git@bitbucket.org:ftrack/ftrack-connect-unity-engine.git

Then you can build and install the package into your current Python
site-packages folder::

    python setup.py build_plugin


Building documentation
----------------------

To build the documentation from source:

.. code::
    
    python setup.py build_sphinx

Then view in your browser::

    file:///path/to/ftrack-connect-unity-engine/build/doc/html/index.html



