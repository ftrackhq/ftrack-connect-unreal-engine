// Copyright 2019 ftrack. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class FTrackUIManagerImpl;

class FTrackUIManager
{
public:
	static void Initialize();
	static void Shutdown();

private:
	static TUniquePtr<FTrackUIManagerImpl> Instance;
};