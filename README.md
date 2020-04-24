Unreal Engine 4 ftrack Integration
===========================
This is an ftrack-connect-unreal integration with Unreal Engine using a UE4 C++ plugin FTrackConnect.

Supported Platforms
-------------------
* Currently supported on Windows 10.
* Is being developed against and supprot for now is limited to Unreal Engine 4.22 (requires a c++ project)
* Compatible with ftrack-connect-package 1.1.0 - 1.1.2


building the integration
------------------------

* clone the repository
* run : python setup.py build_plugin 


Installation
------------
#### 1. Setup ftrack_connect_unreal 

* Copy the plugin to the plugin directory http://ftrack-connect.rtd.ftrack.com/en/stable/using/plugin_directory.html

#### 2. Setup ftrack unreal project plugin

* Copy folder FTrackPlugin from 'resource/plugins' to your UE4 project plugins folder(i.e.: MyProject/Plugins).
* Note: for now only the code is provided which will require to start the project once to recompile the plugin prior to being able to use it.


Done!
-----
* Launch ftrack connect and choose a project and a task now you should see Unreal Engine's launcher icon. 
* Launch Unreal Engine then Launch your project and you should see ftrack in the toolbar


known limitations
-----------------

**publishing**


Due to the limitation of the the current system, publishers for other assets types (eg: geometry, rig etc...)
will be shown on asset level, but won't be working.

Is Currently possible to publish only image_sequence asset (see documentation for details).

