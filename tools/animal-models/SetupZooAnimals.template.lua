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
	  - moves the finished model to ReplicatedStorage.ZooAnimals and selects it.
	Animals that were already set up are skipped, so running it twice is safe.
	To get an .rbxm file: right-click the selected animal in the Explorer and choose "Save to File...".
]]

local DATA = --[[DATA]]

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

-- Glowing parts become Neon in one color; effects are ParticleEmitters; light is a PointLight.
local function addEffects(info, parts, root)
	for name, color in pairs(info.glow or {}) do
		local part = parts[name]
		if part then
			part.Material = Enum.Material.Neon
			part.Color = rgb(color)
			part.TextureID = ""
		end
	end
	for _, e in ipairs(info.effects or {}) do
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
		emitter.Parent = parts[e.part] or root
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

	-- Back to the designed size if Studio scaled the import (for example meters to studs).
	if math.abs(k - 1) > 0.01 then
		model:ScaleTo(model:GetScale() / k)
	end
	addEffects(info, parts, root)

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
