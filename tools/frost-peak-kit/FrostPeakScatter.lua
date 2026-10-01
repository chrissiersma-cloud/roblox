-- FrostPeakScatter: fills an area with pines, rocks, drifts and grass from the Frost Peak kit.
--
-- The Frost Peak area is a big circle: the Valley around the outside, the Slopes in between and the
-- Peak in the middle. Put a big Part over the ground where it should be (it may be see-through), then
-- run in the Command Bar:
--
--   local scatter = require(workspace.FrostPeakKit.FrostPeakScatter)
--   scatter.fillRings(workspace.FrostPeakArea)        -- Valley outside, Slopes, Peak in the middle
--   scatter.fill(workspace.SomeArea, "Slopes")         -- or one zone over a whole part
--
-- Every run makes a new Folder in Workspace (for example "FrostPeak_Rings"). Don't like it? Delete the
-- folder and run it again: every run is different, unless you give the same seed number.
-- Set pieces (cliffs, waterfalls, rivers, the frozen lake, bridges, the cave, lanterns, fences) are not
-- scattered: place those by hand, they make the shape of the area.

local FrostPeakScatter = {}

local KIT = script.Parent

-- Per zone: trees and small things per 1000 square studs, the smallest distance between two trees
-- (gap), and which kit models to pick from.
FrostPeakScatter.Zones = {
	Valley = {
		trees = 3, plants = 6, gap = 12,
		treeList = { "SnowPineSmall", "SnowPine", "PineSapling", "SnowyBush" },
		plantList = { "GrassTufts", "SnowPatch", "Pebbles", "Boulder", "SnowDrift", "SnowyBush", "RockPile" },
	},
	Slopes = {
		trees = 5.5, plants = 5, gap = 10,
		treeList = { "SnowPine", "SnowPineLarge", "SnowPineTall", "PineCluster", "SnowPineSmall" },
		plantList = { "SnowDrift", "Boulder", "BoulderLarge", "RockPile", "Pebbles", "GrassTufts" },
	},
	Peak = {
		trees = 1.5, plants = 5, gap = 14,
		treeList = { "SnowPineTall", "SnowPineSmall", "PineSapling" },
		plantList = { "SnowDrift", "SnowDrift", "BoulderLarge", "Boulder", "Pebbles" },
	},
}

-- fillRings: how far out (0 = centre, 1 = edge) each zone reaches.
FrostPeakScatter.Rings = { { "Peak", 0.3 }, { "Slopes", 0.7 }, { "Valley", 1.0 } }

local PLANT_GAP = 3

local function findTemplate(name)
	local found = KIT:FindFirstChild(name, true)
	if found and found:IsA("Model") then
		return found
	end
	warn("FrostPeakScatter: no model called " .. name .. " in the kit")
	return nil
end

local function groundAt(position, ignore)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local result = workspace:Raycast(position + Vector3.new(0, 500, 0), Vector3.new(0, -1500, 0), params)
	if not result or result.Material == Enum.Material.Water then
		return nil
	end
	-- No trees on steep ground (cliff faces) or on water parts.
	if result.Normal.Y < 0.75 then
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

-- pick(rng) returns a point on top of the area (in world space), or nil to skip.
local function placeMany(count, pick, folder, names, gap, scaleRange, rng, placed, ignore)
	local made, tries = 0, 0
	while made < count and tries < count * 25 do
		tries += 1
		local top = pick(rng)
		local ground = top and groundAt(top, ignore)
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

local function fillZone(zoneName, areaSize, pick, folder, rng, placed, ignore)
	local zone = FrostPeakScatter.Zones[zoneName]
	assert(zone, "FrostPeakScatter: unknown zone '" .. tostring(zoneName) .. "' (use Valley, Slopes or Peak)")
	local trees = placeMany(math.floor(areaSize / 1000 * zone.trees + 0.5), pick, folder, zone.treeList, zone.gap,
		{ 0.85, 1.25 }, rng, placed, ignore)
	local plants = placeMany(math.floor(areaSize / 1000 * zone.plants + 0.5), pick, folder, zone.plantList,
		PLANT_GAP, { 0.8, 1.2 }, rng, placed, ignore)
	print(("FrostPeakScatter: %s -> %d trees, %d other things"):format(zoneName, trees, plants))
end

local function newFolder(name)
	local folder = Instance.new("Folder")
	folder.Name = name
	folder.Parent = workspace
	return folder
end

-- Fills the whole part with one zone.
function FrostPeakScatter.fill(area, zoneName, seed)
	local rng = Random.new(seed or math.floor(os.clock() * 1000))
	local folder = newFolder("FrostPeak_" .. tostring(zoneName))
	local size = area.Size
	local pick = function(r)
		return area.CFrame * Vector3.new(r:NextNumber(-size.X / 2, size.X / 2), size.Y / 2,
			r:NextNumber(-size.Z / 2, size.Z / 2))
	end
	fillZone(zoneName, size.X * size.Z, pick, folder, rng, {}, { area, folder, KIT })
	return folder
end

-- Fills a circle (the largest circle inside the part) with rings: Peak in the middle, Slopes, Valley outside.
function FrostPeakScatter.fillRings(area, seed)
	local rng = Random.new(seed or math.floor(os.clock() * 1000))
	local folder = newFolder("FrostPeak_Rings")
	local radius = math.min(area.Size.X, area.Size.Z) / 2
	local placed = {}
	local inner = 0
	for _, ring in FrostPeakScatter.Rings do
		local zoneName, outerFraction = ring[1], ring[2]
		local r0, r1 = inner * radius, outerFraction * radius
		local pick = function(r)
			-- Uniform over the ring's area.
			local d = math.sqrt(r:NextNumber(r0 * r0, r1 * r1))
			local a = r:NextNumber(0, 2 * math.pi)
			return area.CFrame * Vector3.new(math.cos(a) * d, area.Size.Y / 2, math.sin(a) * d)
		end
		fillZone(zoneName, math.pi * (r1 * r1 - r0 * r0), pick, folder, rng, placed, { area, folder, KIT })
		inner = outerFraction
	end
	return folder
end

return FrostPeakScatter
