-- LassoBurst: when the player clicks with the lasso, every player's LassoFX plays the burst (the loop spins
-- fast and throws out sparks). RunContext = Server, so the click reaches everyone.
-- Your own lasso-throwing script can stay: this only adds the effect.

local tool = script.Parent
local last = 0

tool.Activated:Connect(function()
	local now = os.clock()
	if now - last < 0.35 then
		return
	end
	last = now
	tool:SetAttribute("Bursts", (tool:GetAttribute("Bursts") or 0) + 1)
end)
