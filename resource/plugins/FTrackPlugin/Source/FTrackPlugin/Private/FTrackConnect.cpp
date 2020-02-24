#include "FTrackConnect.h"

#include "AssetRegistryModule.h"
#include "IAssetRegistry.h"

#include "AssetToolsModule.h"
#include "IAssetTools.h"

#include "GameFramework/Actor.h"
#include "IPythonScriptPlugin.h"
#include "Misc/CoreDelegates.h"
#include "Misc/Paths.h"
#include "Templates/Casts.h"
#include "UObject/UObjectHash.h"

DEFINE_LOG_CATEGORY(FTrackLog);

UFTrackConnect *UFTrackConnect::GetInstance()
{
	// The Python FTrack Connect instance must come from a Python class derived from UFTrackConnect
	// In Python, there should be only one derivation, but hot-reloading will create new derived classes, so use the last one
	TArray<UClass *> FTrackConnectClasses;
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
	if (UFTrackConnect *Connect = UFTrackConnect::GetInstance())
	{
		Connect->Shutdown();
	}
}

void UFTrackConnect::OnConnectInitialized() const
{
	IPythonScriptPlugin::Get()->OnPythonShutdown().AddStatic(OnEditorExit);
}

void UFTrackConnect::AddGlobalTagInAssetRegistry(const FString &tag) const
{
#if WITH_EDITOR
	FName tagName(*tag);
	TSet<FName> &GlobalTagsForAssetRegistry = UObject::GetMetaDataTagsForAssetRegistry();
	if (!GlobalTagsForAssetRegistry.Contains(tagName))
	{
		GlobalTagsForAssetRegistry.Add(tagName);
	}
#endif
}

void UFTrackConnect::RecursiveGetDependencies(const FName& PackageName, TSet<FName>& AllDependencies) const
{
	FAssetRegistryModule& AssetRegistryModule = FModuleManager::Get().LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
	TArray<FName> Dependencies;
	
	// Recursively fetch the dependencies of the given package
	AssetRegistryModule.Get().GetDependencies(PackageName, Dependencies);

	for (auto DependsIt = Dependencies.CreateConstIterator(); DependsIt; ++DependsIt)
	{
		if (!AllDependencies.Contains(*DependsIt))
		{
			// Skip engine and script content
			const bool bIsEnginePackage = (*DependsIt).ToString().StartsWith(TEXT("/Engine"));
			const bool bIsScriptPackage = (*DependsIt).ToString().StartsWith(TEXT("/Script"));
			if (!bIsEnginePackage && !bIsScriptPackage)
			{
				AllDependencies.Add(*DependsIt);
				RecursiveGetDependencies(*DependsIt, AllDependencies);
			}
		}
	}
}

void UFTrackConnect::MigratePackages(const FString &package_name, const FString &output_folder) const
{
#if WITH_EDITOR
	FName umapPackageName(*package_name);

	TSet<FName> AllPackageNamesToMove;
	AllPackageNamesToMove.Add(umapPackageName);

	// Fetch the dependencies of the umap level file:
	RecursiveGetDependencies(umapPackageName, AllPackageNamesToMove);

	if (AllPackageNamesToMove.Num() != 0)
	{
		// Copy all specified assets and their dependencies to the destination folder
		for (auto PackageIt = AllPackageNamesToMove.CreateConstIterator(); PackageIt; ++PackageIt)
		{
			const FString& PackageName = (*PackageIt).ToString();
			FString SrcFilename;
			if (FPackageName::DoesPackageExist(PackageName, nullptr, &SrcFilename))
			{
				FString DestFilename = output_folder + PackageName;
				if (IFileManager::Get().Copy(*DestFilename, *SrcFilename) == COPY_OK)
				{
					UE_LOG(FTrackLog, Display, TEXT("Successfully migrated %s to %s"), *PackageName, *DestFilename);
				}
				else
				{
					UE_LOG(FTrackLog, Warning, TEXT("Failed to migrate %s to %s"), *PackageName, *DestFilename);
				}
			}
		}
	}
#endif
}