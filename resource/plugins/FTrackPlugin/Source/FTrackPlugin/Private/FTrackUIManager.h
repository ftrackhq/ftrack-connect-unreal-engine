// Copyright 1998-2019 Epic Games, Inc. All Rights Reserved.

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