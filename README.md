Unreal Engine 4 ftrack Integration
===========================
This is an ftrack-connect-unreal integration with Unreal Engine using a UE4 C++ plugin FTrackConnect.

Supported Platforms
-------------------
* Currently supported on Windows 10.
* Is being developed against  Unreal Engine 4.22.
* Compatible with ftrack-connect-package 0.7.2 - 1.1.0


Installation
------------
#### 1. Setup ftrack_connect_unreal 

* Copy the plugin to the plugin directory http://ftrack-connect.rtd.ftrack.com/en/stable/using/plugin_directory.html

#### 2. Setup ftrack unreal project plugin

* Copy folder FTrackPlugin from 'resource/plugins' to your UE4 project plugins folder(i.e.: MyProject/Plugins).
* Note: for now only the code is provided which will require to start the project once to recompile the plugin prior to being able to use it.


Done!
------------
* Launch ftrack connect and choose a project and a task now you should see Unreal Engine's launcher icon. 
* Launch Unreal Engine then Launch your project and you should see ftrack in the toolbar