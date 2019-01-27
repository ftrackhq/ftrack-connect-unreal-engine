Ftrack Unreal Engine 4 Integration
===========================

Supported Platforms
-------------------
Currently supported on Windows 10.
Has been built and tested through Unreal Engine 4.18 - 4.20.
Compatible with ftrack-connect-package 0.7.2 - 1.1.0

# Dependencies
| Name | Version | Optional |
| ---- | ------- | :------: |
| UnrealEnginePython (https://github.com/20tab/UnrealEnginePython)        | latest version | built with Python 2.7.14 |

# Installation
#### 1. Setup ftrack_connect_unreal main module

Put 'ftrack_connect_unreal' from 'common.zip' folder into ftrack-connect-package's 'common.zip'.
So you will have for exmaple: C:\Program Files (x86)\ftrack-connect-package-0.7.1\common.zip\ftrack_connect_unreal

#### 2. Setup ftrack_connect_unreal resource

Copy contents from 'resource' folder to ftrack-connect-package's 'resource' folder.

#### 3. Setup Ftrack Unreal Engine Startup

Set python script path in Unreal's engine config, so ftrack plugin will be initialized when Unreal launched.

Add following code in DefaultEngine.ini:

```sh
[Python]
ScriptsPath = UNREAL-PYTHONSCRIPT-PATH
```
For example:

```
[Python]
ScriptsPath = "C:/Program Files (x86)/ftrack-connect-package-0.7.1/resource/ftrack_connect_unreal/scripts"
```

* Done!