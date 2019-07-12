// Copyright 2019 ftrack. All Rights Reserved.

namespace UnrealBuildTool.Rules
{
	public class FTrackPlugin : ModuleRules
	{
		public FTrackPlugin(ReadOnlyTargetRules Target) : base(Target)
		{
            PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

            PrivateDependencyModuleNames.AddRange(
                new string[]
                {
                    "AssetRegistry",
                    "AssetTools",
                    "ContentBrowser",
                    "Core",
                    "CoreUObject",
                    "EditorStyle",
                    "Engine",
                    "LevelEditor",
                    "LevelSequence",
                    "MovieScene",
                    "MovieSceneTracks",
                    "PythonScriptPlugin",
                    "Settings",
                    "Slate",
                    "SlateCore",
                    "UnrealEd",
                }
            );
        }
	}
}
