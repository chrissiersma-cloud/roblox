-- LassoSpin: makes the lasso loop above the cowboy's head spin.
--
-- This Script has RunContext = Client, so it runs on every player's computer while the statue is in
-- the Workspace. The spinning is only for looks: every player sees it smooth, and the server does no work.
-- Change the speed with the "SpinSpeed" attribute on the WranglerCampStatue model (turns per second x 2 pi,
-- 5 is a bit less than one turn per second). Set it to 0 to stop the lasso.

local RunService = game:GetService("RunService")

local statue = script.Parent
local loop = statue:WaitForChild("LassoLoop")

-- The loop's PrimaryPart (Hub) sits in the middle of the loop with its Y axis pointing out of the loop,
-- so turning around that axis spins the loop in its own tilted plane.
local start = loop:GetPivot()
local angle = 0

RunService.RenderStepped:Connect(function(dt)
	local speed = statue:GetAttribute("SpinSpeed") or 5
	angle = (angle + dt * speed) % (2 * math.pi)
	loop:PivotTo(start * CFrame.Angles(0, angle, 0))
end)
