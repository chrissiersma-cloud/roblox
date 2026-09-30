-- SwapIn: puts a new building exactly where an old one stands, so it replaces it 1:1.
--
-- In the Command Bar:
--   local swap = require(workspace.HubBuildings.SwapIn)
--   swap(workspace.LassoShop, workspace.HubBuildings.LassoShop)
--
-- The new building gets the old one's spot, turn and size: its footprint is scaled to fit the old
-- building's footprint. The old building is not deleted: it goes to ServerStorage as "<name>_Old",
-- so you can bring it back. Faces the new one the wrong way? Give a turn in degrees:
--   swap(workspace.LassoShop, workspace.HubBuildings.LassoShop, 180)
-- Don't want it scaled? Pass false as the last argument:
--   swap(workspace.LassoShop, workspace.HubBuildings.LassoShop, 0, false)

local ServerStorage = game:GetService("ServerStorage")

return function(old: Model, new: Model, turn: number?, fit: boolean?)
	assert(old and old:IsA("Model"), "SwapIn: the first argument must be the old building (a Model)")
	assert(new and new:IsA("Model"), "SwapIn: the second argument must be the new building (a Model)")

	local oldPivot = old:GetPivot()
	local oldBox, oldSize = old:GetBoundingBox()
	-- Measure the old footprint in the old pivot's own directions.
	local rotation = oldPivot.Rotation * CFrame.Angles(0, math.rad(turn or 0), 0)

	new:PivotTo(CFrame.identity)
	local _, newSize = new:GetBoundingBox()

	if fit ~= false then
		local k = math.min(oldSize.X / newSize.X, oldSize.Z / newSize.Z)
		if k > 0 and k < 100 then
			new:ScaleTo(new:GetScale() * k)
		end
	end

	-- Bottom middle of the old building's bounding box.
	local bottom = oldBox * CFrame.new(0, -oldSize.Y / 2, 0)
	new:PivotTo(CFrame.new(bottom.Position) * rotation)
	new.Parent = old.Parent

	old.Name ..= "_Old"
	old.Parent = ServerStorage
	print(("SwapIn: %s is now where %s was (the old one is in ServerStorage)"):format(new.Name, old.Name))
	return new
end
