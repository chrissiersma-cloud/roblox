--[[
	Create a Zoo - animal setup script

	1. Import the .glb files: Avatar tab > Import 3D (or File > Import 3D) and pick the animal files.
	   Click Import; the animals appear in Workspace.
	2. Open View > Command Bar, paste this whole script and press Enter.

	For every imported animal the script:
	  - adds an invisible RootPart (hitbox, PrimaryPart, pivot under the feet),
	  - joins the body parts with Motor6D joints (Head, legs, tail, wings) so they can be animated,
	  - adds an OverheadAttachment for a name tag and the attributes AnimalId, DisplayName and Rarity,
	  - moves the finished model to ReplicatedStorage.ZooAnimals.
	Animals that were already set up are skipped, so running it twice is safe.
]]

local DATA = {
	Deer = {
		display = "Deer",
		rarity = "Common",
		root = {
			center = { 0.0, 4.6104, -0.7228 },
			size = { 2.48, 9.2209, 8.3509 },
		},
		overhead = { 0.0, 10.2209, -0.7228 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 4.773, -0.233 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 6.2, -3.05 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.6, 4.3, -1.8 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.6, 4.3, -1.8 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.68, 4.4, 2.0 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.68, 4.4, 2.0 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 4.85, 2.95 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 4.773, -0.233 },
				size = { 2.462, 3.7459, 6.6281 },
			},
			Head = {
				center = { 0.0013, 7.6204, -3.8143 },
				size = { 2.4521, 3.2009, 2.1678 },
			},
			LegFR = {
				center = { 0.6, 2.3685, -1.8 },
				size = { 0.9, 4.7369, 0.8738 },
			},
			LegFL = {
				center = { -0.6, 2.3685, -1.8 },
				size = { 0.9, 4.7369, 0.8738 },
			},
			LegBR = {
				center = { 0.68, 2.4726, 2.145 },
				size = { 1.12, 4.9453, 1.3805 },
			},
			LegBL = {
				center = { -0.68, 2.4726, 2.145 },
				size = { 1.12, 4.9453, 1.3805 },
			},
			Tail = {
				center = { 0.0, 4.6996, 3.199 },
				size = { 0.4333, 0.6011, 0.5074 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Wolf = {
		display = "Wolf",
		rarity = "Rare",
		root = {
			center = { 0.0, 2.8261, -0.2304 },
			size = { 2.22, 5.6522, 8.3362 },
		},
		overhead = { 0.0, 6.6522, -0.2304 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 3.4399, -0.3214 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 4.3, -2.6 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.5, 3.1, -1.5 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.5, 3.1, -1.5 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.56, 3.3, 1.6 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.56, 3.3, 1.6 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 3.55, 2.4 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 3.4399, -0.3214 },
				size = { 2.009, 2.9197, 5.8124 },
			},
			Head = {
				center = { 0.0, 4.8111, -3.3677 },
				size = { 1.8301, 1.6822, 2.0617 },
			},
			LegFR = {
				center = { 0.5, 1.7407, -1.5642 },
				size = { 0.8, 3.4975, 0.9073 },
			},
			LegFL = {
				center = { -0.5, 1.7407, -1.5642 },
				size = { 0.8, 3.4975, 0.9073 },
			},
			LegBR = {
				center = { 0.56, 1.9143, 1.7613 },
				size = { 1.1, 3.8426, 1.3939 },
			},
			LegBL = {
				center = { -0.56, 1.9143, 1.7613 },
				size = { 1.1, 3.8426, 1.3939 },
			},
			Tail = {
				center = { 0.0, 2.6088, 3.0668 },
				size = { 0.7799, 2.389, 1.7419 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Bear = {
		display = "Bear",
		rarity = "Epic",
		root = {
			center = { 0.0, 2.875, -0.5072 },
			size = { 4.0, 5.75, 8.6214 },
		},
		overhead = { 0.0, 6.75, -0.5072 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 3.925, 0.253 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 4.4, -2.7 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.95, 3.8, -1.6 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.95, 3.8, -1.6 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 1.0, 3.9, 2.3 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -1.0, 3.9, 2.3 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 4.0, 3.4 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 3.925, 0.253 },
				size = { 3.2499, 3.65, 6.5529 },
			},
			Head = {
				center = { 0.0, 4.59, -3.6154 },
				size = { 1.8715, 1.82, 2.405 },
			},
			LegFR = {
				center = { 0.95, 2.3005, -2.0223 },
				size = { 1.7, 4.6531, 2.4988 },
			},
			LegFL = {
				center = { -0.95, 2.3005, -2.0223 },
				size = { 1.7, 4.6531, 2.4988 },
			},
			LegBR = {
				center = { 1.0, 2.4226, 2.0497 },
				size = { 2.0, 4.8972, 2.4429 },
			},
			LegBL = {
				center = { -1.0, 2.4226, 2.0497 },
				size = { 2.0, 4.8972, 2.4429 },
			},
			Tail = {
				center = { 0.0, 4.0, 3.55 },
				size = { 0.507, 0.52, 0.507 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Fox = {
		display = "Fox",
		rarity = "Common",
		root = {
			center = { 0.0, 2.1762, 0.2897 },
			size = { 1.4, 4.3523, 6.6576 },
		},
		overhead = { 0.0, 5.3523, 0.2897 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.535, -0.1895 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 3.1, -1.75 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.33, 2.2, -1.0 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.33, 2.2, -1.0 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.37, 2.4, 1.1 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.37, 2.4, 1.1 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 2.45, 1.6 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.535, -0.1895 },
				size = { 1.1818, 1.87, 3.8396 },
			},
			Head = {
				center = { -0.0, 3.6462, -2.2627 },
				size = { 1.2323, 1.4123, 1.5529 },
			},
			LegFR = {
				center = { 0.33, 1.2193, -1.0118 },
				size = { 0.5, 2.4486, 0.5109 },
			},
			LegFL = {
				center = { -0.33, 1.2193, -1.0118 },
				size = { 0.5, 2.4486, 0.5109 },
			},
			LegBR = {
				center = { 0.37, 1.3582, 1.2179 },
				size = { 0.66, 2.7265, 0.8787 },
			},
			LegBL = {
				center = { -0.37, 1.3582, 1.2179 },
				size = { 0.66, 2.7265, 0.8787 },
			},
			Tail = {
				center = { 0.0, 1.9393, 2.5109 },
				size = { 0.8189, 1.4186, 2.2152 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Raccoon = {
		display = "Raccoon",
		rarity = "Common",
		root = {
			center = { 0.0, 1.4918, 0.6689 },
			size = { 1.6, 2.9836, 5.536 },
		},
		overhead = { 0.0, 3.9836, 0.6689 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.0, 0.1754 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 2.2, -1.0 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.45, 1.7, -0.65 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.45, 1.7, -0.65 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.5, 1.9, 1.1 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.5, 1.9, 1.1 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 2.1, 1.55 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.0, 0.1754 },
				size = { 1.5363, 1.64, 3.028 },
			},
			Head = {
				center = { 0.0, 2.4568, -1.453 },
				size = { 1.0439, 1.0536, 1.2923 },
			},
			LegFR = {
				center = { 0.45, 0.9634, -0.707 },
				size = { 0.48, 1.9399, 0.5808 },
			},
			LegFL = {
				center = { -0.45, 0.9634, -0.707 },
				size = { 0.48, 1.9399, 0.5808 },
			},
			LegBR = {
				center = { 0.5, 1.0923, 1.1218 },
				size = { 0.6, 2.1976, 0.6259 },
			},
			LegBL = {
				center = { -0.5, 1.0923, 1.1218 },
				size = { 0.6, 2.1976, 0.6259 },
			},
			Tail = {
				center = { 0.0, 1.7391, 2.3857 },
				size = { 0.6435, 1.2582, 2.1026 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Boar = {
		display = "Boar",
		rarity = "Rare",
		root = {
			center = { 0.0, 2.1536, -0.4369 },
			size = { 2.3241, 4.3072, 6.6063 },
		},
		overhead = { 0.0, 5.3072, -0.4369 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.7936, 0.2523 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 2.8, -1.7 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.55, 2.2, -1.0 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.55, 2.2, -1.0 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.55, 2.4, 1.6 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.55, 2.4, 1.6 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 2.9, 2.4 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.7936, 0.2523 },
				size = { 2.3241, 3.0272, 4.4681 },
			},
			Head = {
				center = { 0.0, 2.8795, -2.6057 },
				size = { 1.4378, 1.9495, 2.2688 },
			},
			LegFR = {
				center = { 0.55, 1.2657, -1.0 },
				size = { 0.68, 2.5315, 0.663 },
			},
			LegFL = {
				center = { -0.55, 1.2657, -1.0 },
				size = { 0.68, 2.5315, 0.663 },
			},
			LegBR = {
				center = { 0.55, 1.4031, 1.6 },
				size = { 0.84, 2.8062, 0.8124 },
			},
			LegBL = {
				center = { -0.55, 1.4031, 1.6 },
				size = { 0.84, 2.8062, 0.8124 },
			},
			Tail = {
				center = { 0.0, 2.4802, 2.6249 },
				size = { 0.2, 0.9724, 0.4826 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Elk = {
		display = "Elk",
		rarity = "Epic",
		root = {
			center = { 0.0006, 6.1618, -0.9425 },
			size = { 4.6655, 12.3235, 9.6111 },
		},
		overhead = { 0.0, 13.3235, -0.9425 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 5.6489, -0.341 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 7.2, -3.6 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.72, 5.0, -2.0 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.72, 5.0, -2.0 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.8, 5.2, 2.3 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.8, 5.2, 2.3 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 5.6, 3.5 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 5.6489, -0.341 },
				size = { 2.7181, 4.3379, 7.8424 },
			},
			Head = {
				center = { 0.0006, 9.5068, -3.6357 },
				size = { 4.6655, 5.6335, 4.2246 },
			},
			LegFR = {
				center = { 0.72, 2.7676, -2.0 },
				size = { 1.1, 5.5352, 1.0703 },
			},
			LegFL = {
				center = { -0.72, 2.7676, -2.0 },
				size = { 1.1, 5.5352, 1.0703 },
			},
			LegBR = {
				center = { 0.8, 2.9156, 2.4318 },
				size = { 1.3, 5.8313, 1.5263 },
			},
			LegBL = {
				center = { -0.8, 2.9156, 2.4318 },
				size = { 1.3, 5.8313, 1.5263 },
			},
			Tail = {
				center = { 0.0, 5.2998, 3.6491 },
				size = { 0.4333, 0.6307, 0.4281 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Owl = {
		display = "Owl",
		rarity = "Rare",
		root = {
			center = { -0.025, 1.9267, 0.1387 },
			size = { 3.85, 3.8533, 2.0251 },
		},
		overhead = { 0.0, 5.2, 0.1387 },
		bones = {
			{
				name = "Body",
				pivot = { -0.025, 1.475, 0.1894 },
			},
			{
				name = "WingR",
				parent = "Body",
				pivot = { 0.7, 2.5, 0.0 },
			},
			{
				name = "WingL",
				parent = "Body",
				pivot = { -0.7, 2.5, 0.0 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 2.7, 0.0 },
			},
		},
		parts = {
			Body = {
				center = { -0.025, 1.475, 0.1894 },
				size = { 3.85, 2.95, 1.9236 },
			},
			WingR = {
				center = { 0.78, 1.85, 0.1173 },
				size = { 0.3939, 1.7, 1.3447 },
			},
			WingL = {
				center = { -0.7723, 1.85, 0.1205 },
				size = { 0.4193, 1.7, 1.3403 },
			},
			Head = {
				center = { 0.0, 3.1167, -0.1468 },
				size = { 1.4181, 1.4733, 1.4541 },
			},
		},
		ref = {
			"WingR",
			"WingL",
		},
	},
	Rabbit = {
		display = "Rabbit",
		rarity = "Common",
		root = {
			center = { 0.0, 2.2242, 0.1116 },
			size = { 2.1066, 4.4484, 3.2017 },
		},
		overhead = { 0.0, 5.4484, 0.1116 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.19, 0.1526 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 2.1, -0.5 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.3, 1.0, -0.8 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.3, 1.0, -0.8 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 0.9, 1.3 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.19, 0.1526 },
				size = { 2.1066, 2.38, 2.4628 },
			},
			Head = {
				center = { 0.0, 3.1742, -0.8143 },
				size = { 1.1818, 2.5484, 1.3498 },
			},
			LegFR = {
				center = { 0.3, 0.5572, -0.8009 },
				size = { 0.44, 1.1145, 0.7907 },
			},
			LegFL = {
				center = { -0.3, 0.5572, -0.8009 },
				size = { 0.44, 1.1145, 0.7907 },
			},
			Tail = {
				center = { 0.0, 0.95, 1.42 },
				size = { 0.585, 0.6, 0.585 },
			},
		},
		ref = {
			"LegFR",
			"Tail",
		},
	},
	MountainLion = {
		display = "Mountain Lion",
		rarity = "Epic",
		root = {
			center = { 0.0, 2.375, 0.4891 },
			size = { 2.3299, 4.75, 8.7364 },
		},
		overhead = { 0.0, 5.75, 0.4891 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.9982, -0.2015 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 3.7, -2.6 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.52, 2.7, -1.6 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.52, 2.7, -1.6 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.58, 3.0, 1.8 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.58, 3.0, 1.8 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 3.2, 2.6 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.9982, -0.2015 },
				size = { 1.8711, 2.3764, 5.8741 },
			},
			Head = {
				center = { 0.0, 4.09, -3.1191 },
				size = { 1.2606, 1.32, 1.52 },
			},
			LegFR = {
				center = { 0.52, 1.5495, -1.6628 },
				size = { 0.84, 3.119, 0.9435 },
			},
			LegFL = {
				center = { -0.52, 1.5495, -1.6628 },
				size = { 0.84, 3.119, 0.9435 },
			},
			LegBR = {
				center = { 0.58, 1.7838, 1.9762 },
				size = { 1.1699, 3.5856, 1.5463 },
			},
			LegBL = {
				center = { -0.58, 1.7838, 1.9762 },
				size = { 1.1699, 3.5856, 1.5463 },
			},
			Tail = {
				center = { 0.0, 1.92, 3.6207 },
				size = { 0.429, 2.9998, 2.4731 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	Lynx = {
		display = "Lynx",
		rarity = "Rare",
		root = {
			center = { 0.0, 2.5258, -0.0052 },
			size = { 2.08, 5.0516, 5.488 },
		},
		overhead = { 0.0, 6.0516, -0.0052 },
		bones = {
			{
				name = "Body",
				pivot = { -0.0046, 2.955, 0.1079 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 3.4, -1.6 },
			},
			{
				name = "LegFR",
				parent = "Body",
				pivot = { 0.48, 2.7, -1.1 },
			},
			{
				name = "LegFL",
				parent = "Body",
				pivot = { -0.48, 2.7, -1.1 },
			},
			{
				name = "LegBR",
				parent = "Body",
				pivot = { 0.52, 3.05, 1.4 },
			},
			{
				name = "LegBL",
				parent = "Body",
				pivot = { -0.52, 3.05, 1.4 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 3.4, 2.05 },
			},
		},
		parts = {
			Body = {
				center = { -0.0046, 2.955, 0.1079 },
				size = { 1.7021, 2.07, 4.0968 },
			},
			Head = {
				center = { 0.0, 4.0316, -2.1186 },
				size = { 1.2724, 2.04, 1.2613 },
			},
			LegFR = {
				center = { 0.48, 1.53, -1.1822 },
				size = { 0.76, 3.0801, 0.9046 },
			},
			LegFL = {
				center = { -0.48, 1.53, -1.1822 },
				size = { 0.76, 3.0801, 0.9046 },
			},
			LegBR = {
				center = { 0.52, 1.7736, 1.5442 },
				size = { 1.04, 3.5662, 1.3017 },
			},
			LegBL = {
				center = { -0.52, 1.7736, 1.5442 },
				size = { 1.04, 3.5662, 1.3017 },
			},
			Tail = {
				center = { 0.0, 3.2638, 2.2973 },
				size = { 0.39, 0.6668, 0.883 },
			},
		},
		ref = {
			"Head",
			"Tail",
		},
	},
	WildTurkey = {
		display = "Wild Turkey",
		rarity = "Common",
		root = {
			center = { 0.0, 2.4, -0.0921 },
			size = { 4.177, 4.8, 3.3043 },
		},
		overhead = { 0.0, 5.6, -0.0921 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.385, -0.0198 },
			},
			{
				name = "WingR",
				parent = "Body",
				pivot = { 0.85, 2.7, -0.3 },
			},
			{
				name = "LegR",
				parent = "Body",
				pivot = { 0.3, 1.6, 0.2 },
			},
			{
				name = "WingL",
				parent = "Body",
				pivot = { -0.85, 2.7, -0.3 },
			},
			{
				name = "LegL",
				parent = "Body",
				pivot = { -0.3, 1.6, 0.2 },
			},
			{
				name = "Head",
				parent = "Body",
				pivot = { 0.0, 3.0, -0.9 },
			},
			{
				name = "Tail",
				parent = "Body",
				pivot = { 0.0, 2.7, 1.2 },
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.385, -0.0198 },
				size = { 1.8711, 2.07, 3.0001 },
			},
			WingR = {
				center = { 0.9, 2.3492, 0.3398 },
				size = { 0.3545, 1.2947, 2.1436 },
			},
			LegR = {
				center = { 0.3188, 0.846, 0.0008 },
				size = { 0.5302, 1.6698, 0.7058 },
			},
			WingL = {
				center = { -0.9, 2.3492, 0.3398 },
				size = { 0.3545, 1.2947, 2.1436 },
			},
			LegL = {
				center = { -0.3212, 0.846, 0.0008 },
				size = { 0.5302, 1.6698, 0.7058 },
			},
			Head = {
				center = { 0.0, 3.4907, -1.174 },
				size = { 0.585, 1.5786, 1.1404 },
			},
			Tail = {
				center = { 0.0, 3.698, 1.5125 },
				size = { 4.177, 2.2041, 0.0951 },
			},
		},
		ref = {
			"Head",
			"Tail",
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

	-- Back to the designed size if Studio scaled the import (for example meters to studs).
	if math.abs(k - 1) > 0.01 then
		model:ScaleTo(model:GetScale() / k)
	end

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
