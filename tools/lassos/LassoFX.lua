-- LassoFX: twirls the lasso's loop and plays the burst when its owner clicks.
--
-- RunContext = Client: this runs on every player's computer, so everyone sees the loop spin, and the server
-- does no work for it. Attributes on the Tool:
--   SpinSpeed       turns per second while idle (0 stops the loop)
--   BurstSpinSpeed  turns per second right after a click
--   Flicker         the light flickers like fire
--   Bursts          counted up by LassoBurst on every click; every player plays the burst when it changes

local RunService = game:GetService("RunService")

local tool = script.Parent
local handle = tool:WaitForChild("Handle")
local hub = tool:WaitForChild("LoopHub")
local motor = handle:WaitForChild("LoopSpin") :: Motor6D

local light = hub:FindFirstChild("Light", true)
local baseBrightness = if light and light:IsA("PointLight") then light.Brightness else 0

local burstEmitters: { ParticleEmitter } = {}
local burst = hub:FindFirstChild("Burst")
if burst then
	for _, child in burst:GetChildren() do
		if child:IsA("ParticleEmitter") then
			table.insert(burstEmitters, child)
		end
	end
end

local TAU = 2 * math.pi
local angle = 0
local boost = 0 -- 1 right after a click, fades back to 0
local flash = 0
local seen = tool:GetAttribute("Bursts") or 0

local function playBurst()
	boost = 1
	flash = 1
	for _, emitter in burstEmitters do
		emitter:Emit(if emitter.Name == "BurstFlash" then 1 else 26)
	end
end

tool:GetAttributeChangedSignal("Bursts"):Connect(function()
	local count = tool:GetAttribute("Bursts") or 0
	if count ~= seen then
		seen = count
		playBurst()
	end
end)

RunService.PreSimulation:Connect(function(dt)
	local idle = tool:GetAttribute("SpinSpeed") or 1.1
	local fast = tool:GetAttribute("BurstSpinSpeed") or 4.5
	boost = math.max(0, boost - dt * 0.8)
	local speed = idle + (fast - idle) * boost * boost * (3 - 2 * boost)
	angle = (angle + dt * speed * TAU) % TAU
	motor.Transform = CFrame.Angles(0, angle, 0)

	if light and light:IsA("PointLight") then
		flash = math.max(0, flash - dt * 3)
		local flicker = 1
		if tool:GetAttribute("Flicker") then
			local t = os.clock()
			flicker = 0.8 + 0.15 * math.sin(t * 17) + 0.1 * math.sin(t * 29 + 1.3)
		end
		light.Brightness = baseBrightness * flicker + flash * 4
	end
end)
