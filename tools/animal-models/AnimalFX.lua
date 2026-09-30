-- AnimalFX: idle effects for a Dark Woods animal. RunContext = Client, so it runs on every player's
-- computer and costs the server nothing. It only moves joints (Motor6D.Transform) and tweens glow,
-- so the animal's RootPart (hitbox) stays exactly where your game puts it.
--
-- Settings are attributes on the animal model:
--   FlapSpeed, FlapAngle  wings (joints called Wing...) flap up and down
--   Hover, HoverSpeed     the body bobs up and down (studs)
--   OrbitSpeed            the joint called Orbit spins around (radians per second)
--   TailSway              the Tail joint swings from side to side (degrees)
-- Neon parts and lights with a "Pulse" attribute (seconds) glow brighter and dimmer.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local model = script.Parent

local joints = {}
for _, joint in model:GetDescendants() do
	if joint:IsA("Motor6D") then
		joints[joint.Name] = joint
	end
end

for _, item in model:GetDescendants() do
	local seconds = item:GetAttribute("Pulse")
	if seconds then
		local info = TweenInfo.new(seconds, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true)
		if item:IsA("BasePart") then
			TweenService:Create(item, info, { Transparency = math.max(item.Transparency, 0.45) }):Play()
		elseif item:IsA("Light") then
			TweenService:Create(item, info, { Brightness = item.Brightness * 0.3 }):Play()
		end
	end
end

local function attribute(name, default)
	local value = model:GetAttribute(name)
	if value == nil then
		return default
	end
	return value
end

local start = os.clock()
local phase = math.random() * 10 -- so a group of the same animal doesn't move in sync

RunService.PreSimulation:Connect(function()
	if not model.Parent then
		return
	end
	local t = os.clock() - start + phase

	local flapSpeed = attribute("FlapSpeed", 0)
	if flapSpeed > 0 then
		local angle = math.sin(t * flapSpeed) * math.rad(attribute("FlapAngle", 30))
		for name, joint in joints do
			if name:sub(1, 4) == "Wing" then
				local side = if name:sub(-1) == "L" then -1 else 1
				joint.Transform = CFrame.Angles(0, 0, angle * side)
			end
		end
	end

	local hover = attribute("Hover", 0)
	if hover > 0 and joints.Root then
		joints.Root.Transform = CFrame.new(0, math.sin(t * attribute("HoverSpeed", 2)) * hover, 0)
	end

	local orbit = attribute("OrbitSpeed", 0)
	if orbit ~= 0 and joints.Orbit then
		joints.Orbit.Transform = CFrame.Angles(0, t * orbit, 0)
	end

	local sway = attribute("TailSway", 0)
	if sway > 0 and joints.Tail then
		joints.Tail.Transform = CFrame.Angles(0, math.sin(t * 1.6) * math.rad(sway), 0)
	end
end)
