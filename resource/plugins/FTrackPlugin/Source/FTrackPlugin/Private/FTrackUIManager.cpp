// Copyright 2019 ftrack. All Rights Reserved.

#include "FTrackUIManager.h"
#include "FTrackStyle.h"
#include "FTrackConnect.h"
#include "ContentBrowserModule.h"
#include "LevelEditor.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"
#include "Framework/MultiBox/MultiBoxExtender.h"
#include "Misc/Paths.h"
#include "IPythonScriptPlugin.h"


#define LOCTEXT_NAMESPACE "ftrack"
#define LEVELEDITOR_MODULE_NAME TEXT("LevelEditor")


class FTrackUIManagerImpl
{
public:
	void Initialize();
	void Shutdown();
protected:
	void FillToolbar(FToolBarBuilder& ToolbarBuilder);
	TSharedRef<SWidget> GenerateFtrackToolbarMenu();
};

TUniquePtr<FTrackUIManagerImpl> FTrackUIManager::Instance;

void FTrackUIManagerImpl::Initialize()
{
	FFTrackStyle::Initialize();
	FFTrackStyle::SetIcon("Logo", "ftrack_logo");
	FFTrackStyle::SetIcon("ContextLogo", "ftrack_logo");

	// This code will execute after your module is loaded into memory (but after global variables are initialized, of course.)
	FLevelEditorModule& LevelEditorModule = FModuleManager::LoadModuleChecked<FLevelEditorModule>(LEVELEDITOR_MODULE_NAME);

	TSharedPtr<FExtender> ToolbarExtender = MakeShareable(new FExtender);
	ToolbarExtender->AddToolBarExtension("Settings", EExtensionHook::After, nullptr, FToolBarExtensionDelegate::CreateRaw(this, &FTrackUIManagerImpl::FillToolbar));

	LevelEditorModule.GetToolBarExtensibilityManager()->AddExtender(ToolbarExtender);
}

void FTrackUIManagerImpl::Shutdown()
{
	FFTrackStyle::Shutdown();
}

TSharedRef<SWidget> FTrackUIManagerImpl::GenerateFtrackToolbarMenu()
{
	const bool bShouldCloseWindowAfterMenuSelection = true;
	FMenuBuilder MenuBuilder(bShouldCloseWindowAfterMenuSelection, nullptr);

	if (UFTrackConnect* ftrackConnect = UFTrackConnect::GetInstance())
	{
		TArray<FFTrackMenuItem> menuItems =  ftrackConnect->GetFtrackMenuItems();
		for (const FFTrackMenuItem& menuItem : menuItems)
		{
			if (menuItem.Type == TEXT("separator"))
			{
				MenuBuilder.AddMenuSeparator();
			}
			else 
			{
				FString CommandName = menuItem.Name;
				MenuBuilder.AddMenuEntry(
					FText::FromString(menuItem.DisplayName),
					FText::FromString(menuItem.Description),
					FSlateIcon(),
					FExecuteAction::CreateLambda([CommandName]()
					{
						if (UFTrackConnect* ftrackConnect = UFTrackConnect::GetInstance())
						{
							ftrackConnect->ExecuteCommand(CommandName);
						}
					})
				);
			}
		}
	}


	return MenuBuilder.MakeWidget();
}
void FTrackUIManagerImpl::FillToolbar(FToolBarBuilder& ToolbarBuilder)
{
	ToolbarBuilder.BeginSection(TEXT("ftrack"));
	{
		// Add a drop-down menu (with a label and an icon for the drop-down button) to list the ftrack actions available
		ToolbarBuilder.AddComboButton(
			FUIAction(),
			FOnGetContent::CreateRaw(this, &FTrackUIManagerImpl::GenerateFtrackToolbarMenu),
			LOCTEXT("FtrackCombo_Label", "ftrack"),
			LOCTEXT("FTrackCombo_Tooltip", "Available ftrack commands"),
			FSlateIcon(FFTrackStyle::GetStyleSetName(), "FTrack.Logo")
		);
	}
	ToolbarBuilder.EndSection();
}

void FTrackUIManager::Initialize()
{
	if (!Instance.IsValid())
	{
		Instance = MakeUnique<FTrackUIManagerImpl>();
		Instance->Initialize();
	}
}

void FTrackUIManager::Shutdown()
{
	if (Instance.IsValid())
	{
		Instance->Shutdown();
		Instance.Reset();
	}
}
