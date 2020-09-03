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

Building ftrack unreal project plugin
----------------------------------

In case of a new version of Unreal Engine is released, and the plugin result incompatible, the plugin can be manually recopiled.
The plugin sources are stored with the integration itself and available under the **'resource/plugins'** folder.

.. note:: 
    This process will require to have the `windows development kit <https://developer.microsoft.com/en-us/windows/downloads/windows-10-sdk/>`_ installed.

1) Start Unreal engine with connect
2) Create a c++ project
3) Copy Plugin **FTrackPlugin** from **'resource/plugins'** to your UE4 project plugins folder (i.e.: MyProject/Plugins)
4) Restart the unreal through ftrack-connect. This will trigger the re compilation of the plugin for your current version.

Once compiled you can save the `compiled package <https://docs.unrealengine.com/en-US/Programming/Plugins/index.html>`_ through the Unreal plugin window, 
using the same procedure used to Distribute the plugin to the Epic Marketplace.


known limitations
-----------------

**publishing**

Due to the limitation of the the current system, publishers for other assets types (eg: geometry, rig etc...)
will be shown on asset level, but won't be working.

Is Currently possible to publish only image_sequence asset (see documentation for details) on shot level.
