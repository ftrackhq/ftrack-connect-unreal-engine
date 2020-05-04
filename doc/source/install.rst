..
    :copyright: Copyright (c) 2014-2020 ftrack

.. _install:

Supported Platforms
===================

* Currently supported on Windows 10.
* Compatible with ftrack-connect-package 1.1.0 - 1.1.2


Setup and Install 
=================

In here you'll be able to find the documentation on how to install the integration.

install integration
-------------------

Whether you have been downloading the integration or built yourself, 
copy the uncompressed folder in the **%FTRACK_CONNECT_PLUGIN_PATH%**

You can find more information on how to locate it in the `ftrack help page <https://help.ftrack.com/connect/getting-started-with-connect/installing-and-using-connect>`_

Setup ftrack unreal project plugin
----------------------------------
(beta and rc release only)
Copy Binary Plugin FTrackPlugin from 'resource/plugins' to your UE4 project plugins folder(i.e.: MyProject/Plugins).

known limitations
-----------------

**publishing**

Due to the limitation of the the current system, publishers for other assets types (eg: geometry, rig etc...)
will be shown on asset level, but won't be working.

Is Currently possible to publish only image_sequence asset (see documentation for details) on shot level.
