-- StatueStyle: gives the cowboy statue a different finish.
--
-- In Studio, open View > Command Bar and run one of these:
--
--   require(workspace.WranglerCampStatue.StatueStyle).apply("Painted")  -- bright colours (default)
--   require(workspace.WranglerCampStatue.StatueStyle).apply("Bronze")   -- old bronze statue
--   require(workspace.WranglerCampStatue.StatueStyle).apply("Gold")     -- shiny golden statue
--
-- Every part of the cowboy has a "Paint" attribute (shirt, vest, jeans, ...) that says which colour it gets.

local StatueStyle = {}

local rgb = Color3.fromRGB

StatueStyle.Styles = {
	Painted = {
		shirt = rgb(216, 67, 59), vest = rgb(107, 63, 34), jeans = rgb(47, 95, 208), skin = rgb(241, 201, 160),
		hat = rgb(163, 106, 54), hatDark = rgb(58, 36, 22), boots = rgb(90, 52, 24), bandana = rgb(47, 95, 208),
		belt = rgb(58, 36, 22), gold = rgb(242, 193, 78), eye = rgb(26, 16, 8), hair = rgb(90, 52, 24),
		reflectance = 0,
	},
	Bronze = {
		shirt = rgb(176, 122, 68), vest = rgb(138, 90, 46), jeans = rgb(154, 106, 58), skin = rgb(196, 138, 80),
		hat = rgb(138, 90, 46), hatDark = rgb(90, 52, 24), boots = rgb(107, 68, 36), bandana = rgb(160, 106, 54),
		belt = rgb(90, 52, 24), gold = rgb(212, 154, 90), eye = rgb(58, 36, 22), hair = rgb(107, 68, 36),
		reflectance = 0.1,
	},
	Gold = {
		shirt = rgb(232, 184, 74), vest = rgb(201, 150, 46), jeans = rgb(217, 168, 60), skin = rgb(242, 204, 106),
		hat = rgb(201, 150, 46), hatDark = rgb(138, 100, 24), boots = rgb(168, 118, 28), bandana = rgb(242, 213, 122),
		belt = rgb(138, 100, 24), gold = rgb(255, 240, 168), eye = rgb(107, 74, 16), hair = rgb(168, 118, 28),
		reflectance = 0.2,
	},
}

function StatueStyle.apply(styleName)
	local style = StatueStyle.Styles[styleName]
	assert(style, "StatueStyle: unknown style '" .. tostring(styleName) .. "' (use Painted, Bronze or Gold)")
	local statue = script.Parent
	local count = 0
	for _, part in statue:GetDescendants() do
		if part:IsA("BasePart") then
			local key = part:GetAttribute("Paint")
			if key and style[key] then
				part.Color = style[key]
				part.Reflectance = style.reflectance
				count += 1
			end
		end
	end
	statue:SetAttribute("Style", styleName)
	print(("StatueStyle: %s applied to %d parts"):format(styleName, count))
end

return StatueStyle
