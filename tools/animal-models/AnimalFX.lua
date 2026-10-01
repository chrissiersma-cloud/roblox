-- AnimalFX: animations and effects for a Dark Woods animal. RunContext = Client, so it runs on every
-- player's device and costs the server nothing. It only moves joints (Motor6D.Transform) and makes
-- particles, so the animal's RootPart (hitbox) stays exactly where your game puts it.
--
-- WALKING starts by itself: the script measures how fast the RootPart moves (PivotTo, tweens, anything)
-- and blends from idle into a walk that fits the animal (trot, hop, slither, waddle, flutter...).
-- The steps keep pace with the ground speed, and every step makes its own effect.
-- IDLE: breathing, looking around, and every few seconds a special action (a croak, a roar, a stomp...).
--
-- Attributes on the animal model you can change:
--   State           "" (automatic), "Idle", "Walk" or "Run" to force an animation
--   WalkSpeed       the speed (studs/s) of a normal walk; faster moves look like running
--   IdleActions     false = no special idle actions
--   FXDistance      beyond this many studs from the camera there are no effects (default 160)
--   FlapSpeed, FlapAngle, Hover, HoverSpeed, OrbitSpeed, TailSway   (see the README)
-- Neon parts and lights with a "Pulse" attribute (seconds) glow brighter and dimmer.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

local model = script.Parent
local root = model.PrimaryPart or model:FindFirstChild("RootPart")
if not root then
	return
end

local TEX = {
	spark = "rbxasset://textures/particles/sparkles_main.dds",
	smoke = "rbxasset://textures/particles/smoke_main.dds",
	fire = "rbxasset://textures/particles/fire_main.dds",
}

local function hex(h: string): Color3
	return Color3.fromHex(h)
end

-- ------------------------------------------------------------ profiles --
-- gait: "quad" (four legs, pattern = phase of each leg), "hop", "slither", "fly", "biped", "bird"
-- stride: studs per step cycle, swing: leg swing (degrees), bounce: body bob (studs)
-- step / aura: particle effects (see makeEmitter), ring: shockwave on each step
-- idle: the special idle action, every = seconds between actions
-- runPattern: leg phases when running (a gallop), maxCycles: at most this many strides per second, so a very
-- fast animal (a mount) still moves its legs like a gallop instead of a blur

local TROT = { LegFR = 0, LegBL = 0, LegFL = 0.5, LegBR = 0.5 }
local WALK4 = { LegFL = 0, LegBR = 0.25, LegFR = 0.5, LegBL = 0.75 }
local GALLOP = { LegBL = 0, LegBR = 0.1, LegFL = 0.42, LegFR = 0.52 }

