#include "FTrackConnect.h"

#include "AssetRegistryModule.h"
#include "IAssetRegistry.h"

#include "GameFramework/Actor.h"
#include "IPythonScriptPlugin.h"
#include "Misc/CoreDelegates.h"
#include "Misc/Paths.h"
#include "Templates/Casts.h"
#include "UObject/UObjectHash.h"

UFTrackConnect* UFTrackConnect::GetInstance()
{
	// The Python FTrack Connect instance must come from a Python class derived from UFTrackConnect
	// In Python, there should be only one derivation, but hot-reloading will create new derived classes, so use the last one
	TArray<UClass*> FTrackConnectClasses;
	GetDerivedClasses(UFTrackConnect::StaticClass(), FTrackConnectClasses);
	int32 NumClasses = FTrackConnectClasses.Num();
	if (NumClasses > 0)
	{
		return Cast<UFTrackConnect>(FTrackConnectClasses[NumClasses - 1]->GetDefaultObject());
	}
	return nullptr;
}

static void OnEditorExit()
{
	if (UFTrackConnect* Connect = UFTrackConnect::GetInstance())
	{
		Connect->Shutdown();
	}
}

void UFTrackConnect::OnConnectInitialized() const
{
	IPythonScriptPlugin::Get()->OnPythonShutdown().AddStatic(OnEditorExit);
}

void UFTrackConnect::AddGlobalTagInAssetRegistry(const FString& tag) const
{
#if WITH_EDITOR
	FName tagName(*tag);
	TSet<FName>& GlobalTagsForAssetRegistry = UObject::GetMetaDataTagsForAssetRegistry();
	if (!GlobalTagsForAssetRegistry.Contains(tagName))
	{
		GlobalTagsForAssetRegistry.Add(tagName);
	}
#endif
}
