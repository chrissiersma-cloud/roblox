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
	  - moves the finished model to ReplicatedStorage.ZooAnimals and selects it.
	Animals that were already set up are skipped, so running it twice is safe.
	To get an .rbxm file: right-click the selected animal in the Explorer and choose "Save to File...".
]]

local DATA = {
	Bear = {
		display = "Bear",
		rarity = "Epic",
		root = {
			center = { 0.0, 2.124, -0.654 },
			size = { 2.76, 4.248, 6.684 },
		},
		overhead = { 0.0, 5.248, -0.654 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.904, -0.654 },
			},
			{
				name = "LegFL",
				pivot = { -0.744, 2.04, -1.56 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.744, 2.04, -1.56 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.792, 2.04, 1.68 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.792, 2.04, 1.68 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.904, -0.654 },
				size = { 2.52, 2.688, 6.684 },
			},
			LegFL = {
				center = { -0.744, 1.23, -1.638 },
				size = { 1.032, 2.46, 1.236 },
			},
			LegFR = {
				center = { 0.744, 1.23, -1.638 },
				size = { 1.032, 2.46, 1.236 },
			},
			LegBL = {
				center = { -0.792, 1.29, 1.704 },
				size = { 1.176, 2.58, 1.44 },
			},
			LegBR = {
				center = { 0.792, 1.29, 1.704 },
				size = { 1.176, 2.58, 1.44 },
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
			center = { 0.0, 1.245, -0.4725 },
			size = { 1.62, 2.49, 4.605 },
		},
		overhead = { 0.0, 3.49, -0.4725 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.645, -0.4725 },
			},
			{
				name = "LegFL",
				pivot = { -0.42, 0.85, -0.95 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.42, 0.85, -0.95 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.45, 0.85, 1.0 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.45, 0.85, 1.0 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.645, -0.4725 },
				size = { 1.62, 1.69, 4.605 },
			},
			LegFL = {
				center = { -0.42, 0.575, -0.955 },
				size = { 0.56, 1.15, 0.61 },
			},
			LegFR = {
				center = { 0.42, 0.575, -0.955 },
				size = { 0.56, 1.15, 0.61 },
			},
			LegBL = {
				center = { -0.45, 0.625, 1.02 },
				size = { 0.66, 1.25, 0.84 },
			},
			LegBR = {
				center = { 0.45, 0.625, 1.02 },
				size = { 0.66, 1.25, 0.84 },
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
			center = { 0.0, 2.99, -0.175 },
			size = { 2.247, 5.98, 5.19 },
		},
		overhead = { 0.0, 6.98, -0.175 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 3.955, -0.175 },
			},
			{
				name = "LegFL",
				pivot = { -0.45, 2.3, -1.05 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.45, 2.3, -1.05 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.48, 2.3, 1.3 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.48, 2.3, 1.3 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 3.955, -0.175 },
				size = { 2.247, 4.05, 5.19 },
			},
			LegFL = {
				center = { -0.45, 1.275, -1.065 },
				size = { 0.62, 2.55, 0.69 },
			},
			LegFR = {
				center = { 0.45, 1.275, -1.065 },
				size = { 0.62, 2.55, 0.69 },
			},
			LegBL = {
				center = { -0.48, 1.35, 1.32 },
				size = { 0.74, 2.7, 0.92 },
			},
			LegBR = {
				center = { 0.48, 1.35, 1.32 },
				size = { 0.74, 2.7, 0.92 },
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
			center = { 0.0, 1.5949, 0.2 },
			size = { 1.14, 3.1898, 5.04 },
		},
		overhead = { 0.0, 4.1898, 0.2 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.0599, 0.2 },
			},
			{
				name = "LegFL",
				pivot = { -0.27, 1.3, -0.8 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.27, 1.3, -0.8 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.3, 1.3, 0.85 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.3, 1.3, 0.85 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.0599, 0.2 },
				size = { 1.06, 2.2598, 5.04 },
			},
			LegFL = {
				center = { -0.27, 0.775, -0.85 },
				size = { 0.44, 1.55, 0.58 },
			},
			LegFR = {
				center = { 0.27, 0.775, -0.85 },
				size = { 0.44, 1.55, 0.58 },
			},
			LegBL = {
				center = { -0.3, 0.8, 0.88 },
				size = { 0.54, 1.6, 0.72 },
			},
			LegBR = {
				center = { 0.3, 0.8, 0.88 },
				size = { 0.54, 1.6, 0.72 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Owl = {
		display = "Owl",
		rarity = "Rare",
		root = {
			center = { 0.0, 1.4557, -0.046 },
			size = { 1.64, 2.9113, 1.372 },
		},
		overhead = { 0.0, 3.9113, -0.046 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.6657, -0.046 },
			},
			{
				name = "WingL",
				pivot = { -0.6, 1.85, 0.06 },
				parent = "Body",
			},
			{
				name = "WingR",
				pivot = { 0.6, 1.85, 0.06 },
				parent = "Body",
			},
			{
				name = "LegL",
				pivot = { -0.28, 0.55, 0.0 },
				parent = "Body",
			},
			{
				name = "LegR",
				pivot = { 0.28, 0.55, 0.0 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.6657, -0.046 },
				size = { 1.34, 2.4913, 1.372 },
			},
			WingL = {
				center = { -0.66, 1.215, 0.12 },
				size = { 0.32, 1.33, 0.88 },
			},
			WingR = {
				center = { 0.66, 1.215, 0.12 },
				size = { 0.32, 1.33, 0.88 },
			},
			LegL = {
				center = { -0.28, 0.31, -0.12 },
				size = { 0.38, 0.62, 0.56 },
			},
			LegR = {
				center = { 0.28, 0.31, -0.12 },
				size = { 0.38, 0.62, 0.56 },
			},
		},
		ref = {
			"WingL",
			"WingR",
		},
	},
	Rabbit = {
		display = "Rabbit",
		rarity = "Common",
		root = {
			center = { 0.0, 1.6305, 0.09 },
			size = { 1.5, 3.2611, 2.5 },
		},
		overhead = { 0.0, 4.2611, 0.09 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.8005, 0.09 },
			},
			{
				name = "LegFL",
				pivot = { -0.3, 0.55, -0.42 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.3, 0.55, -0.42 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.46, 0.9, 0.55 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.46, 0.9, 0.55 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.8005, 0.09 },
				size = { 1.44, 2.9211, 2.5 },
			},
			LegFL = {
				center = { -0.3, 0.4, -0.495 },
				size = { 0.42, 0.8, 0.59 },
			},
			LegFR = {
				center = { 0.3, 0.4, -0.495 },
				size = { 0.42, 0.8, 0.59 },
			},
			LegBL = {
				center = { -0.46, 0.6, 0.415 },
				size = { 0.58, 1.2, 1.29 },
			},
			LegBR = {
				center = { 0.46, 0.6, 0.415 },
				size = { 0.58, 1.2, 1.29 },
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
			center = { 0.0, 1.1373, 0.36 },
			size = { 1.3, 2.2746, 3.96 },
		},
		overhead = { 0.0, 3.2746, 0.36 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 1.4323, 0.36 },
			},
			{
				name = "LegFL",
				pivot = { -0.3, 0.75, -0.5 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.3, 0.75, -0.5 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.36, 0.85, 0.55 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.36, 0.85, 0.55 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 1.4323, 0.36 },
				size = { 1.3, 1.6845, 3.96 },
			},
			LegFL = {
				center = { -0.3, 0.475, -0.555 },
				size = { 0.42, 0.95, 0.53 },
			},
			LegFR = {
				center = { 0.3, 0.475, -0.555 },
				size = { 0.42, 0.95, 0.53 },
			},
			LegBL = {
				center = { -0.36, 0.55, 0.555 },
				size = { 0.52, 1.1, 0.71 },
			},
			LegBR = {
				center = { 0.36, 0.55, 0.555 },
				size = { 0.52, 1.1, 0.71 },
			},
		},
		ref = {
			"LegFL",
			"LegBR",
		},
	},
	Wolf = {
		display = "Wolf",
		rarity = "Rare",
		root = {
			center = { 0.0, 2.075, -0.28 },
			size = { 1.6, 4.15, 5.64 },
		},
		overhead = { 0.0, 5.15, -0.28 },
		bones = {
			{
				name = "Body",
				pivot = { 0.0, 2.565, -0.28 },
			},
			{
				name = "LegFL",
				pivot = { -0.42, 1.75, -1.05 },
				parent = "Body",
			},
			{
				name = "LegFR",
				pivot = { 0.42, 1.75, -1.05 },
				parent = "Body",
			},
			{
				name = "LegBL",
				pivot = { -0.45, 1.75, 1.25 },
				parent = "Body",
			},
			{
				name = "LegBR",
				pivot = { 0.45, 1.75, 1.25 },
				parent = "Body",
			},
		},
		parts = {
			Body = {
				center = { 0.0, 2.565, -0.28 },
				size = { 1.56, 3.17, 5.64 },
			},
			LegFL = {
				center = { -0.42, 1.025, -1.11 },
				size = { 0.58, 2.05, 0.74 },
			},
			LegFR = {
				center = { 0.42, 1.025, -1.11 },
				size = { 0.58, 2.05, 0.74 },
			},
			LegBL = {
				center = { -0.45, 1.075, 1.28 },
				size = { 0.7, 2.15, 0.92 },
			},
			LegBR = {
				center = { 0.45, 1.075, 1.28 },
				size = { 0.7, 2.15, 0.92 },
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
local finished = {}
for model, id in pairs(findImported()) do
	local ok, result = pcall(setup, model, id)
	if ok and result then
		done += 1
		table.insert(finished, model)
		print(("Set up %s"):format(id))
	else
		failed += 1
		warn(("Could not set up %s: %s"):format(id, tostring(result)))
	end
end
print(("Create a Zoo: %d animals set up, %d failed. Find them in ReplicatedStorage.ZooAnimals."):format(done, failed))
if done > 0 then
	game:GetService("Selection"):Set(finished)
	print('To save them as .rbxm: right-click the selected animal in the Explorer and choose "Save to File..."')
end
