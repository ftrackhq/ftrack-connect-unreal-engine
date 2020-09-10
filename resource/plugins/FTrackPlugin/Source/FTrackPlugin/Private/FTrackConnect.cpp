// Copyright 2019 ftrack. All Rights Reserved.
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
#include "HAL/FileManager.h"

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
#if WITH_EDITOR
	// This function is identical to UAssetToolsImpl::RecursiveGetDependencies in UE4's AssetTools module.
	// It is being added here for use by the MigratePackages re-implementation provided below.
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
#endif
}

TArray<FString> UFTrackConnect::MigratePackages(const FString &MapName, const FString &OutputFolder) const
{
#if WITH_EDITOR
	// This is a re-implementation of Unreal's AssetTools.MigratePackages() function to remove all blocking UI.
	// The functionality, however, is the same (utilizing public modules that are exposed to the UE4 C++ API).
	FName UMapPackageName(*MapName);
	TArray<FString> SuccessfullyCopiedPackages;

	TSet<FName> AllPackagesToMove;
	AllPackagesToMove.Add(UMapPackageName);

	// Fetch the dependencies of the umap level file:
	RecursiveGetDependencies(UMapPackageName, AllPackagesToMove);

	// Copy all specified assets and their dependencies to the destination folder
	for (auto PackageIt = AllPackagesToMove.CreateConstIterator(); PackageIt; ++PackageIt)
	{
		const FString& PackageName = (*PackageIt).ToString();
		FString SrcFilename;
		
		// Check that the package exists and retrive the filename on disk
		if (FPackageName::DoesPackageExist(PackageName, nullptr, &SrcFilename))
		{
			FString DestFilename = OutputFolder;
			FPaths::NormalizeFilename(DestFilename);

			if (!DestFilename.EndsWith(TEXT("/")))
			{
				DestFilename += TEXT("/");
			}

			// Construct the destination filepath using the package's existing location
			// in the project's Content directory
			FString SubFolder;
			if (SrcFilename.Split(TEXT("/Content/"), nullptr, &SubFolder))
			{	
				DestFilename += *SubFolder;
				if (IFileManager::Get().FileSize(*DestFilename) > 0)
				{
					UE_LOG(FTrackLog, Display, TEXT("The package %s already exists at the destination %s."), *PackageName, *DestFilename);
				}
				else if (IFileManager::Get().Copy(*DestFilename, *SrcFilename) != COPY_OK)
				{
					UE_LOG(FTrackLog, Warning, TEXT("Failed to copy package %s to %s."), *PackageName, *DestFilename);
				}
				else 
				{
					SuccessfullyCopiedPackages.Add(PackageName);
				}
			}
			else 
			{
				UE_LOG(FTrackLog, Warning, TEXT("Failed to construct destination path for %s."), *SrcFilename);
			}
		}
		else 
		{
			UE_LOG(FTrackLog, Warning, TEXT("The package %s does not exist."), *PackageName);
		}
	}
	return SuccessfullyCopiedPackages;
#endif
}