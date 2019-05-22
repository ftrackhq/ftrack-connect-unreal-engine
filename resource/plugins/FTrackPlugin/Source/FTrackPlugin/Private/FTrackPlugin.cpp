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
#if WITH_EDITOR
		TSet<FName>& GlobalTagsForAssetRegistry = UObject::GetMetaDataTagsForAssetRegistry();
		if (!GlobalTagsForAssetRegistry.Contains(FName("ftrack.IntegrationVersion")))
		{
			GlobalTagsForAssetRegistry.Add(FName("ftrack.IntegrationVersion"));
		}
		if (!GlobalTagsForAssetRegistry.Contains(FName("ftrack.AssetComponentId")))
		{
			GlobalTagsForAssetRegistry.Add(FName("ftrack.AssetComponentId"));
		}
		if (!GlobalTagsForAssetRegistry.Contains(FName("ftrack.AssetVersionId")))
		{
			GlobalTagsForAssetRegistry.Add(FName("ftrack.AssetVersionId"));
		}
		if (!GlobalTagsForAssetRegistry.Contains(FName("ftrack.ComponentName")))
		{
			GlobalTagsForAssetRegistry.Add(FName("ftrack.ComponentName"));
		}
		if (!GlobalTagsForAssetRegistry.Contains(FName("ftrack.AssetId")))
		{
			GlobalTagsForAssetRegistry.Add(FName("ftrack.AssetId"));
		}
		if (!GlobalTagsForAssetRegistry.Contains(FName("ftrack.AssetType")))
		{
			GlobalTagsForAssetRegistry.Add(FName("ftrack.AssetType"));
		}
#endif
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



