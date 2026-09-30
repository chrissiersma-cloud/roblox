-- DarkWoodsScatter: fills an area with trees, crystals and plants from the Dark Woods kit.
--
-- Put a big Part over the ground where the forest should be (it may be see-through), then run
-- in the Command Bar:
--
--   local scatter = require(workspace.DarkWoodsKit.DarkWoodsScatter)
--   scatter.fillGradient(workspace.DarkWoodsArea)   -- Gloom at the part's front, Heart at the back
--   scatter.fill(workspace.DeepArea, "Deep")         -- or one zone at a time
--
-- Every run makes a new Folder in Workspace (for example "DarkWoods_Deep"). Don't like it? Delete the
-- folder and run it again: every run is different, unless you give the same seed number.
-- Hanging models (HangingVines, HangingLantern) and single set pieces (MoonwoodTree, RuneCircle,
-- CrystalLarge, RootArch, lanterns) are not scattered: place those by hand.

local DarkWoodsScatter = {}

local KIT = script.Parent

-- Per zone: trees and plants per 1000 square studs, the smallest distance between two trees
-- (gap), and which kit models to pick from.
DarkWoodsScatter.Zones = {
	Gloom = {
		trees = 3, plants = 7, gap = 11,
		treeList = { "ShadowOakSmall", "ShadowOak", "GnarledTree", "IndigoOak" },
		plantList = { "ThornBrambleSmall", "PurpleLeaves", "ShadowBoulder", "ShadowFern", "CrystalShards",
			"ShadowBush" },
	},
	Deep = {
		trees = 6.5, plants = 9, gap = 9,
		treeList = { "ShadowOak", "ShadowOakLarge", "IndigoOak", "ShadowPine", "GnarledTree" },
		plantList = { "ThornBramble", "ShadowFern", "GlowShrooms", "CrystalSmall", "CrystalCluster", "PurpleLeaves",
			"GlowMoss", "IndigoBush", "NightBlooms", "TwistedStump", "FallenShadowLog" },
	},
	Heart = {
		trees = 5, plants = 9, gap = 10,
		treeList = { "PlumOak", "GnarledCrystalTree", "ShadowOakLarge" },
		plantList = { "CrystalCluster", "CrystalClusterPink", "NightBlooms", "GlowMoss", "ShadowFern",
			"CrystalShards" },
	},
}

DarkWoodsScatter.GradientOrder = { "Gloom", "Deep", "Heart" }

local PLANT_GAP = 2.5

local function findTemplate(name)
	local found = KIT:FindFirstChild(name, true)
	if found and found:IsA("Model") then
		return found
	end
	warn("DarkWoodsScatter: no model called " .. name .. " in the kit")
	return nil
end

local function groundAt(position, ignore)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local result = workspace:Raycast(position + Vector3.new(0, 300, 0), Vector3.new(0, -900, 0), params)
	if not result or result.Material == Enum.Material.Water then
		return nil
	end
	return result.Position
end

local function isFree(point, gap, placed)
	for _, other in placed do
		local dx = point.X - other.position.X
		local dz = point.Z - other.position.Z
		local need = math.min(gap, other.gap)
		if dx * dx + dz * dz < need * need then
			return false
		end
	end
	return true
end

-- region = { cframe = CFrame, size = Vector3 }
local function placeMany(region, folder, names, per1000, gap, scaleRange, rng, placed, ignore)
	local size = region.size
	local count = math.floor(size.X * size.Z / 1000 * per1000 + 0.5)
	local made, tries = 0, 0
	while made < count and tries < count * 25 do
		tries += 1
		local top = region.cframe * Vector3.new(
			rng:NextNumber(-size.X / 2, size.X / 2),
			size.Y / 2,
			rng:NextNumber(-size.Z / 2, size.Z / 2)
		)
		local ground = groundAt(top, ignore)
		if ground and isFree(ground, gap, placed) then
			local template = findTemplate(names[rng:NextInteger(1, #names)])
			if template then
				local model = template:Clone()
				model:ScaleTo(rng:NextNumber(scaleRange[1], scaleRange[2]))
				model:PivotTo(CFrame.new(ground) * CFrame.Angles(0, rng:NextNumber(0, 2 * math.pi), 0))
				model.Parent = folder
				table.insert(placed, { position = ground, gap = gap })
				made += 1
			end
		end
	end
	return made
end

local function fillRegion(region, zoneName, folder, rng, placed, ignore)
	local zone = DarkWoodsScatter.Zones[zoneName]
	assert(zone, "DarkWoodsScatter: unknown zone '" .. tostring(zoneName) .. "' (use Gloom, Deep or Heart)")
	local trees = placeMany(region, folder, zone.treeList, zone.trees, zone.gap, { 0.85, 1.2 }, rng, placed, ignore)
	local plants = placeMany(region, folder, zone.plantList, zone.plants, PLANT_GAP, { 0.8, 1.2 }, rng, placed, ignore)
	print(("DarkWoodsScatter: %s -> %d trees, %d plants"):format(zoneName, trees, plants))
end

local function newFolder(name)
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = workspace
	return folder
end

-- Fills the whole part with one zone.
function DarkWoodsScatter.fill(area, zoneName, seed)
	local rng = Random.new(seed or math.floor(os.clock() * 1000))
	local folder = newFolder("DarkWoods_" .. tostring(zoneName))
	fillRegion({ cframe = area.CFrame, size = area.Size }, zoneName, folder, rng, {}, { area, folder, KIT })
	return folder
end

-- Splits the part into 3 strips along its length (local Z): Gloom at the front face (the side
-- the part looks at), then Deep and Heart at the back.
function DarkWoodsScatter.fillGradient(area, seed)
	local rng = Random.new(seed or math.floor(os.clock() * 1000))
	local folder = newFolder("DarkWoods_Gradient")
	local placed = {}
	local order = DarkWoodsScatter.GradientOrder
	local strip = area.Size.Z / #order
	for i, zoneName in order do
		local z = -area.Size.Z / 2 + strip * (i - 0.5)
		local region = {
			cframe = area.CFrame * CFrame.new(0, 0, z),
			size = Vector3.new(area.Size.X, area.Size.Y, strip),
		}
		fillRegion(region, zoneName, folder, rng, placed, { area, folder, KIT })
	end
	return folder
end

return DarkWoodsScatter