local P = {
	MossbackToad = {
		gait = "hop", stride = 5, swing = 32, bounce = 1.6, headBob = 6, walkSpeed = 6, breathe = 0.08,
		step = { tex = "smoke", c = { "#7aa843", "#46a846" }, size = { 1.2, 3 }, life = { 0.6, 1 }, speed = { 3, 6 },
			spread = 80, count = 14, drag = 3, light = 0 },
		stepRing = { color = "#8fe05a", radius = 5, time = 0.45 },
		aura = { at = "Body", tex = "spark", c = { "#b8ff6a", "#46a846" }, size = { 0.3, 0 }, life = { 1, 1.6 },
			speed = { 0.5, 1.5 }, rate = 8, accel = Vector3.new(0, 2, 0) },
		idle = "croak", every = { 5, 9 },
	},
	ShroomSnail = {
		gait = "slither", stride = 3, swing = 0, bounce = 0.15, headBob = 10, walkSpeed = 3, breathe = 0.05,
		step = { tex = "spark", c = { "#9ff5ff", "#5ef0ff" }, size = { 0.6, 0 }, life = { 1.5, 2.5 }, speed = { 0.2, 0.8 },
			spread = 60, count = 10 },
		aura = { at = "CapPeak", tex = "spark", c = { "#ffffff", "#9ff5ff" }, size = { 0.35, 0 }, life = { 1.5, 2.5 },
			speed = { 1, 2.5 }, rate = 12, accel = Vector3.new(0, 1.5, 0), spread = 40 },
		idle = "spores", every = { 6, 10 },
	},
	Duskbat = {
		gait = "fly", stride = 8, swing = 0, bounce = 0.3, walkSpeed = 12, breathe = 0, lean = 18, flapBoost = 0.9,
		aura = { at = "Body", tex = "spark", c = { "#b58cff", "#5a3f86" }, size = { 0.6, 0 }, life = { 0.4, 0.8 },
			speed = { 1, 3 }, rate = 25, spread = 180 },
		idle = "screech", every = { 5, 8 },
	},
	NightHedgehog = {
		gait = "quad", pattern = TROT, stride = 2.2, swing = 38, bounce = 0.25, headBob = 6, walkSpeed = 7,
		breathe = 0.05,
		step = { tex = "spark", c = { "#9ff5ff", "#2a6fff" }, size = { 0.5, 0 }, life = { 0.3, 0.6 }, speed = { 3, 6 },
			spread = 70, count = 8 },
		aura = { at = "Body", tex = "spark", c = { "#5ef0ff", "#2a6fff" }, size = { 0.45, 0 }, life = { 0.3, 0.6 },
			speed = { 2, 5 }, rate = 20, spread = 60 },
		idle = "bristle", every = { 5, 8 },
	},
	Glowmoth = {
		gait = "fly", stride = 8, swing = 0, bounce = 0.4, walkSpeed = 10, breathe = 0, lean = 12, flapBoost = 0.7,
		aura = { at = "Body", tex = "spark", c = { "#9ff5ff", "#8a5cff" }, size = { 0.4, 0 }, life = { 1.5, 2.5 },
			speed = { 0.3, 1 }, rate = 30, accel = Vector3.new(0, -1.5, 0), spread = 180 },
		idle = "dustburst", every = { 5, 8 },
	},
	HollowBadger = {
		gait = "quad", pattern = TROT, stride = 3.4, swing = 30, bounce = 0.3, roll = 5, headBob = 5, walkSpeed = 8,
		breathe = 0.06,
		step = { tex = "smoke", c = { "#9a7a52", "#6b5037" }, size = { 1, 2.6 }, life = { 0.6, 1.1 }, speed = { 2, 4 },
			spread = 70, count = 10, drag = 2, light = 0, accel = Vector3.new(0, -2, 0) },
		stepRing = { color = "#c9a36b", radius = 3, time = 0.35 },
		idle = "dig", every = { 6, 10 },
	},
	Barkling = {
		gait = "biped", stride = 3.2, swing = 30, armSwing = 28, bounce = 0.35, roll = 6, walkSpeed = 5, breathe = 0.06,
		step = { tex = "spark", c = { "#b8ff6a", "#46a846" }, size = { 0.6, 0 }, life = { 0.8, 1.4 }, speed = { 2, 5 },
			spread = 60, count = 12, accel = Vector3.new(0, -3, 0) },
		stepRing = { color = "#6fd35a", radius = 4, time = 0.45 },
		aura = { at = "CutTop", tex = "spark", c = { "#74d14c", "#f2c14e" }, size = { 0.5, 0.2 }, life = { 2, 3 },
			speed = { 0.5, 1.5 }, rate = 10, accel = Vector3.new(0, -2, 0), spread = 180, light = 0.3 },
		idle = "stretch", every = { 6, 10 },
	},
	WispLynx = {
		gait = "quad", pattern = TROT, stride = 5, swing = 32, bounce = 0.35, headBob = 5, walkSpeed = 12,
		breathe = 0.06,
		step = { tex = "fire", c = { "#9ff5ff", "#5ea8ff" }, size = { 1.2, 0 }, life = { 0.4, 0.7 }, speed = { 1, 3 },
			spread = 30, count = 10, accel = Vector3.new(0, 4, 0) },
		stepRing = { color = "#9ff5ff", radius = 3, time = 0.35 },
		aura = { at = "Body", tex = "smoke", c = { "#bfe8ff", "#5ea8ff" }, size = { 1.2, 3 }, life = { 0.8, 1.4 },
			speed = { 0.5, 1.5 }, rate = 14, spread = 180, transparency = 0.6 },
		idle = "phase", every = { 6, 10 },
	},
	Moonraven = {
		gait = "bird", stride = 1.6, swing = 32, bounce = 0.35, headBob = 16, walkSpeed = 5, breathe = 0.05,
		step = { tex = "spark", c = { "#ffffff", "#b9c8ff" }, size = { 0.5, 0 }, life = { 0.5, 1 }, speed = { 1, 3 },
			spread = 60, count = 6 },
		aura = { at = "Body", tex = "spark", c = { "#e8eeff", "#8a7dff" }, size = { 0.35, 0 }, life = { 1.5, 2.5 },
			speed = { 0.3, 1 }, rate = 10, accel = Vector3.new(0, -1, 0), spread = 180 },
		idle = "wingspread", every = { 6, 9 },
	},
	UmbraPanther = {
		gait = "quad", pattern = TROT, stride = 6.5, swing = 34, bounce = 0.3, headBob = 4, walkSpeed = 14,
		breathe = 0.07, lean = 4,
		step = { tex = "smoke", c = { "#2a1640", "#000000" }, size = { 1.5, 3.5 }, life = { 0.7, 1.2 }, speed = { 1, 3 },
			spread = 60, count = 10, light = 0, transparency = 0.3 },
		stepSpark = { tex = "spark", c = { "#d05cff", "#8a2bff" }, size = { 0.5, 0 }, life = { 0.4, 0.8 },
			speed = { 3, 7 }, spread = 70, count = 8 },
		stepRing = { color = "#b44bff", radius = 4, time = 0.4 },
		aura = { at = "Body", tex = "spark", c = { "#d05cff", "#3a1466" }, size = { 0.5, 0 }, life = { 0.4, 0.8 },
			speed = { 1, 3 }, rate = 20, spread = 180 },
		idle = "roar", every = { 6, 10 },
	},
	MosskingElk = {
		gait = "quad", pattern = WALK4, stride = 10, swing = 22, bounce = 0.25, headBob = 4, walkSpeed = 10,
		breathe = 0.1,
		step = { tex = "spark", c = { "#ff9ec4", "#bdfbff" }, size = { 0.7, 0 }, life = { 1, 1.8 }, speed = { 2, 5 },
			spread = 70, count = 12, accel = Vector3.new(0, -2, 0) },
		stepRing = { color = "#8fe05a", radius = 6, time = 0.5 },
		aura = { at = "Body", tex = "spark", c = { "#5ef0ff", "#b8ff6a" }, size = { 0.5, 0 }, life = { 2, 3 },
			speed = { 0.5, 1.5 }, rate = 12, accel = Vector3.new(0, 1.5, 0), spread = 180 },
		idle = "stomp", every = { 7, 11 },
	},
	NightshadeDrake = {
		gait = "quad", pattern = WALK4, stride = 8, swing = 24, bounce = 0.3, headBob = 5, walkSpeed = 10,
		breathe = 0.12, flapBoost = 0.6,
		step = { tex = "fire", c = { "#7dffc4", "#1f8a5a" }, size = { 1.5, 0 }, life = { 0.4, 0.8 }, speed = { 2, 5 },
			spread = 60, count = 12, accel = Vector3.new(0, 5, 0) },
		stepRing = { color = "#5ef0b0", radius = 6, time = 0.45 },
		aura = { at = "Body", tex = "spark", c = { "#7dffc4", "#5ef0b0" }, size = { 0.6, 0 }, life = { 0.8, 1.4 },
			speed = { 1, 3 }, rate = 20, accel = Vector3.new(0, 3, 0), spread = 180 },
		idle = "breath", every = { 7, 11 },
	},
	ThunderUnicorn = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 11, swing = 26, bounce = 0.45, headBob = 5,
		walkSpeed = 16, breathe = 0.1, maxCycles = 2.4,
		step = { tex = "spark", c = { "#fff7c2", "#4fd6ff" }, size = { 0.9, 0 }, life = { 0.3, 0.6 }, speed = { 6, 12 },
			spread = 75, count = 14, drag = 2 },
		stepSpark = { tex = "smoke", c = { "#c9d3f5", "#7f8cc0" }, size = { 1.6, 3.2 }, life = { 0.5, 0.9 },
			speed = { 2, 5 }, spread = 80, count = 5, light = 0, transparency = 0.5 },
		stepRing = { color = "#4fd6ff", radius = 5, time = 0.35 },
		aura = { at = "HornTip", tex = "spark", c = { "#ffffff", "#4fd6ff" }, size = { 0.6, 0 }, life = { 0.3, 0.6 },
			speed = { 2, 6 }, rate = 30, spread = 180 },
		idle = "thunder", every = { 7, 11 },
	},
	Pony = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 7, swing = 30, bounce = 0.4, headBob = 7,
		walkSpeed = 10, breathe = 0.08, maxCycles = 3,
		step = { tex = "smoke", c = { "#e8d2a8", "#b89a6a" }, size = { 1.2, 2.8 }, life = { 0.5, 0.9 },
			speed = { 2, 4 }, spread = 80, count = 5, light = 0, transparency = 0.5 },
		idle = "graze", every = { 5, 9 },
	},
	BrownHorse = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 10, swing = 26, bounce = 0.4, headBob = 5,
		walkSpeed = 12, breathe = 0.1, maxCycles = 2.6,
		step = { tex = "smoke", c = { "#e8d2a8", "#b89a6a" }, size = { 1.2, 2.8 }, life = { 0.5, 0.9 },
			speed = { 2, 4 }, spread = 80, count = 5, light = 0, transparency = 0.5 },
		idle = "paw", every = { 6, 10 },
	},
	PaintHorse = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 10, swing = 26, bounce = 0.4, headBob = 5,
		walkSpeed = 12, breathe = 0.1, maxCycles = 2.6,
		step = { tex = "smoke", c = { "#e8d2a8", "#b89a6a" }, size = { 1.2, 2.8 }, life = { 0.5, 0.9 },
			speed = { 2, 4 }, spread = 80, count = 5, light = 0, transparency = 0.5 },
		stepSpark = { tex = "spark", c = { "#ffffff", "#c99bff" }, size = { 0.6, 0 }, life = { 0.4, 0.8 },
			speed = { 3, 6 }, spread = 70, count = 6 },
		stepRing = { color = "#c99bff", radius = 3.5, time = 0.35 },
		idle = "toss", every = { 6, 10 },
		tossColor = { "#ffffff", "#c99bff" },
	},
	BlackStallion = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 11, swing = 26, bounce = 0.45, headBob = 5,
		walkSpeed = 13, breathe = 0.12, maxCycles = 2.5,
		step = { tex = "smoke", c = { "#6a6070", "#2a2430" }, size = { 1.4, 3.2 }, life = { 0.5, 0.9 },
			speed = { 2, 5 }, spread = 80, count = 6, light = 0, transparency = 0.45 },
		stepSpark = { tex = "spark", c = { "#fff2a8", "#ff9a1a" }, size = { 0.7, 0 }, life = { 0.3, 0.6 },
			speed = { 5, 10 }, spread = 70, count = 8, drag = 2 },
		stepRing = { color = "#ffcf3f", radius = 4.5, time = 0.35 },
		idle = "rear", every = { 7, 11 },
		rearRing = "#ffcf3f",
		rearBurst = { tex = "spark", c = { "#fff2a8", "#ff9a1a" }, size = { 0.9, 0 }, life = { 0.5, 1 },
			speed = { 6, 12 }, spread = 180, drag = 2 },
	},
	GoldenMustang = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 11, swing = 27, bounce = 0.45, headBob = 5,
		walkSpeed = 14, breathe = 0.1, maxCycles = 2.5,
		step = { tex = "spark", c = { "#fffbe6", "#ffc93c" }, size = { 0.9, 0 }, life = { 0.6, 1.2 },
			speed = { 3, 7 }, spread = 75, count = 12, accel = Vector3.new(0, 2, 0) },
		stepSpark = { tex = "smoke", c = { "#ffe8a8", "#d9a84c" }, size = { 1.2, 2.6 }, life = { 0.4, 0.8 },
			speed = { 2, 4 }, spread = 80, count = 4, light = 0, transparency = 0.55 },
		stepRing = { color = "#ffe27a", radius = 5, time = 0.4 },
		aura = { at = "Body", tex = "spark", c = { "#fffbe6", "#ffc93c" }, size = { 0.5, 0 }, life = { 0.8, 1.4 },
			speed = { 1, 3 }, rate = 10, spread = 180, accel = Vector3.new(0, 1.5, 0) },
		idle = "rear", every = { 7, 11 },
		rearRing = "#ffe27a",
		rearBurst = { tex = "spark", c = { "#ffffff", "#ffc93c" }, size = { 1.1, 0 }, life = { 0.8, 1.4 },
			speed = { 8, 16 }, spread = 180, drag = 2, accel = Vector3.new(0, 2, 0) },
	},
}

