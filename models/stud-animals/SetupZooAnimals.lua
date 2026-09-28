--[[
	Create a Zoo - animal setup script

	1. Import the .glb files: Avatar tab > Import 3D (or File > Import 3D) and pick the animal files.
	   Click Import; the animals appear in Workspace.
	2. Open View > Command Bar, paste this whole script and press Enter.

	For every imported animal the script:
	  - adds an invisible RootPart (hitbox, PrimaryPart, pivot under the feet),
	  - joins the body parts with Motor6D joints (legs, and head, tail or wings where the animal has them)
	    so they can be animated,
	  - adds an OverheadAttachment for a name tag and the attributes AnimalId, DisplayName and Rarity,
	  - makes glowing parts Neon and adds sparkles, flames and a light (only animals that have them),
	  - gives Rare animals and up soft sparkles in the color of their rarity,
	  - moves the finished model to ReplicatedStorage.ZooAnimals.
	At the end it selects the ZooAnimals folder. Animals that were already set up are skipped, so running it
	twice is safe. To get one .rbxm file with every animal: right-click ZooAnimals and choose "Save to File...".
]]

local DATA = {
	Bear = {
		display = "Bear",
		rarity = "Epic",
		root = {
			center = { 0.0, 1.915, -0.41 },
			size = { 2.04, 3.83, 4.92 },
		},
		overhead = { 0.0, 4.83, -0.41 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.59, -0.41 },
			},
			{
				name = "LegFL",
				pivot = { -0.6, 1.9, -0.85 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.6, 1.9, -0.85 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.62, 1.9, 1.3 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.62, 1.9, 1.3 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.59, -0.41 },
				size = { 1.98, 2.48, 4.92 },
			},
			LegFL = {
				center = { -0.6, 0.875, -0.93 },
				size = { 0.78, 1.75, 0.96 },
			},
			LegFR = {
				center = { 0.6, 0.875, -0.93 },
				size = { 0.78, 1.75, 0.96 },
			},
			LegBL = {
				center = { -0.62, 1.025, 1.32 },
				size = { 0.8, 2.05, 1.16 },
			},
			LegBR = {
				center = { 0.62, 1.025, 1.32 },
				size = { 0.8, 2.05, 1.16 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Boar = {
		display = "Boar",
		rarity = "Rare",
		root = {
			center = { 0.0, 1.1342, -0.2549 },
			size = { 1.42, 2.2684, 3.6302 },
		},
		overhead = { 0.0, 3.2684, -0.2549 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.4592, -0.2549 },
			},
			{
				name = "LegFL",
				pivot = { -0.42, 0.85, -0.62 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.42, 0.85, -0.62 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.42, 0.85, 0.92 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.42, 0.85, 0.92 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.4592, -0.2549 },
				size = { 1.42, 1.6184, 3.6302 },
			},
			LegFL = {
				center = { -0.42, 0.425, -0.64 },
				size = { 0.38, 0.85, 0.44 },
			},
			LegFR = {
				center = { 0.42, 0.425, -0.64 },
				size = { 0.38, 0.85, 0.44 },
			},
			LegBL = {
				center = { -0.42, 0.425, 0.9 },
				size = { 0.38, 0.85, 0.44 },
			},
			LegBR = {
				center = { 0.42, 0.425, 0.9 },
				size = { 0.38, 0.85, 0.44 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Deer = {
		display = "Deer",
		rarity = "Common",
		root = {
			center = { 0.0, 2.7874, -0.4264 },
			size = { 1.8848, 5.5747, 4.5273 },
		},
		overhead = { 0.0, 6.5747, -0.4264 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 3.6974, -0.4264 },
			},
			{
				name = "LegFL",
				pivot = { -0.4, 2.1, -0.95 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.4, 2.1, -0.95 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.42, 2.1, 1.12 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.42, 2.1, 1.12 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 3.6974, -0.4264 },
				size = { 1.8848, 3.7547, 4.5273 },
			},
			LegFL = {
				center = { -0.4, 1.025, -0.965 },
				size = { 0.46, 2.05, 0.53 },
			},
			LegFR = {
				center = { 0.4, 1.025, -0.965 },
				size = { 0.46, 2.05, 0.53 },
			},
			LegBL = {
				center = { -0.42, 1.11, 1.17 },
				size = { 0.54, 2.22, 0.78 },
			},
			LegBR = {
				center = { 0.42, 1.11, 1.17 },
				size = { 0.54, 2.22, 0.78 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Fox = {
		display = "Fox",
		rarity = "Common",
		root = {
			center = { 0.0, 1.62, 0.1399 },
			size = { 1.16, 3.24, 4.5397 },
		},
		overhead = { 0.0, 4.24, 0.1399 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.08, 0.1399 },
			},
			{
				name = "LegFL",
				pivot = { -0.3, 1.1, -0.72 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.3, 1.1, -0.72 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.33, 1.15, 0.9 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.33, 1.15, 0.9 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.08, 0.1399 },
				size = { 1.16, 2.32, 4.5397 },
			},
			LegFL = {
				center = { -0.3, 0.5, -0.74 },
				size = { 0.32, 1.0, 0.4 },
			},
			LegFR = {
				center = { 0.3, 0.5, -0.74 },
				size = { 0.32, 1.0, 0.4 },
			},
			LegBL = {
				center = { -0.33, 0.64, 0.9 },
				size = { 0.38, 1.28, 0.62 },
			},
			LegBR = {
				center = { 0.33, 0.64, 0.9 },
				size = { 0.38, 1.28, 0.62 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	GorillaKing = {
		display = "Gorilla King",
		rarity = "Secret",
		root = {
			center = { 0.0, 2.64, -0.4794 },
			size = { 3.32, 5.28, 4.0012 },
		},
		overhead = { 0.0, 6.28, -0.4794 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 3.0027, -0.4544 },
			},
			{
				name = "LegFL",
				pivot = { -1.1, 3.3, -0.75 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 1.1, 3.3, -0.75 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.72, 1.7, 0.95 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.72, 1.7, 0.95 },
				parent = "Body",
			},
			{
				name = "Crown",
				pivot = { -0.0, 4.88, -1.415 },
				parent = "Body",
			},
			{
				name = "Chains",
				pivot = { -0.0622, 2.91, -1.4299 },
				parent = "Body",
			},
			{
				name = "Grills",
				pivot = { -0.0, 3.42, -2.44 },
				parent = "Body",
			},
			{
				name = "BraceletL",
				pivot = { -1.2, 0.92, -1.06 },
				parent = "LegFL",
			},
			{
				name = "BraceletR",
				pivot = { 1.2, 0.92, -1.06 },
				parent = "LegFR",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 3.0027, -0.4544 },
				size = { 2.1, 3.0945, 3.9513 },
			},
			LegFL = {
				center = { -1.2, 1.675, -1.07 },
				size = { 0.86, 3.35, 1.2 },
			},
			LegFR = {
				center = { 1.2, 1.675, -1.07 },
				size = { 0.86, 3.35, 1.2 },
			},
			LegBL = {
				center = { -0.75, 0.875, 0.8125 },
				size = { 0.8, 1.75, 1.325 },
			},
			LegBR = {
				center = { 0.75, 0.875, 0.8125 },
				size = { 0.8, 1.75, 1.325 },
			},
			Crown = {
				center = { 0.0, 4.88, -1.415 },
				size = { 1.52, 0.8, 1.39 },
			},
			Chains = {
				center = { -0.0622, 2.91, -1.4299 },
				size = { 1.4557, 1.8, 0.2602 },
			},
			Grills = {
				center = { 0.0, 3.42, -2.44 },
				size = { 0.64, 0.18, 0.08 },
			},
			BraceletL = {
				center = { -1.2, 0.92, -1.06 },
				size = { 0.92, 0.24, 0.98 },
			},
			BraceletR = {
				center = { 1.2, 0.92, -1.06 },
				size = { 0.92, 0.24, 0.98 },
			},
		},
		glow = {
			Crown = { 255.0, 210.0, 58.0 },
		},
		shine = {
			Chains = 0.35,
			Grills = 0.4,
			BraceletL = 0.35,
			BraceletR = 0.35,
		},
		effects = {
			{
				name = "CrownSparkles",
				part = "Crown",
				kind = "Sparkles",
				color = { 255.0, 210.0, 58.0 },
				color2 = { 255.0, 255.0, 255.0 },
				rate = 5,
				size = { 0.4, 0.0 },
				lifetime = { 0.6, 1.2 },
				speed = { 0.3, 0.8 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "GoldSparkles",
				part = "Chains",
				kind = "Sparkles",
				color = { 255.0, 210.0, 58.0 },
				color2 = { 255.0, 210.0, 58.0 },
				rate = 4,
				size = { 0.3, 0.0 },
				lifetime = { 0.6, 1.2 },
				speed = { 0.2, 0.5 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "GrillShine",
				part = "Grills",
				kind = "Sparkles",
				color = { 255.0, 255.0, 255.0 },
				color2 = { 191.0, 239.0, 255.0 },
				rate = 2,
				size = { 0.25, 0.0 },
				lifetime = { 0.3, 0.6 },
				speed = { 0.1, 0.3 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "BraceletSparkles",
				part = "BraceletL",
				kind = "Sparkles",
				color = { 255.0, 210.0, 58.0 },
				color2 = { 255.0, 210.0, 58.0 },
				rate = 2,
				size = { 0.25, 0.0 },
				lifetime = { 0.6, 1.2 },
				speed = { 0.1, 0.4 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "BraceletSparkles",
				part = "BraceletR",
				kind = "Sparkles",
				color = { 255.0, 210.0, 58.0 },
				color2 = { 255.0, 210.0, 58.0 },
				rate = 2,
				size = { 0.25, 0.0 },
				lifetime = { 0.6, 1.2 },
				speed = { 0.1, 0.4 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
		},
		light = {
			part = "Crown",
			color = { 255.0, 210.0, 58.0 },
			brightness = 1.2,
			range = 12,
		},
		ref = {
			"LegBL",
			"Grills",
		},
	},
	Owl = {
		display = "Owl",
		rarity = "Rare",
		root = {
			center = { 0.0, 1.61, 0.015 },
			size = { 1.9246, 3.22, 1.7099 },
		},
		overhead = { 0.0, 4.22, 0.015 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.8176, 0.015 },
			},
			{
				name = "WingL",
				pivot = { -0.66, 2.0, 0.0 },
				parent = "Body",
			},
			{
				name = "WingR",
				pivot = { 0.66, 2.0, 0.0 },
				parent = "Body",
			},
			{
				name = "LegL",
				pivot = { -0.3, 0.55, -0.08 },
				parent = "Body",
			},
			{
				name = "LegR",
				pivot = { 0.3, 0.55, -0.08 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.8176, 0.015 },
				size = { 1.46, 2.8048, 1.7099 },
			},
			WingL = {
				center = { -0.76, 1.35, 0.05 },
				size = { 0.4046, 1.3238, 1.0 },
			},
			WingR = {
				center = { 0.76, 1.35, 0.05 },
				size = { 0.4046, 1.3238, 1.0 },
			},
			LegL = {
				center = { -0.3, 0.28, -0.1945 },
				size = { 0.5236, 0.56, 0.4689 },
			},
			LegR = {
				center = { 0.3, 0.28, -0.1945 },
				size = { 0.5236, 0.56, 0.4689 },
			},
		},
		ref = {
			"WingL",
			"WingR",
		},
	},
	Phoenix = {
		display = "Phoenix",
		rarity = "Mythic",
		root = {
			center = { 0.0, 2.4148, 1.082 },
			size = { 6.9832, 4.8297, 4.8442 },
		},
		overhead = { 0.0, 5.8297, 1.082 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.1315, 0.8091 },
			},
			{
				name = "WingL",
				pivot = { -0.62, 2.75, 0.1 },
				parent = "Body",
			},
			{
				name = "WingR",
				pivot = { 0.62, 2.75, 0.1 },
				parent = "Body",
			},
			{
				name = "LegL",
				pivot = { -0.3, 1.28, 0.1 },
				parent = "Body",
			},
			{
				name = "LegR",
				pivot = { 0.3, 1.28, 0.1 },
				parent = "Body",
			},
			{
				name = "WingFlameL",
				pivot = { -2.2368, 4.2589, 0.1115 },
				parent = "WingL",
			},
			{
				name = "WingFlameR",
				pivot = { 2.2368, 4.2589, 0.1115 },
				parent = "WingR",
			},
			{
				name = "Crest",
				pivot = { -0.0, 4.285, -0.065 },
				parent = "Body",
			},
			{
				name = "TailFlames",
				pivot = { -0.0, 0.4351, 3.132 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.1315, 0.8091 },
				size = { 1.7678, 3.577, 4.2983 },
			},
			WingL = {
				center = { -1.7795, 3.5412, 0.11 },
				size = { 2.6761, 2.0675, 0.2406 },
			},
			WingR = {
				center = { 1.7795, 3.5412, 0.11 },
				size = { 2.6761, 2.0675, 0.2406 },
			},
			LegL = {
				center = { -0.3, 0.6522, -0.15 },
				size = { 0.688, 1.3044, 0.94 },
			},
			LegR = {
				center = { 0.3, 0.6522, -0.15 },
				size = { 0.688, 1.3044, 0.94 },
			},
			WingFlameL = {
				center = { -2.2368, 4.2589, 0.1115 },
				size = { 2.5096, 1.1416, 0.1558 },
			},
			WingFlameR = {
				center = { 2.2368, 4.2589, 0.1115 },
				size = { 2.5096, 1.1416, 0.1558 },
			},
			Crest = {
				center = { 0.0, 4.285, -0.065 },
				size = { 0.48, 0.93, 1.13 },
			},
			TailFlames = {
				center = { 0.0, 0.435, 3.132 },
				size = { 1.7942, 0.1943, 0.7442 },
			},
		},
		glow = {
			Crest = { 255.0, 192.0, 46.0 },
			TailFlames = { 255.0, 192.0, 46.0 },
			WingFlameL = { 255.0, 192.0, 46.0 },
			WingFlameR = { 255.0, 192.0, 46.0 },
		},
		effects = {
			{
				name = "TailFire",
				part = "TailFlames",
				kind = "Fire",
				color = { 255.0, 140.0, 26.0 },
				color2 = { 255.0, 59.0, 31.0 },
				rate = 14,
				size = { 1.1, 0.0 },
				lifetime = { 0.4, 0.7 },
				speed = { 1.5, 2.5 },
				spread = 25,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "WingFire",
				part = "WingFlameL",
				kind = "Fire",
				color = { 255.0, 178.0, 26.0 },
				color2 = { 255.0, 59.0, 31.0 },
				rate = 8,
				size = { 0.9, 0.0 },
				lifetime = { 0.3, 0.6 },
				speed = { 1.0, 2.0 },
				spread = 25,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "WingFire",
				part = "WingFlameR",
				kind = "Fire",
				color = { 255.0, 178.0, 26.0 },
				color2 = { 255.0, 59.0, 31.0 },
				rate = 8,
				size = { 0.9, 0.0 },
				lifetime = { 0.3, 0.6 },
				speed = { 1.0, 2.0 },
				spread = 25,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "Embers",
				part = "Body",
				kind = "Sparkles",
				color = { 255.0, 210.0, 63.0 },
				color2 = { 255.0, 59.0, 31.0 },
				rate = 8,
				size = { 0.4, 0.0 },
				lifetime = { 0.6, 1.2 },
				speed = { 0.5, 1.5 },
				spread = 180,
				accel = { 0.0, 3.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "CrestFire",
				part = "Crest",
				kind = "Fire",
				color = { 255.0, 210.0, 63.0 },
				color2 = { 255.0, 59.0, 31.0 },
				rate = 6,
				size = { 0.5, 0.0 },
				lifetime = { 0.25, 0.45 },
				speed = { 0.8, 1.4 },
				spread = 15,
				accel = { 0.0, 2.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
				at = { 0.0, 4.75, -0.065 },
			},
		},
		light = {
			part = "Body",
			color = { 255.0, 140.0, 26.0 },
			brightness = 1.8,
			range = 18,
		},
		ref = {
			"WingFlameL",
			"WingFlameR",
		},
	},
	Rabbit = {
		display = "Rabbit",
		rarity = "Common",
		root = {
			center = { 0.0, 1.6484, -0.035 },
			size = { 1.34, 3.2968, 2.55 },
		},
		overhead = { 0.0, 4.2968, -0.035 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.8984, -0.035 },
			},
			{
				name = "LegFL",
				pivot = { -0.3, 0.85, -0.38 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.3, 0.85, -0.38 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.5, 0.95, 0.5 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.5, 0.95, 0.5 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.8984, -0.035 },
				size = { 1.16, 2.7968, 2.55 },
			},
			LegFL = {
				center = { -0.3, 0.4125, -0.45 },
				size = { 0.34, 0.825, 0.44 },
			},
			LegFR = {
				center = { 0.3, 0.4125, -0.45 },
				size = { 0.34, 0.825, 0.44 },
			},
			LegBL = {
				center = { -0.5, 0.555, 0.2425 },
				size = { 0.34, 1.11, 1.275 },
			},
			LegBR = {
				center = { 0.5, 0.555, 0.2425 },
				size = { 0.34, 1.11, 1.275 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Raccoon = {
		display = "Raccoon",
		rarity = "Common",
		root = {
			center = { 0.0, 1.075, 0.4211 },
			size = { 1.26, 2.15, 3.8622 },
		},
		overhead = { 0.0, 3.15, 0.4211 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.315, 0.4211 },
			},
			{
				name = "LegFL",
				pivot = { -0.36, 0.62, -0.4 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.36, 0.62, -0.4 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.38, 0.62, 0.72 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.38, 0.62, 0.72 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.315, 0.4211 },
				size = { 1.26, 1.67, 3.8622 },
			},
			LegFL = {
				center = { -0.36, 0.325, -0.43 },
				size = { 0.34, 0.65, 0.4 },
			},
			LegFR = {
				center = { 0.36, 0.325, -0.43 },
				size = { 0.34, 0.65, 0.4 },
			},
			LegBL = {
				center = { -0.38, 0.325, 0.69 },
				size = { 0.34, 0.65, 0.4 },
			},
			LegBR = {
				center = { 0.38, 0.325, 0.69 },
				size = { 0.34, 0.65, 0.4 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Thunderhoof = {
		display = "Thunderhoof",
		rarity = "Legendary",
		root = {
			center = { 0.0, 3.98, -0.2564 },
			size = { 2.9296, 7.96, 6.8673 },
		},
		overhead = { 0.0, 8.96, -0.2564 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 4.396, -0.6273 },
			},
			{
				name = "LegFL",
				pivot = { -0.55, 3.0, -1.3 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.55, 3.0, -1.3 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.58, 3.0, 1.5 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.58, 3.0, 1.5 },
				parent = "Body",
			},
			{
				name = "Lightning",
				pivot = { -0.0, 5.3412, 0.445 },
				parent = "Body",
			},
			{
				name = "Mane",
				pivot = { -0.0, 5.2408, -1.78 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 4.396, -0.6273 },
				size = { 2.5086, 3.752, 6.1254 },
			},
			LegFL = {
				center = { -0.55, 1.475, -1.305 },
				size = { 0.62, 2.95, 0.71 },
			},
			LegFR = {
				center = { 0.55, 1.475, -1.305 },
				size = { 0.62, 2.95, 0.71 },
			},
			LegBL = {
				center = { -0.58, 1.575, 1.55 },
				size = { 0.74, 3.15, 1.05 },
			},
			LegBR = {
				center = { 0.58, 1.575, 1.55 },
				size = { 0.74, 3.15, 1.05 },
			},
			Lightning = {
				center = { 0.0, 5.3412, 0.445 },
				size = { 2.9296, 5.2377, 5.4645 },
			},
			Mane = {
				center = { 0.0, 5.2408, -1.7801 },
				size = { 0.4, 2.5184, 2.3399 },
			},
		},
		glow = {
			Lightning = { 255.0, 226.0, 58.0 },
			Mane = { 70.0, 210.0, 255.0 },
		},
		effects = {
			{
				name = "Sparks",
				part = "Lightning",
				kind = "Sparkles",
				color = { 255.0, 226.0, 58.0 },
				color2 = { 255.0, 255.0, 255.0 },
				rate = 8,
				size = { 0.5, 0.0 },
				lifetime = { 0.2, 0.5 },
				speed = { 3.0, 6.0 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "HoofSparks",
				part = "LegFL",
				kind = "Sparkles",
				color = { 255.0, 226.0, 58.0 },
				color2 = { 255.0, 255.0, 255.0 },
				rate = 3,
				size = { 0.3, 0.0 },
				lifetime = { 0.15, 0.35 },
				speed = { 1.5, 3.0 },
				spread = 180,
				accel = { 0.0, -4.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
				at = { -0.55, 0.0, -1.305 },
			},
			{
				name = "HoofSparks",
				part = "LegFR",
				kind = "Sparkles",
				color = { 255.0, 226.0, 58.0 },
				color2 = { 255.0, 255.0, 255.0 },
				rate = 3,
				size = { 0.3, 0.0 },
				lifetime = { 0.15, 0.35 },
				speed = { 1.5, 3.0 },
				spread = 180,
				accel = { 0.0, -4.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
				at = { 0.55, 0.0, -1.305 },
			},
			{
				name = "HoofSparks",
				part = "LegBL",
				kind = "Sparkles",
				color = { 255.0, 226.0, 58.0 },
				color2 = { 255.0, 255.0, 255.0 },
				rate = 3,
				size = { 0.3, 0.0 },
				lifetime = { 0.15, 0.35 },
				speed = { 1.5, 3.0 },
				spread = 180,
				accel = { 0.0, -4.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
				at = { -0.58, 0.0, 1.55 },
			},
			{
				name = "HoofSparks",
				part = "LegBR",
				kind = "Sparkles",
				color = { 255.0, 226.0, 58.0 },
				color2 = { 255.0, 255.0, 255.0 },
				rate = 3,
				size = { 0.3, 0.0 },
				lifetime = { 0.15, 0.35 },
				speed = { 1.5, 3.0 },
				spread = 180,
				accel = { 0.0, -4.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
				at = { 0.58, 0.0, 1.55 },
			},
		},
		light = {
			part = "Lightning",
			color = { 159.0, 230.0, 255.0 },
			brightness = 1.5,
			range = 14,
		},
		ref = {
			"LegBL",
			"Mane",
		},
	},
	Voidwhisker = {
		display = "Voidwhisker",
		rarity = "Mythic",
		root = {
			center = { 0.0, 2.54, 0.2684 },
			size = { 2.7242, 5.08, 4.1792 },
		},
		overhead = { 0.0, 6.08, 0.2684 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.8945, 0.274 },
			},
			{
				name = "LegFL",
				pivot = { -0.4, 1.55, -0.75 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.4, 1.55, -0.75 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.42, 1.55, 1.15 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.42, 1.55, 1.15 },
				parent = "Body",
			},
			{
				name = "Void",
				pivot = { -0.0, 2.845, -1.0756 },
				parent = "Body",
			},
			{
				name = "Gems",
				pivot = { -0.0, 2.8975, -0.7717 },
				parent = "Body",
			},
			{
				name = "TailWisp",
				pivot = { -0.0, 4.72, 1.88 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.8945, 0.274 },
				size = { 1.36, 2.9891, 4.1681 },
			},
			LegFL = {
				center = { -0.4, 0.75, -0.79 },
				size = { 0.44, 1.5, 0.52 },
			},
			LegFR = {
				center = { 0.4, 0.75, -0.79 },
				size = { 0.44, 1.5, 0.52 },
			},
			LegBL = {
				center = { -0.42, 0.85, 1.15 },
				size = { 0.5, 1.7, 0.85 },
			},
			LegBR = {
				center = { 0.42, 0.85, 1.15 },
				size = { 0.5, 1.7, 0.85 },
			},
			Void = {
				center = { 0.0, 2.845, -1.0756 },
				size = { 1.764, 1.27, 1.4912 },
			},
			Gems = {
				center = { 0.0, 2.8975, -0.7718 },
				size = { 2.7242, 1.955, 1.3677 },
			},
			TailWisp = {
				center = { 0.0, 4.72, 1.88 },
				size = { 0.594, 0.72, 0.594 },
			},
		},
		glow = {
			Void = { 177.0, 77.0, 255.0 },
			Gems = { 255.0, 156.0, 242.0 },
			TailWisp = { 177.0, 77.0, 255.0 },
		},
		effects = {
			{
				name = "VoidSparks",
				part = "TailWisp",
				kind = "Sparkles",
				color = { 177.0, 77.0, 255.0 },
				color2 = { 255.0, 156.0, 242.0 },
				rate = 6,
				size = { 0.5, 0.0 },
				lifetime = { 0.6, 1.2 },
				speed = { 0.3, 0.9 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.2,
				lightEmission = 1,
			},
			{
				name = "ShadowWisps",
				part = "Body",
				kind = "Smoke",
				color = { 58.0, 20.0, 102.0 },
				color2 = { 58.0, 20.0, 102.0 },
				rate = 5,
				size = { 1.2, 2.6 },
				lifetime = { 1.0, 1.6 },
				speed = { 0.2, 0.6 },
				spread = 180,
				accel = { 0.0, 0.0, 0.0 },
				transparency = 0.5,
				lightEmission = 0,
			},
		},
		light = {
			part = "Body",
			color = { 177.0, 77.0, 255.0 },
			brightness = 1.2,
			range = 12,
		},
		ref = {
			"Void",
			"TailWisp",
		},
	},
	Wolf = {
		display = "Wolf",
		rarity = "Rare",
		root = {
			center = { 0.0, 2.15, -0.123 },
			size = { 1.26, 4.3001, 4.914 },
		},
		overhead = { 0.0, 5.3001, -0.123 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.7534, -0.123 },
			},
			{
				name = "LegFL",
				pivot = { -0.36, 1.75, -0.95 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.36, 1.75, -0.95 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.4, 1.85, 1.18 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.4, 1.85, 1.18 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.7534, -0.123 },
				size = { 1.22, 3.0933, 4.914 },
			},
			LegFL = {
				center = { -0.36, 0.9, -0.99 },
				size = { 0.4, 1.8, 0.5 },
			},
			LegFR = {
				center = { 0.36, 0.9, -0.99 },
				size = { 0.4, 1.8, 0.5 },
			},
			LegBL = {
				center = { -0.4, 0.98, 1.2 },
				size = { 0.46, 1.96, 0.76 },
			},
			LegBR = {
				center = { 0.4, 0.98, 1.2 },
				size = { 0.46, 1.96, 0.76 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
}

local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function vec(t)
	return Vector3.new(t[1], t[2], t[3])
end

local function flat(v)
	return Vector3.new(v.X, 0, v.Z)
end

local function rgb(t)
	return Color3.fromRGB(t[1], t[2], t[3])
end

local PARTICLE_TEXTURES = {
	Sparkles = "rbxasset://textures/particles/sparkles_main.dds",
	Fire = "rbxasset://textures/particles/fire_main.dds",
	Smoke = "rbxasset://textures/particles/smoke_main.dds",
}

-- Rare animals and up get soft sparkles around them in the color of their rarity, so players can see it.
local RARITY_AURA = {
	Rare = { 69, 166, 255 },
	Epic = { 184, 97, 255 },
	Legendary = { 255, 204, 51 },
	Mythic = { 255, 74, 74 },
	Secret = { 255, 123, 229 },
}

local function addAura(info, root)
	local color = RARITY_AURA[info.rarity]
	if not color then
		return
	end
	local aura = Instance.new("ParticleEmitter")
	aura.Name = "RarityAura"
	aura.Texture = PARTICLE_TEXTURES.Sparkles
	aura.Color = ColorSequence.new(rgb(color), Color3.new(1, 1, 1))
	aura.Rate = 3
	aura.Lifetime = NumberRange.new(1, 1.8)
	aura.Speed = NumberRange.new(0.3, 0.8)
	aura.SpreadAngle = Vector2.new(180, 180)
	aura.Acceleration = Vector3.new(0, 0.6, 0)
	aura.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
	aura.Transparency = NumberSequence.new(0.3, 1)
	aura.LightEmission = 1
	aura.LightInfluence = 0
	aura.Parent = root
end

-- Glowing parts become Neon in one color, shiny parts reflect; effects are ParticleEmitters (out of a whole part,
-- or out of one spot: an Attachment); light is a PointLight.
local function addEffects(info, parts, root, spots)
	for name, color in pairs(info.glow or {}) do
		local part = parts[name]
		if part then
			part.Material = Enum.Material.Neon
			part.Color = rgb(color)
			part.TextureID = ""
		end
	end
	for name, reflectance in pairs(info.shine or {}) do
		local part = parts[name]
		if part then
			part.Reflectance = reflectance
		end
	end
	for i, e in ipairs(info.effects or {}) do
		local emitter = Instance.new("ParticleEmitter")
		emitter.Name = e.name
		emitter.Texture = PARTICLE_TEXTURES[e.kind]
		emitter.Color = ColorSequence.new(rgb(e.color), rgb(e.color2))
		emitter.Rate = e.rate
		emitter.Lifetime = NumberRange.new(e.lifetime[1], e.lifetime[2])
		emitter.Speed = NumberRange.new(e.speed[1], e.speed[2])
		emitter.SpreadAngle = Vector2.new(e.spread, e.spread)
		emitter.Acceleration = vec(e.accel)
		emitter.Size = NumberSequence.new({
			NumberSequenceKeypoint.new(0, e.size[1]),
			NumberSequenceKeypoint.new(1, e.size[2]),
		})
		emitter.Transparency = NumberSequence.new(e.transparency, 1)
		emitter.LightEmission = e.lightEmission
		emitter.LightInfluence = 0
		emitter.RotSpeed = NumberRange.new(-90, 90)
		emitter.Parent = spots[i] or parts[e.part] or root
	end
	if info.light then
		local light = Instance.new("PointLight")
		light.Name = "Glow"
		light.Color = rgb(info.light.color)
		light.Brightness = info.light.brightness
		light.Range = info.light.range
		light.Parent = parts[info.light.part] or root
	end
end

local function findMeshParts(model)
	local parts = {}
	for _, d in ipairs(model:GetDescendants()) do
		if d:IsA("MeshPart") and parts[d.Name] == nil then
			parts[d.Name] = d
		end
	end
	return parts
end

-- Finds the imported copies of each animal: a Model named after the animal that holds a MeshPart "Body".
local function findImported()
	local found = {}
	for _, d in ipairs(workspace:GetDescendants()) do
		if d:IsA("Model") and DATA[d.Name] and not d:FindFirstChild("RootPart") then
			local parts = findMeshParts(d)
			if parts.Body then
				local top = d
				while top.Parent and top.Parent:IsA("Model") and top.Parent.Name == d.Name do
					top = top.Parent
				end
				found[top] = d.Name
			end
		end
	end
	return found
end

local function setup(model, id)
	local info = DATA[id]
	local parts = findMeshParts(model)
	for name in pairs(info.parts) do
		if not parts[name] then
			local names = {}
			for n in pairs(parts) do
				table.insert(names, n)
			end
			warn(("%s: no MeshPart called %q (found: %s)"):format(id, name, table.concat(names, ", ")))
			return false
		end
	end

	-- Work out where Studio put the model: scale k, turn (yaw) and position, from two far-apart parts.
	local refA, refB = info.ref[1], info.ref[2]
	local dA, dB = vec(info.parts[refA].center), vec(info.parts[refB].center)
	local aA, aB = parts[refA].Position, parts[refB].Position
	local designFlat, actualFlat = flat(dB - dA), flat(aB - aA)
	local k = (aB - aA).Magnitude / (dB - dA).Magnitude
	local yaw = math.atan2(actualFlat.X, actualFlat.Z) - math.atan2(designFlat.X, designFlat.Z)
	local basis = CFrame.Angles(0, yaw, 0)
	local function toWorld(p)
		return aA + basis:VectorToWorldSpace((vec(p) - dA) * k)
	end

	local worst = 0
	for name, part in pairs(parts) do
		if info.parts[name] then
			worst = math.max(worst, (toWorld(info.parts[name].center) - part.Position).Magnitude)
		end
	end
	if worst > 0.1 * k * vec(info.root.size).Magnitude then
		warn(("%s: the parts are not where they were designed (off by %.2f studs); joints may be wrong"):format(id, worst))
	end

	local root = Instance.new("Part")
	root.Name = "RootPart"
	root.Size = vec(info.root.size) * k
	root.CFrame = CFrame.new(toWorld(info.root.center)) * basis
	root.Transparency = 1
	root.Anchored = true
	root.CanCollide = false
	root.CanTouch = true
	root.CanQuery = true
	root.CastShadow = false
	root.PivotOffset = CFrame.new(0, -root.Size.Y / 2, 0)
	root.Parent = model
	model.PrimaryPart = root

	for _, bone in ipairs(info.bones) do
		local part = parts[bone.name]
		part.Anchored = false
		part.CanCollide = false
		part.CanTouch = false
		part.CanQuery = false
		part.Massless = true
		part:SetAttribute("Bone", bone.name)
		local part0 = bone.parent and parts[bone.parent] or root
		local joint = CFrame.new(toWorld(bone.pivot)) * basis
		local motor = Instance.new("Motor6D")
		motor.Name = bone.parent and bone.name or "Root"
		motor.Part0 = part0
		motor.Part1 = part
		motor.C0 = part0.CFrame:ToObjectSpace(joint)
		motor.C1 = part.CFrame:ToObjectSpace(joint)
		motor.Parent = part
	end

	local overhead = Instance.new("Attachment")
	overhead.Name = "OverheadAttachment"
	overhead.Parent = root
	overhead.WorldPosition = toWorld(info.overhead)

	model.Name = id
	model:SetAttribute("AnimalId", id)
	model:SetAttribute("DisplayName", info.display)
	model:SetAttribute("Rarity", info.rarity)
	CollectionService:AddTag(model, "ZooAnimal")

	-- Spots for effects that come out of one point (like sparks from a hoof). They are made before the scaling
	-- below, so they move along with their parts.
	local spots = {}
	for i, e in ipairs(info.effects or {}) do
		if e.at then
			local spot = Instance.new("Attachment")
			spot.Name = e.name .. "Spot"
			spot.Parent = parts[e.part] or root
			spot.WorldPosition = toWorld(e.at)
			spots[i] = spot
		end
	end

	-- Back to the designed size if Studio scaled the import (for example meters to studs).
	if math.abs(k - 1) > 0.01 then
		model:ScaleTo(model:GetScale() / k)
	end
	addEffects(info, parts, root, spots)
	addAura(info, root)

	local folder = ReplicatedStorage:FindFirstChild("ZooAnimals")
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = "ZooAnimals"
		folder.Parent = ReplicatedStorage
	end
	local old = folder:FindFirstChild(id)
	if old then
		old:Destroy()
	end
	model.Parent = folder
	return true
end

local done, failed = 0, 0
for model, id in pairs(findImported()) do
	local ok, result = pcall(setup, model, id)
	if ok and result then
		done += 1
		print(("Set up %s"):format(id))
	else
		failed += 1
		warn(("Could not set up %s: %s"):format(id, tostring(result)))
	end
end
print(("Create a Zoo: %d animals set up, %d failed. Find them in ReplicatedStorage.ZooAnimals."):format(done, failed))
if done > 0 then
	-- Select the whole folder: "Save to File..." then makes one .rbxm with every animal in it.
	game:GetService("Selection"):Set({ ReplicatedStorage.ZooAnimals })
	print('To save all animals as one .rbxm: right-click ZooAnimals (selected) and choose "Save to File..."')
end
