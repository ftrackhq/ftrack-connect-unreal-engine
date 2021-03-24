// Copyright 2019 ftrack. All Rights Reserved.

#include "FTrackStyle.h"

#include "Framework/Application/SlateApplication.h"
#include "Styling/SlateStyle.h"
#include "Styling/SlateStyleRegistry.h"
#include "Interfaces/IPluginManager.h"

TUniquePtr< FSlateStyleSet > FFTrackStyle::FTrackStyleInstance = nullptr;

void FFTrackStyle::Initialize()
{
	if (!FTrackStyleInstance.IsValid())
	{
		FTrackStyleInstance = Create();
		FSlateStyleRegistry::RegisterSlateStyle(*FTrackStyleInstance);
	}
}

void FFTrackStyle::Shutdown()
{
	if (FTrackStyleInstance.IsValid())
	{
		FSlateStyleRegistry::UnRegisterSlateStyle(*FTrackStyleInstance);
		FTrackStyleInstance.Reset();
	}
}

FName FFTrackStyle::GetStyleSetName()
{
	static FName StyleSetName(TEXT("FTrackStyle"));
	return StyleSetName;
}

FName FFTrackStyle::GetContextName()
{
	static FName ContextName(TEXT("FTrack"));
	return ContextName;
}

#define IMAGE_BRUSH( RelativePath, ... ) FSlateImageBrush( Style->RootToContentDir( RelativePath, TEXT(".png") ), __VA_ARGS__ )

const FVector2D Icon20x20(20.0f, 20.0f);
const FVector2D Icon40x40(40.0f, 40.0f);

TUniquePtr< FSlateStyleSet > FFTrackStyle::Create()
{
	TUniquePtr< FSlateStyleSet > Style = MakeUnique<FSlateStyleSet>(GetStyleSetName());
	FString PluginDir = IPluginManager::Get().FindPlugin("FTrackPlugin")->GetBaseDir();
	FString RPath(PluginDir / TEXT("Resources"));
	UE_LOG(FTrackLog, Display, TEXT("Using ftrack resource path: %s."), *RPath);
	Style->SetContentRoot(RPath);

	return Style;
}

void FFTrackStyle::SetIcon(const FString& StyleName, const FString& ResourcePath)
{
	FSlateStyleSet* Style = FTrackStyleInstance.Get();

	FString Name(GetContextName().ToString());
	Name = Name + "." + StyleName;
	Style->Set(*Name, new IMAGE_BRUSH(ResourcePath, Icon40x40));

	Name += ".Small";
	Style->Set(*Name, new IMAGE_BRUSH(ResourcePath, Icon20x20));

	FSlateApplication::Get().GetRenderer()->ReloadTextureResources();
}

#undef IMAGE_BRUSH

const ISlateStyle& FFTrackStyle::Get()
{
	check(FTrackStyleInstance);
	return *FTrackStyleInstance;
}