local profile = P[model:GetAttribute("AnimalId") or model.Name] or P.MossbackToad

-- --------------------------------------------------------------- setup --

local joints: { [string]: Motor6D } = {}
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

local function attribute(name: string, default: any): any
	local value = model:GetAttribute(name)
	if value == nil then
		return default
	end
	return value
end

local function part(name: string): BasePart
	local found = model:FindFirstChild(name, true)
	if found and found:IsA("BasePart") then
		return found
	end
	return root
end

local function seq(a: number, b: number): NumberSequence
	return NumberSequence.new({ NumberSequenceKeypoint.new(0, a), NumberSequenceKeypoint.new(1, b) })
end

-- One emitter per effect spec, on an attachment inside `parent` (the attachment follows that part).
local function makeEmitter(spec, parent: Instance): ParticleEmitter
	local e = Instance.new("ParticleEmitter")
	e.Enabled = false
	e.Texture = TEX[spec.tex or "spark"]
	e.Color = ColorSequence.new(hex(spec.c[1]), hex(spec.c[2] or spec.c[1]))
	e.Size = seq(spec.size[1], spec.size[2])
	e.Transparency = seq(spec.transparency or 0.1, 1)
	e.Lifetime = NumberRange.new(spec.life[1], spec.life[2])
	e.Speed = NumberRange.new(spec.speed[1], spec.speed[2])
	e.SpreadAngle = Vector2.new(spec.spread or 180, spec.spread or 180)
	e.Acceleration = spec.accel or Vector3.zero
	e.Drag = spec.drag or 0
	e.LightEmission = spec.light or 1
	e.LightInfluence = if (spec.light or 1) > 0 then 0 else 1
	e.Rotation = NumberRange.new(0, 360)
	e.RotSpeed = NumberRange.new(-90, 90)
	e.EmissionDirection = spec.dir or Enum.NormalId.Top
	e.Rate = spec.rate or 10
	e.Parent = parent
	return e
end

local function attachmentOn(target: BasePart, name: string): Attachment
	local a = Instance.new("Attachment")
	a.Name = name
	a.Parent = target
	return a
end

-- Step effects are emitted at a world position: this attachment is moved there first.
local stepPoint = attachmentOn(root, "FXStep")
local stepFx = profile.step and makeEmitter(profile.step, stepPoint)
local stepSpark = profile.stepSpark and makeEmitter(profile.stepSpark, stepPoint)

