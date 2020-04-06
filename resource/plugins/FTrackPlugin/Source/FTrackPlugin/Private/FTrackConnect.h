// Copyright 2019 ftrack. All Rights Reserved.
#pragma once

#include "CoreMinimal.h"
#include "AssetData.h"

#include "FTrackConnect.generated.h"

DECLARE_LOG_CATEGORY_EXTERN(FTrackLog, Log, All);

USTRUCT(Blueprintable)
struct FFTrackMenuItem
{
	GENERATED_BODY()

public:
	// Command name for internal use
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Python)
	FString Name;

	// Text to display in the menu
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Python)
	FString DisplayName;

	// Description text for the tooltip
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Python)
	FString Description;

	// Menu item type to help interpret the command
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = Python)
	FString Type;
};

/**
 * Wrapper for the Python ftrack connect
 * The functions are implemented in Python by a class that derives from this one
 */
UCLASS(Blueprintable)
class UFTrackConnect : public UObject
{
	GENERATED_BODY()

	// Gets the dependencies of the specified package recursively
	void RecursiveGetDependencies(const FName& PackageName, TSet<FName>& AllDependencies) const;

public:
	// Get the instance of the Python ftrack connect
	UFUNCTION(BlueprintCallable, Category = Python)
	static UFTrackConnect *GetInstance();

	// Callback for when the Python ftrack connect has finished initialization
	UFUNCTION(BlueprintCallable, Category = Python)
	void OnConnectInitialized() const;

	// Get the available FTrack commands.
	UFUNCTION(BlueprintImplementableEvent, Category = Python)
	TArray<FFTrackMenuItem> GetFtrackMenuItems() const;

	// Shut down the Python ftrack connect
	UFUNCTION(BlueprintImplementableEvent, Category = Python)
	void Shutdown() const;

	// Execute a command in Python
	UFUNCTION(BlueprintImplementableEvent, Category = Python)
	void ExecuteCommand(const FString &CommandName) const;

	// Add global tag in asset registry, this is used to facilitate query of assets
	UFUNCTION(BlueprintCallable, Category = Python)
	void AddGlobalTagInAssetRegistry(const FString &tag) const;

	// Returns capture arguments specific to ftrack
	UFUNCTION(BlueprintImplementableEvent, Category = Python)
	FString GetCaptureArguments() const;

	// Migrate the Unreal umap file and its dependencies to the output folder.
	// Returns an array of the package names that were successfully copied over.
	UFUNCTION(BlueprintCallable, Category = "Editor Scripting|Asset Tools")
	TArray<FString> MigratePackages(const FString &MapName, const FString &OutputFolder) const;
};
