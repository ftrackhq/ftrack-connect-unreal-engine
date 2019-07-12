#include "FTrackConnect.h"

#include "AssetRegistryModule.h"
#include "IAssetRegistry.h"

#include "GameFramework/Actor.h"
#include "IPythonScriptPlugin.h"
#include "Misc/CoreDelegates.h"
#include "Misc/Paths.h"
#include "Templates/Casts.h"
#include "UObject/UObjectHash.h"
#include "Factories/Factory.h"
#include "LevelEditor/Public/LevelEditor.h"
#include "AssetTools/Public/AssetToolsModule.h"
#include "Tracks/MovieSceneCinematicShotTrack.h"

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

ULevelSequence* UFTrackConnect::CreateMasterSequence(const FString& sequenceName, const FString& shotInfo) const
{
	ULevelSequence* masterSequence = NULL;
	

	FString MasterSequencePackagePath = "Tmp";
	IAssetTools& AssetTools = FModuleManager::GetModuleChecked<FAssetToolsModule>("AssetTools").Get();
	UObject* NewAsset = nullptr;
	for (TObjectIterator<UClass> It ; It ; ++It)
	{
		UClass* CurrentClass = *It;
		if (CurrentClass->IsChildOf(UFactory::StaticClass()) && !(CurrentClass->HasAnyClassFlags(CLASS_Abstract)))
		{
			UFactory* Factory = Cast<UFactory>(CurrentClass->GetDefaultObject());
			if (Factory->CanCreateNew() && Factory->ImportPriority >= 0 && Factory->SupportedClass == ULevelSequence::StaticClass())
			{
				masterSequence = Cast<ULevelSequence>(AssetTools.CreateAsset(sequenceName, "/Game/Cinematic", ULevelSequence::StaticClass(), Factory));
				break;
			}
		}
	}

	UMovieSceneCinematicShotTrack* ShotTrack = masterSequence->GetMovieScene()->AddMasterTrack<UMovieSceneCinematicShotTrack>();

	FFrameRate TickResolution = masterSequence->GetMovieScene()->GetTickResolution();

	// Create shots with a camera cut and a camera for each
	/*FFrameNumber SequenceStartTime = (ProjectSettings->DefaultStartTime * TickResolution).FloorToFrame();
	FFrameNumber ShotStartTime = SequenceStartTime;
	FFrameNumber ShotEndTime   = ShotStartTime;
	int32        ShotDuration  = (ProjectSettings->DefaultDuration * TickResolution).RoundToFrame().Value;
	FString FirstShotName; 
	for (uint32 ShotIndex = 0; ShotIndex < NumShots; ++ShotIndex)
	{
		ShotEndTime += ShotDuration;

		FString ShotName = MovieSceneToolHelpers::GenerateNewShotName(ShotTrack->GetAllSections(), ShotStartTime);
		FString ShotPackagePath = MovieSceneToolHelpers::GenerateNewShotPath(MasterSequence->GetMovieScene(), ShotName);

		if (ShotIndex == 0)
		{
			FirstShotName = ShotName;
		}

		AddShot(ShotTrack, ShotName, ShotPackagePath, ShotStartTime, ShotEndTime, AssetToDuplicate, FirstShotName);
		GetSequencer()->ResetToNewRootSequence(*MasterSequence);

		ShotStartTime = ShotEndTime;
	}

	MasterSequence->GetMovieScene()->SetPlaybackRange(SequenceStartTime, (ShotEndTime - SequenceStartTime).Value);*/


	return masterSequence;
}