local aura = nil
if profile.aura then
	aura = makeEmitter(profile.aura, attachmentOn(part(profile.aura.at), "FXAura"))
	aura.Enabled = true
	aura.Rate = 0
end

local activeRings = 0
local function ring(cf: CFrame, color: string, radius: number, time: number)
	if activeRings >= 6 then
		return
	end
	activeRings += 1
	local p = Instance.new("Part")
	p.Name = "FXRing"
	p.Anchored = true
	p.CanCollide = false
	p.CanQuery = false
	p.CanTouch = false
	p.CastShadow = false
	p.Material = Enum.Material.Neon
	p.Color = hex(color)
	p.Shape = Enum.PartType.Cylinder
	p.Size = Vector3.new(0.15, 1, 1)
	p.CFrame = cf * CFrame.Angles(0, 0, math.rad(90))
	p.Transparency = 0.25
	p.Parent = workspace
	local info = TweenInfo.new(time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(p, info, { Size = Vector3.new(0.15, radius * 2, radius * 2), Transparency = 1 }):Play()
	task.delay(time, function()
		activeRings -= 1
	end)
	Debris:AddItem(p, time + 0.1)
end

local function groundY(): number
	return root.Position.Y - root.Size.Y / 2
end

local function groundRing(pos: Vector3, color: string, radius: number, time: number)
	ring(CFrame.new(pos.X, groundY() + 0.15, pos.Z), color, radius, time)
end

-- A one-off burst of particles from a part (effects for the idle actions).
local burstCache: { [string]: ParticleEmitter } = {}
local function burst(key: string, at: string, spec, count: number)
	local e = burstCache[key]
	if not e then
		e = makeEmitter(spec, attachmentOn(part(at), "FX" .. key))
		burstCache[key] = e
	end
	e:Emit(count)
end

-- An emitter that runs for a while (the drake's breath, the badger's digging).
local function stream(key: string, at: string, spec, seconds: number)
	local e = burstCache[key]
	if not e then
		e = makeEmitter(spec, attachmentOn(part(at), "FX" .. key))
		burstCache[key] = e
	end
	e.Enabled = true
	task.delay(seconds, function()
		e.Enabled = false
	end)
end

local fxOn = true

local function footstep(pos: Vector3)
	if not fxOn then
		return
	end
	stepPoint.WorldPosition = Vector3.new(pos.X, groundY() + 0.3, pos.Z)
	if stepFx then
		stepFx:Emit(profile.step.count or 8)
	end
	if stepSpark then
		stepSpark:Emit(profile.stepSpark.count or 6)
	end
	local r = profile.stepRing
	if r then
		groundRing(pos, r.color, r.radius, r.time)
	end
end

-- A lightning bolt from `from` down to `to`: a jagged line of Neon pieces that flashes and fades.
local function lightning(from: Vector3, to: Vector3, color: string, width: number)
	local points = { from }
	local steps = 8
	for i = 1, steps - 1 do
		local p = from:Lerp(to, i / steps)
		local jitter = (to - from).Magnitude / steps * 0.6
		table.insert(points, p + Vector3.new((math.random() - 0.5) * 2 * jitter, 0, (math.random() - 0.5) * 2 * jitter))
	end
	table.insert(points, to)
	local pieces = {}
	for i = 1, #points - 1 do
		local a, b = points[i], points[i + 1]
		local p = Instance.new("Part")
		p.Name = "FXBolt"
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.CastShadow = false
		p.Material = Enum.Material.Neon
		p.Color = hex(color)
		p.Size = Vector3.new(width, width, (b - a).Magnitude + width)
		p.CFrame = CFrame.lookAt((a + b) / 2, b)
		p.Parent = workspace
		table.insert(pieces, p)
	end
	local info = TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	for _, p in pieces do
		TweenService:Create(p, info, { Transparency = 1, Size = p.Size * Vector3.new(0.3, 0.3, 1) }):Play()
		Debris:AddItem(p, 0.5)
	end
end

-- A short, bright flash of light at a part.
local function flash(at: string, color: string, brightness: number, range: number, time: number)
	local light = Instance.new("PointLight")
	light.Color = hex(color)
	light.Brightness = brightness
	light.Range = range
	light.Shadows = false
	light.Parent = part(at)
	TweenService:Create(light, TweenInfo.new(time), { Brightness = 0 }):Play()
	Debris:AddItem(light, time + 0.1)
end

local function jointPos(name: string): Vector3
	local j = joints[name]
	return if j and j.Part1 then j.Part1.Position else root.Position
end

-- ------------------------------------------------------ idle actions --
-- Each action returns its pose for progress p (0..1): root offset, and extra rotation per joint.
-- `fire(p)` triggers the effects once when p passes a moment.

local R = math.rad
local ACTIONS = {}

local function ease(p: number, a: number, b: number): number
	-- 0 before a, rises to 1 at the middle of [a, b], back to 0 at b
	if p <= a or p >= b then
		return 0
	end
	return math.sin((p - a) / (b - a) * math.pi)
end

ACTIONS.croak = {
	time = 1.6,
	pose = function(p)
		local k = ease(p, 0.1, 0.9)
		return CFrame.new(0, k * 0.3, 0), { Head = CFrame.Angles(R(22) * k, 0, 0) }
	end,
	moments = { [0.35] = function()
		local head = part("Head")
		ring(head.CFrame * CFrame.new(0, 0, -1.5) * CFrame.Angles(R(90), 0, 0), "#b8ff6a", 5, 0.5)
		burst("Croak", "Head", { tex = "spark", c = { "#e3eba0", "#46a846" }, size = { 0.7, 0 }, life = { 0.8, 1.4 },
			speed = { 4, 8 }, spread = 40, dir = Enum.NormalId.Front }, 30)
	end, [0.6] = function()
		local head = part("Head")
		ring(head.CFrame * CFrame.new(0, 0, -1.5) * CFrame.Angles(R(90), 0, 0), "#8fe05a", 7, 0.6)
	end },
}

ACTIONS.spores = {
	time = 2.0,
	pose = function(p)
		local k = ease(p, 0.05, 0.6)
		return CFrame.new(0, -k * 0.2, 0), { Head = CFrame.Angles(-R(25) * k, 0, 0) }
	end,
	moments = { [0.4] = function()
		burst("Spores", "CapPeak", { tex = "spark", c = { "#ffffff", "#5ef0ff" }, size = { 0.8, 0 },
			life = { 2, 3.5 }, speed = { 4, 9 }, spread = 50, accel = Vector3.new(0, -1.5, 0), drag = 1 }, 60)
		groundRing(root.Position, "#9ff5ff", 6, 0.6)
	end },
}

ACTIONS.screech = {
	time = 1.4,
	pose = function(p)
		local k = ease(p, 0, 1)
		return CFrame.Angles(R(15) * k, 0, 0), {}
	end,
	flapBoost = 2.5,
	moments = { [0.2] = function()
		local nose = part("Nose")
		ring(nose.CFrame * CFrame.new(0, 0, -1) * CFrame.Angles(R(90), 0, 0), "#c77dff", 4, 0.4)
	end, [0.4] = function()
		local nose = part("Nose")
		ring(nose.CFrame * CFrame.new(0, 0, -2) * CFrame.Angles(R(90), 0, 0), "#b58cff", 6, 0.5)
		burst("Screech", "Nose", { tex = "spark", c = { "#d9b8ff", "#8a5cff" }, size = { 0.6, 0 }, life = { 0.5, 1 },
			speed = { 6, 12 }, spread = 35, dir = Enum.NormalId.Front }, 30)
	end, [0.6] = function()
		local nose = part("Nose")
		ring(nose.CFrame * CFrame.new(0, 0, -3) * CFrame.Angles(R(90), 0, 0), "#8a5cff", 8, 0.6)
	end },
}

ACTIONS.bristle = {
	time = 1.5,
	pose = function(p)
		local k = ease(p, 0.05, 0.95)
		return CFrame.new(0, -k * 0.35, 0) * CFrame.Angles(-R(6) * k, 0, 0), { Head = CFrame.Angles(R(15) * k, 0, 0) }
	end,
	moments = { [0.45] = function()
		burst("Bristle", "Body", { tex = "spark", c = { "#ffffff", "#2a8fff" }, size = { 0.7, 0 }, life = { 0.4, 0.9 },
			speed = { 8, 14 }, spread = 70, drag = 2 }, 50)
		groundRing(root.Position, "#5ef0ff", 7, 0.45)
	end },
}

ACTIONS.dustburst = {
	time = 1.8,
	pose = function(p)
		return CFrame.new(0, ease(p, 0, 1) * 0.8, 0), {}
	end,
	flapBoost = 1.8,
	moments = { [0.5] = function()
		burst("Dust", "Body", { tex = "spark", c = { "#9ff5ff", "#8a5cff" }, size = { 0.6, 0 }, life = { 2, 3.5 },
			speed = { 3, 8 }, spread = 180, drag = 2, accel = Vector3.new(0, -1, 0) }, 80)
		ring(CFrame.new(part("Body").Position), "#9ff5ff", 8, 0.6)
	end },
}

ACTIONS.dig = {
	time = 2.4,
	pose = function(p)
		local k = ease(p, 0, 1)
		local paddle = math.sin(p * 40) * k
		return CFrame.Angles(-R(10) * k, 0, 0), {
			Head = CFrame.Angles(-R(25) * k, 0, 0),
			LegFR = CFrame.Angles(R(35) * paddle, 0, 0),
			LegFL = CFrame.Angles(-R(35) * paddle, 0, 0),
		}
	end,
	moments = { [0.15] = function()
		stream("DigDirt", "PawFR", { tex = "smoke", c = { "#9a7a52", "#6b5037" }, size = { 0.8, 2 }, life = { 0.6, 1.2 },
			speed = { 4, 8 }, spread = 40, accel = Vector3.new(0, -12, 0), light = 0, rate = 40,
			dir = Enum.NormalId.Back }, 1.8)
	end, [0.5] = function()
		groundRing(part("PawFR").Position, "#c9a36b", 4, 0.4)
	end },
}

ACTIONS.stretch = {
	time = 2.4,
	pose = function(p)
		local k = ease(p, 0, 1)
		return CFrame.new(0, k * 0.4, 0), {
			ArmR = CFrame.Angles(0, 0, R(100) * k),
			ArmL = CFrame.Angles(0, 0, -R(100) * k),
		}
	end,
	orbitBoost = 6,
	moments = { [0.45] = function()
		burst("Leaves", "CutTop", { tex = "spark", c = { "#74d14c", "#f2c14e" }, size = { 0.8, 0.3 }, life = { 2, 3 },
			speed = { 4, 9 }, spread = 70, accel = Vector3.new(0, -3, 0), drag = 1, light = 0.3 }, 50)
		burst("Fireflies", "CutTop", { tex = "spark", c = { "#fff27a", "#b8ff6a" }, size = { 0.5, 0 },
			life = { 1.5, 2.5 }, speed = { 2, 5 }, spread = 180, drag = 1 }, 30)
		groundRing(root.Position, "#6fd35a", 8, 0.6)
	end },
}

ACTIONS.phase = {
	time = 2.2,
	pose = function(p)
		local k = ease(p, 0, 1)
		-- a cat stretch: front down, rear up
		return CFrame.Angles(-R(8) * k, 0, 0) * CFrame.new(0, -k * 0.2, 0), {
			LegFR = CFrame.Angles(-R(35) * k, 0, 0),
			LegFL = CFrame.Angles(-R(35) * k, 0, 0),
			Head = CFrame.Angles(R(15) * k, 0, 0),
		}
	end,
	moments = { [0.5] = function()
		burst("Wisp", "Body", { tex = "fire", c = { "#ffffff", "#5ea8ff" }, size = { 2, 0 }, life = { 0.6, 1.1 },
			speed = { 3, 8 }, spread = 180, accel = Vector3.new(0, 5, 0) }, 40)
		ring(CFrame.new(part("Body").Position), "#9ff5ff", 9, 0.6)
		groundRing(root.Position, "#5ea8ff", 7, 0.5)
	end },
}

ACTIONS.wingspread = {
	time = 2.0,
	pose = function(p)
		local k = ease(p, 0, 1)
		local flap = math.sin(p * 22) * 0.35 * k
		return CFrame.new(0, k * 0.3, 0), {
			WingR = CFrame.Angles(0, 0, R(75) * k + flap),
			WingL = CFrame.Angles(0, 0, -R(75) * k - flap),
			Head = CFrame.Angles(R(20) * k, 0, 0),
		}
	end,
	moments = { [0.45] = function()
		burst("Moon", "Body", { tex = "spark", c = { "#ffffff", "#b9c8ff" }, size = { 0.8, 0 }, life = { 1, 2 },
			speed = { 5, 10 }, spread = 180, drag = 2 }, 60)
		ring(CFrame.new(part("Body").Position), "#e8eeff", 8, 0.6)
	end },
}

ACTIONS.roar = {
	time = 2.0,
	pose = function(p)
		local up = ease(p, 0, 0.45)
		local roar = ease(p, 0.35, 1)
		return CFrame.Angles(R(6) * up, 0, 0), {
			Head = CFrame.Angles(R(28) * up - R(12) * roar, 0, 0) * CFrame.new(0, 0, -0.4 * roar),
			Tail = CFrame.Angles(R(30) * roar, 0, 0),
		}
	end,
	moments = { [0.45] = function()
		local nose = part("Nose")
		burst("RoarSmoke", "Nose", { tex = "smoke", c = { "#3a1466", "#000000" }, size = { 2, 5 }, life = { 0.8, 1.4 },
			speed = { 8, 14 }, spread = 30, drag = 3, light = 0, dir = Enum.NormalId.Front, transparency = 0.2 }, 30)
		burst("RoarSpark", "Nose", { tex = "spark", c = { "#ff9cff", "#8a2bff" }, size = { 0.7, 0 }, life = { 0.5, 1 },
			speed = { 10, 18 }, spread = 35, dir = Enum.NormalId.Front }, 40)
		ring(nose.CFrame * CFrame.new(0, 0, -2) * CFrame.Angles(R(90), 0, 0), "#b44bff", 7, 0.5)
		groundRing(root.Position, "#8a2bff", 14, 0.7)
	end },
}

ACTIONS.stomp = {
	time = 2.2,
	pose = function(p)
		local lift = ease(p, 0, 0.55)
		return CFrame.Angles(R(4) * lift, 0, 0), {
			LegFR = CFrame.Angles(-R(40) * lift, 0, 0),
			Head = CFrame.Angles(R(10) * lift - R(8) * ease(p, 0.5, 1), 0, 0),
		}
	end,
	moments = { [0.5] = function()
		local hoof = jointPos("LegFR")
		groundRing(hoof, "#8fe05a", 18, 0.8)
		stepPoint.WorldPosition = Vector3.new(hoof.X, groundY() + 0.3, hoof.Z)
		if stepFx then
			stepFx:Emit(50)
		end
		burst("Antlers", "Shroom0R", { tex = "spark", c = { "#bdfbff", "#5ef0ff" }, size = { 0.8, 0 }, life = { 1.5, 2.5 },
			speed = { 3, 7 }, spread = 180, accel = Vector3.new(0, 2, 0) }, 30)
		burst("AntlersL", "Shroom0L", { tex = "spark", c = { "#bdfbff", "#5ef0ff" }, size = { 0.8, 0 },
			life = { 1.5, 2.5 }, speed = { 3, 7 }, spread = 180, accel = Vector3.new(0, 2, 0) }, 30)
	end },
}

ACTIONS.breath = {
	time = 3.0,
	pose = function(p)
		local back = ease(p, 0, 0.35)
		local blow = ease(p, 0.25, 0.95)
		return CFrame.Angles(R(5) * back - R(4) * blow, 0, 0), {
			Head = CFrame.Angles(R(25) * back - R(15) * blow, 0, 0),
			Tail = CFrame.Angles(0, R(20) * math.sin(p * 12) * blow, 0),
		}
	end,
	moments = { [0.3] = function()
		local mouth = part("MouthGlow")
		stream("Breath", "MouthGlow", { tex = "fire", c = { "#c8ffe6", "#1f8a5a" }, size = { 1.5, 5 }, life = { 0.6, 1 },
			speed = { 18, 28 }, spread = 12, rate = 90, dir = Enum.NormalId.Front, drag = 1 }, 1.8)
		stream("BreathSmoke", "MouthGlow", { tex = "smoke", c = { "#2a6a4a", "#0c2222" }, size = { 2, 6 },
			life = { 1, 1.6 }, speed = { 8, 14 }, spread = 25, rate = 20, dir = Enum.NormalId.Front, light = 0,
			transparency = 0.4 }, 1.8)
		ring(mouth.CFrame * CFrame.new(0, 0, -2) * CFrame.Angles(R(90), 0, 0), "#7dffc4", 6, 0.5)
		groundRing(root.Position, "#5ef0b0", 16, 0.8)
	end },
}

-- Where the back hooves touch the ground, in the Root joint's frame (measured once, while nothing is posed yet).
-- Rearing up turns the body around this point.
local hindPivot = Vector3.new(0, -root.Size.Y / 2, 0)
do
	local rootJoint, leg = joints.Root, joints.LegBR or joints.LegBL
	if rootJoint and leg and leg.Part0 then
		local frame = root.CFrame * rootJoint.C0
		local hip = frame:PointToObjectSpace((leg.Part0.CFrame * leg.C0).Position)
		local ground = frame:PointToObjectSpace(root.Position - Vector3.new(0, root.Size.Y / 2, 0))
		hindPivot = Vector3.new(0, ground.Y, hip.Z)
	end
end

-- Rear up around the back hooves: lift the front, keep the hind legs on the ground, kick the front legs.
local function rearPose(p)
	local k = ease(p, 0.05, 0.85)
	local up = math.min(k * 1.6, 1)
	local pivot = hindPivot
	local tilt = R(30) * up
	local kick = math.sin(p * 30) * R(18) * up
	return CFrame.new(pivot) * CFrame.Angles(tilt, 0, 0) * CFrame.new(-pivot), {
		LegFR = CFrame.Angles(-R(70) * up + kick, 0, 0),
		LegFL = CFrame.Angles(-R(55) * up - kick, 0, 0),
		Head = CFrame.Angles(-R(18) * up, 0, 0),
		Tail = CFrame.Angles(R(25) * up, 0, 0),
	}
end

local function frontHoovesLand(count: number)
	for _, leg in { "LegFR", "LegFL" } do
		local hoof = jointPos(leg)
		stepPoint.WorldPosition = Vector3.new(hoof.X, groundY() + 0.3, hoof.Z)
		if stepFx then
			stepFx:Emit(count)
		end
		if stepSpark then
			stepSpark:Emit(math.floor(count / 2))
		end
	end
end

-- A horse rears up and whinnies, and lands with a shockwave.
ACTIONS.rear = {
	time = 2.4,
	pose = rearPose,
	moments = { [0.3] = function()
		if profile.rearBurst then
			burst("Rear", "Head", profile.rearBurst, 45)
		end
	end, [0.8] = function()
		frontHoovesLand(30)
		groundRing(root.Position, profile.rearRing or "#e8d2a8", 16, 0.7)
	end },
}

-- Lowers its head to nibble the grass, swishing its tail.
ACTIONS.graze = {
	time = 3.2,
	pose = function(p)
		local k = ease(p, 0.02, 0.98)
		local down = math.min(k * 1.8, 1)
		local chew = math.sin(p * 40) * R(4) * down
		return CFrame.Angles(-R(5) * down, 0, 0), {
			Head = CFrame.Angles(-R(65) * down + chew, 0, 0),
			Tail = CFrame.Angles(0, math.sin(p * 14) * R(25), 0),
		}
	end,
	moments = { [0.45] = function()
		burst("Graze", "Head", { tex = "spark", c = { "#8fe05a", "#3f9a3a" }, size = { 0.4, 0 }, life = { 0.5, 0.9 },
			speed = { 2, 4 }, spread = 120, accel = Vector3.new(0, -6, 0), light = 0 }, 10)
	end },
}

-- Paws at the ground with a front hoof, twice, kicking up dust.
ACTIONS.paw = {
	time = 2.2,
	pose = function(p)
		local k = ease(p, 0.05, 0.95)
		local scrape = 0.6 + 0.4 * math.sin(p * 4 * math.pi * 2)
		return CFrame.identity, {
			LegFR = CFrame.Angles(-R(45) * k * scrape, 0, 0),
			Head = CFrame.Angles(-R(12) * k, 0, 0),
		}
	end,
	moments = { [0.35] = function()
		local hoof = jointPos("LegFR")
		stepPoint.WorldPosition = Vector3.new(hoof.X, groundY() + 0.3, hoof.Z)
		if stepFx then
			stepFx:Emit(14)
		end
	end, [0.7] = function()
		local hoof = jointPos("LegFR")
		stepPoint.WorldPosition = Vector3.new(hoof.X, groundY() + 0.3, hoof.Z)
		if stepFx then
			stepFx:Emit(14)
		end
	end },
}

-- Tosses its head and mane from side to side.
ACTIONS.toss = {
	time = 1.8,
	pose = function(p)
		local k = ease(p, 0.05, 0.95)
		return CFrame.identity, {
			Head = CFrame.Angles(R(10) * k, math.sin(p * 3 * 2 * math.pi) * R(25) * k, math.sin(p * 3 * 2 * math.pi) * R(10) * k),
			Tail = CFrame.Angles(0, math.sin(p * 18) * R(20) * k, 0),
		}
	end,
	moments = { [0.5] = function()
		local c = profile.tossColor or { "#ffffff", "#ffffff" }
		burst("Toss", "Head", { tex = "spark", c = c, size = { 0.6, 0 }, life = { 0.5, 1 }, speed = { 4, 8 },
			spread = 180, drag = 2 }, 24)
	end },
}

ACTIONS.thunder = {
	time = 2.6,
	pose = rearPose,
	moments = { [0.32] = function()
		local tip = part("HornTip")
		lightning(tip.Position + Vector3.new(math.random(-6, 6), 45, math.random(-6, 6)), tip.Position, "#fff7c2", 0.6)
		lightning(tip.Position + Vector3.new(math.random(-8, 8), 40, math.random(-8, 8)), tip.Position, "#4fd6ff", 0.3)
		flash("HornTip", "#bff3ff", 12, 40, 0.6)
		burst("Thunder", "HornTip", { tex = "spark", c = { "#ffffff", "#4fd6ff" }, size = { 1.2, 0 },
			life = { 0.5, 1 }, speed = { 10, 20 }, spread = 180, drag = 3 }, 60)
		ring(tip.CFrame * CFrame.Angles(R(90), 0, 0), "#fff7c2", 8, 0.5)
	end, [0.8] = function()
		frontHoovesLand(40)
		groundRing(root.Position, "#4fd6ff", 22, 0.8)
		groundRing(root.Position, "#fff7c2", 14, 0.6)
		flash("Body", "#4fd6ff", 6, 30, 0.5)
	end },
}

-- ------------------------------------------------------------- update --

local rng = Random.new()
local start = os.clock()
local phase = rng:NextNumber(0, 10) -- so a group of the same animal doesn't move in sync
local lastPos = root.Position
local lastLook = root.CFrame.LookVector
local speed, turn, walk = 0, 0, 0
local gaitPhase = 0
local lastSin: { [string]: number } = {}
local nextAction = os.clock() + rng:NextNumber(2, 5)
local action, actionStart = nil, 0
local fired: { [number]: boolean } = {}
local posed = false

local function identityAll()
	for _, j in joints do
		j.Transform = CFrame.identity
	end
end

RunService.PreSimulation:Connect(function(dt)
	if not model.Parent or dt <= 0 then
		return
	end
	local now = os.clock()
	local t = now - start + phase

	-- Distance culling: far away animals don't animate at all, a bit closer they animate without effects.
	local camera = workspace.CurrentCamera
	local dist = if camera then (camera.CFrame.Position - root.Position).Magnitude else 0
	if dist > attribute("FXDistance", 160) * 1.6 then
		if posed then
			identityAll()
			posed = false
		end
		if aura then
			aura.Rate = 0
		end
		return
	end
	posed = true
	fxOn = dist < attribute("FXDistance", 160)

	-- How fast is the game moving us? (smoothed, horizontal only)
	local pos = root.Position
	local delta = pos - lastPos
	lastPos = pos
	local measured = Vector3.new(delta.X, 0, delta.Z).Magnitude / dt
	if measured > 200 then
		measured = 0 -- teleported
	end
	speed += (measured - speed) * math.min(1, dt * 6)
	local look = root.CFrame.LookVector
	local yawRate = math.asin(math.clamp(lastLook:Cross(look).Y, -1, 1)) / dt
	lastLook = look
	turn += (yawRate - turn) * math.min(1, dt * 4)

	local walkSpeed = attribute("WalkSpeed", profile.walkSpeed)
	local state = attribute("State", "")
	local effSpeed = speed
	if state == "Idle" then
		effSpeed = 0
	elseif state == "Walk" then
		effSpeed = walkSpeed
	elseif state == "Run" then
		effSpeed = walkSpeed * 1.8
	end
	local target = math.clamp(effSpeed / (walkSpeed * 0.35), 0, 1)
	walk += (target - walk) * math.min(1, dt * 5)
	local run = math.clamp((effSpeed / walkSpeed - 1) / 0.8, 0, 1)

	local cycles = math.max(effSpeed, walk * walkSpeed * 0.3) / profile.stride
	if profile.maxCycles then
		cycles = math.min(cycles, profile.maxCycles)
	end
	gaitPhase += dt * cycles * 2 * math.pi
	local swing = R(profile.swing) * walk * (1 + run * 0.35)

	-- Idle actions only when standing still.
	if not action and walk < 0.1 and attribute("IdleActions", true) and now > nextAction then
		local a = ACTIONS[profile.idle]
		if a then
			action, actionStart, fired = a, now, {}
		end
	end
	local actionRoot, actionJoints = CFrame.identity, {}
	local flapBoost, orbitBoost = 0, 0
	if action then
		local p = (now - actionStart) / action.time
		if p >= 1 or walk > 0.3 then
			action = nil
			local every = profile.every or { 6, 10 }
			nextAction = now + rng:NextNumber(every[1], every[2])
		else
			actionRoot, actionJoints = action.pose(p)
			flapBoost, orbitBoost = action.flapBoost or 0, action.orbitBoost or 0
			for moment, fn in action.moments do
				if p >= moment and not fired[moment] then
					fired[moment] = true
					if fxOn then
						fn()
					end
				end
			end
		end
	end

	-- Leg poses per gait, and footsteps when a foot comes down.
	local pose: { [string]: CFrame } = {}
	local gait = profile.gait
	local bounce = 0
	if gait == "quad" or gait == "biped" or gait == "bird" then
		local pattern = (run > 0.5 and profile.runPattern) or profile.pattern or { LegR = 0, LegL = 0.5 }
		for leg, offset in pattern do
			if joints[leg] then
				local s = math.sin(gaitPhase + offset * 2 * math.pi)
				local lift = math.max(0, math.cos(gaitPhase + offset * 2 * math.pi)) * 0.25 * walk
				pose[leg] = CFrame.new(0, lift, 0) * CFrame.Angles(s * swing, 0, 0)
				local prev = lastSin[leg] or s
				if prev > 0 and s <= 0 and walk > 0.4 then
					footstep(jointPos(leg))
				end
				lastSin[leg] = s
			end
		end
		bounce = math.abs(math.sin(gaitPhase * (if gait == "biped" or gait == "bird" then 1 else 2))) * profile.bounce * walk
		if gait == "biped" then
			local arm = R(profile.armSwing or 25) * walk
			pose.ArmR = CFrame.Angles(math.sin(gaitPhase + math.pi) * arm, 0, 0)
			pose.ArmL = CFrame.Angles(math.sin(gaitPhase) * arm, 0, 0)
		end
	elseif gait == "hop" then
		local cyc = (gaitPhase / (2 * math.pi)) % 1
		local air = math.sin(cyc * math.pi)
		bounce = air * profile.bounce * walk
		local legSwing = math.cos(cyc * 2 * math.pi) * swing
		for _, leg in { "LegFR", "LegFL" } do
			pose[leg] = CFrame.Angles(-legSwing * 0.6, 0, 0)
		end
		for _, leg in { "LegBR", "LegBL" } do
			pose[leg] = CFrame.Angles(legSwing, 0, 0)
		end
		local prev = lastSin.hop or air
		if prev < 0.15 and air >= 0.15 and walk > 0.4 then
			-- lands and pushes off: one big puff under the body
			footstep(root.Position)
		end
		lastSin.hop = air
	elseif gait == "slither" then
		local s = math.sin(gaitPhase)
		bounce = (s * 0.5 + 0.5) * profile.bounce * walk
		pose.Head = CFrame.new(0, 0, -s * 0.35 * walk)
		local prev = lastSin.slither or s
		if prev > 0 and s <= 0 and walk > 0.4 then
			footstep(part("Sole").Position + root.CFrame.LookVector * -3)
		end
		lastSin.slither = s
	end

	-- Body: breathing, bounce, lean into the movement and into turns.
	local breathe = math.sin(t * 2.2) * (profile.breathe or 0) * (1 - walk)
	local lean = R(profile.lean or 3) * walk * (1 + run)
	local roll = math.sin(gaitPhase) * R(profile.roll or 0) * walk - math.clamp(turn * 0.08, -0.25, 0.25) * walk
	local hover = attribute("Hover", 0)
	local hoverY = if hover > 0 then math.sin(t * attribute("HoverSpeed", 2)) * hover else 0
	if joints.Root then
		joints.Root.Transform = CFrame.new(0, hoverY + bounce + breathe, 0) * CFrame.Angles(-lean, 0, roll) * actionRoot
	end

	-- Head: looks around when idle, bobs when walking.
	if joints.Head then
		local lookYaw = math.noise(t * 0.25, 1.3) * R(35) * (1 - walk)
		local lookPitch = math.noise(t * 0.2, 7.1) * R(10) * (1 - walk)
		local bob = math.sin(gaitPhase * 2) * R(profile.headBob or 4) * walk
		local base = pose.Head or CFrame.identity
		if profile.gait == "bird" then
			base *= CFrame.new(0, 0, math.sin(gaitPhase * 2) * -0.4 * walk)
		end
		pose.Head = base * CFrame.Angles(lookPitch + bob, lookYaw, 0)
	end

	-- Tail: sways when idle, wags faster when walking.
	if joints.Tail then
		local sway = R(attribute("TailSway", 12))
		pose.Tail = CFrame.Angles(math.sin(gaitPhase * 2) * R(6) * walk,
			math.sin(t * (1.6 + walk * 3)) * sway * (1 + walk * 0.5), 0)
	end

	-- Wings: flap, faster when moving or during an action.
	local flapSpeed = attribute("FlapSpeed", 0)
	if flapSpeed > 0 then
		local boost = 1 + walk * (profile.flapBoost or 0) + flapBoost
		local angle = math.sin(t * flapSpeed * boost) * R(attribute("FlapAngle", 30))
		for name, _ in joints do
			if name:sub(1, 4) == "Wing" then
				local side = if name:sub(-1) == "L" then -1 else 1
				pose[name] = CFrame.Angles(0, 0, angle * side)
			end
		end
	elseif gait == "bird" then
		-- a walking bird holds its wings a little open for balance
		pose.WingR = CFrame.Angles(0, 0, R(12) * walk)
		pose.WingL = CFrame.Angles(0, 0, -R(12) * walk)
	end

	local orbit = attribute("OrbitSpeed", 0)
	if orbit ~= 0 and joints.Orbit then
		joints.Orbit.Transform = CFrame.Angles(0, t * orbit * (1 + orbitBoost + walk), 0)
	end

	for name, joint in joints do
		if name ~= "Root" and name ~= "Orbit" then
			local cf = pose[name] or CFrame.identity
			local extra = actionJoints[name]
			joint.Transform = if extra then cf * extra else cf
		end
	end

	if aura then
		aura.Rate = if fxOn then (profile.aura.rate or 10) * walk * (1 + run) else 0
	end
end)
