// Copyright 2019 ftrack. All Rights Reserved.

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"
#include "IFTrackPlugin.h"
#include "FTrackUIManager.h"


class FTrackPlugin : public IFTrackPlugin
{
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};

IMPLEMENT_MODULE( FTrackPlugin, FTrackPlugin )


void FTrackPlugin::StartupModule()
{
	if (GIsEditor)
	{
		FTrackUIManager::Initialize();
	}
}


void FTrackPlugin::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
	if (GIsEditor)
	{
		FTrackUIManager::Shutdown();
	}
}



