# ftrack-connect-unreal
Unreal Engine 4 integration with ftrack.

Tested in Unreal Engine 4.19 and 4.20 within Window 10.

# Installation

* Install UnrealEnginePython (https://github.com/20tab/UnrealEnginePython)

Make sure you have latest version installed.

* Copy contents of source folder to your ftrack-connect common folder.

Create a folder named 'ftrack_connect_unreal' under ftrack-connect 'common' folder. Then copy 'source' folder's contents to it.
The default path is: C:\Program Files (x86)\ftrack-connect-package-0.7.1\common\ftrack_connect_unreal

* Copy hook file to your ftrack-connect hook folder.

Copy resource/hook/ftrack_connect_unreal_hook.py to your ftrack-connect 'hook' folder.

The default path is: C:\Program Files (x86)\ftrack-connect-package-0.7.1\resource\hook

* Copy scripts to your ftrack-connect resource folder.

Copy resource/scripts to your ftrack-connect 'resource' folder.

Create a folder named 'ftrack_connect_unreal' under ftrack-connect's resource folder. Then copy resource/scripts to it.

* Setup DefaultEngine.ini for your Unreal project

Setup python path in your Unreal project DefaultEngine.ini, so ftrack plugin will be initialized when Unreal start.

Add following code in DefaultEngine.ini:

```sh
[Python]
ScriptsPath = YOUR ftrack_connect_unreal/scripts PATH
```
By default, it should be like this:

```
[Python]
ScriptsPath = "C:/Program Files (x86)/ftrack-connect-package-0.7.1/resource/track_connect_unreal/scripts"
```

* Done!