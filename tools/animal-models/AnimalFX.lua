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
	flamespark = "rbxasset://textures/particles/fire_sparks_main.dds",
	glow = "rbxasset://textures/particles/forcefield_glow_main.dds",
	vortex = "rbxasset://textures/particles/forcefield_vortex_main.dds",
	core = "rbxasset://textures/particles/explosion01_core_main.dds",
	shock = "rbxasset://textures/particles/explosion01_shockwave_main.dds",
	implode = "rbxasset://textures/particles/explosion01_implosion_main.dds",
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
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 11.5, swing = 27, bounce = 0.5, headBob = 5,
		walkSpeed = 16, breathe = 0.1, maxCycles = 2.4, flapBoost = 1.6, wingRun = 38,
		step = { tex = "spark", c = { "#e9fdff", "#4fe3ff" }, size = { 1.0, 0 }, life = { 0.3, 0.6 }, speed = { 6, 12 },
			spread = 75, count = 16, drag = 2 },
		stepSpark = { tex = "smoke", c = { "#a9b3e8", "#3d4580" }, size = { 1.8, 3.6 }, life = { 0.5, 0.9 },
			speed = { 2, 5 }, spread = 80, count = 5, light = 0, transparency = 0.5 },
		stepRing = { color = "#4fe3ff", radius = 6, time = 0.35 },
		stepBolt = { chance = 0.3, color = "#e9fdff", glow = "#4fe3ff" },
		aura = { at = "Body", tex = "spark", c = { "#ffffff", "#4fe3ff" }, size = { 0.7, 0 }, life = { 0.3, 0.6 },
			speed = { 3, 8 }, rate = 40, spread = 180 },
		idle = { "storm", "thunder" }, every = { 6, 10 },
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
	PebbleMarmot = {
		gait = "hop", stride = 2.6, swing = 30, bounce = 0.9, headBob = 6, walkSpeed = 7, breathe = 0.08,
		step = { tex = "smoke", c = { "#e8d8bc", "#b8a07a" }, size = { 0.9, 2.2 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3 }, spread = 80, count = 4, light = 0, transparency = 0.5 },
		idle = "graze", every = { 5, 9 },
	},
	PikaPuff = {
		gait = "hop", stride = 2.2, swing = 30, bounce = 1.0, headBob = 6, walkSpeed = 6, breathe = 0.1,
		step = { tex = "smoke", c = { "#e8d8bc", "#b8a07a" }, size = { 0.9, 2.2 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3 }, spread = 80, count = 4, light = 0, transparency = 0.5 },
		idle = "toss", every = { 5, 8 }, tossColor = { "#ffffff", "#ffe08a" },
	},
	CliffKid = {
		gait = "quad", pattern = TROT, runPattern = GALLOP, stride = 4, swing = 32, bounce = 0.6, headBob = 6,
		walkSpeed = 9, breathe = 0.08, maxCycles = 3.2,
		step = { tex = "smoke", c = { "#e8d8bc", "#b8a07a" }, size = { 0.9, 2.2 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3 }, spread = 80, count = 4, light = 0, transparency = 0.5 },
		idle = "toss", every = { 5, 9 }, tossColor = { "#ffffff", "#ffd23f" },
	},
	SnowshoeHare = {
		gait = "hop", stride = 4, swing = 34, bounce = 1.4, headBob = 6, walkSpeed = 9, breathe = 0.08,
		step = { tex = "smoke", c = { "#ffffff", "#d6e6f5" }, size = { 1.0, 2.4 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3.5 }, spread = 80, count = 5, light = 0, transparency = 0.45 },
		idle = "graze", every = { 5, 9 },
	},
	BighornRam = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 8, swing = 26, bounce = 0.4, headBob = 5,
		walkSpeed = 11, breathe = 0.1, maxCycles = 2.8,
		step = { tex = "smoke", c = { "#e8a070", "#b85532" }, size = { 1.2, 2.8 }, life = { 0.5, 0.9 },
			speed = { 2, 4 }, spread = 80, count = 5, light = 0, transparency = 0.45 },
		idle = "headbutt", every = { 6, 10 }, impactColor = "#ffb35a",
	},
	AlpineIbex = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 8, swing = 26, bounce = 0.4, headBob = 5,
		walkSpeed = 11, breathe = 0.1, maxCycles = 2.8,
		step = { tex = "smoke", c = { "#e8d8bc", "#b8a07a" }, size = { 0.9, 2.2 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3 }, spread = 80, count = 4, light = 0, transparency = 0.5 },
		idle = "graze", every = { 6, 10 },
	},
	RedPanda = {
		gait = "quad", pattern = TROT, stride = 3.4, swing = 30, bounce = 0.3, headBob = 5, walkSpeed = 8,
		breathe = 0.08,
		step = { tex = "smoke", c = { "#e8d8bc", "#b8a07a" }, size = { 0.9, 2.2 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3 }, spread = 80, count = 4, light = 0, transparency = 0.5 },
		idle = "graze", every = { 5, 9 },
	},
	PeakEagle = {
		gait = "bird", stride = 2.2, swing = 30, bounce = 0.35, headBob = 14, walkSpeed = 6, breathe = 0.06,
		step = { tex = "spark", c = { "#fff3b0", "#ffc93c" }, size = { 0.5, 0 }, life = { 0.5, 1 },
			speed = { 1, 3 }, spread = 60, count = 6 },
		aura = { at = "Body", tex = "spark", c = { "#fff3b0", "#ffc93c" }, size = { 0.4, 0 }, life = { 1, 1.8 },
			speed = { 0.4, 1.2 }, rate = 10, spread = 180 },
		idle = "wingspread", every = { 6, 9 },
	},
	MountainYak = {
		gait = "quad", pattern = WALK4, stride = 9, swing = 22, bounce = 0.3, headBob = 4, walkSpeed = 8,
		breathe = 0.12, maxCycles = 2.2,
		step = { tex = "smoke", c = { "#ffffff", "#d6e6f5" }, size = { 1.0, 2.4 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3.5 }, spread = 80, count = 5, light = 0, transparency = 0.45 },
		stepRing = { color = "#ffd23f", radius = 4, time = 0.4 },
		idle = "paw", every = { 6, 10 },
	},
	GeodeTortoise = {
		gait = "quad", pattern = WALK4, stride = 3, swing = 22, bounce = 0.1, headBob = 6, walkSpeed = 4,
		breathe = 0.05,
		step = { tex = "spark", c = { "#e9d6ff", "#b46bff" }, size = { 0.6, 0 }, life = { 0.5, 1 },
			speed = { 1, 3 }, spread = 70, count = 6 },
		idle = "graze", every = { 6, 10 },
	},
	SnowLeopard = {
		gait = "quad", pattern = TROT, runPattern = GALLOP, stride = 6.5, swing = 34, bounce = 0.3, headBob = 4,
		walkSpeed = 13, breathe = 0.07, lean = 4, maxCycles = 2.8,
		step = { tex = "spark", c = { "#e6fbff", "#7fe3ff" }, size = { 0.7, 0 }, life = { 0.4, 0.8 },
			speed = { 2, 5 }, spread = 70, count = 8 },
		stepSpark = { tex = "smoke", c = { "#ffffff", "#d6e6f5" }, size = { 1, 2.2 }, life = { 0.4, 0.7 },
			speed = { 1, 3 }, spread = 80, count = 3, light = 0, transparency = 0.5 },
		aura = { at = "Body", tex = "spark", c = { "#e6fbff", "#7fe3ff" }, size = { 0.45, 0 }, life = { 0.5, 1 },
			speed = { 1, 3 }, rate = 16, spread = 180 },
		idle = "howl", every = { 6, 10 }, howlColor = { "#e6fbff", "#7fe3ff" },
	},
	FrostfangAlpha = {
		gait = "quad", pattern = TROT, runPattern = GALLOP, stride = 7, swing = 34, bounce = 0.3, headBob = 4,
		walkSpeed = 14, breathe = 0.08, maxCycles = 2.8,
		step = { tex = "spark", c = { "#e6fbff", "#7fe3ff" }, size = { 0.8, 0 }, life = { 0.4, 0.8 },
			speed = { 3, 6 }, spread = 70, count = 10 },
		stepSpark = { tex = "smoke", c = { "#ffffff", "#bfe6ff" }, size = { 1.2, 2.6 }, life = { 0.4, 0.8 },
			speed = { 1, 3 }, spread = 80, count = 4, light = 0, transparency = 0.45 },
		stepRing = { color = "#7fe3ff", radius = 4, time = 0.35 },
		aura = { at = "Body", tex = "spark", c = { "#ffffff", "#7fe3ff" }, size = { 0.5, 0 }, life = { 0.4, 0.8 },
			speed = { 2, 5 }, rate = 20, spread = 180 },
		idle = "howl", every = { 6, 10 }, howlColor = { "#ffffff", "#7fe3ff" },
	},
	LittleYeti = {
		gait = "biped", pattern = { LegR = 0, LegL = 0.5 }, stride = 3.2, swing = 30, bounce = 0.5, headBob = 6,
		walkSpeed = 8, breathe = 0.1, armSwing = 30,
		step = { tex = "smoke", c = { "#ffffff", "#d6e6f5" }, size = { 1.0, 2.4 }, life = { 0.4, 0.8 },
			speed = { 1.5, 3.5 }, spread = 80, count = 5, light = 0, transparency = 0.45 },
		idle = "snowball", every = { 5, 9 },
	},
	SkyGriffin = {
		gait = "quad", pattern = WALK4, runPattern = GALLOP, stride = 11, swing = 26, bounce = 0.45, headBob = 5,
		walkSpeed = 15, breathe = 0.1, maxCycles = 2.5, flapBoost = 1.6, wingRun = 40,
		step = { tex = "spark", c = { "#fff3b0", "#ffc93c" }, size = { 1.0, 0 }, life = { 0.5, 1 },
			speed = { 4, 9 }, spread = 75, count = 14, drag = 2 },
		stepSpark = { tex = "smoke", c = { "#ffffff", "#f2e6c8" }, size = { 1.6, 3.4 }, life = { 0.5, 0.9 },
			speed = { 2, 5 }, spread = 80, count = 5, light = 0, transparency = 0.5 },
		stepRing = { color = "#ffc93c", radius = 6, time = 0.4 },
		aura = { at = "Body", tex = "spark", c = { "#ffffff", "#ffc93c" }, size = { 0.7, 0 }, life = { 0.6, 1.2 },
			speed = { 3, 7 }, rate = 36, spread = 180 },
		idle = { "skyroar", "toss" }, every = { 6, 10 }, tossColor = { "#fff3b0", "#ffc93c" },
	},
	GlacierMammoth = {
		gait = "quad", pattern = WALK4, stride = 10, swing = 22, bounce = 0.35, headBob = 4, walkSpeed = 9,
		breathe = 0.12, maxCycles = 2.2,
		step = { tex = "spark", c = { "#e6fbff", "#7fe3ff" }, size = { 1.0, 0 }, life = { 0.5, 1 },
			speed = { 3, 7 }, spread = 75, count = 14 },
		stepSpark = { tex = "smoke", c = { "#ffffff", "#bfe6ff" }, size = { 2, 4.5 }, life = { 0.6, 1.1 },
			speed = { 2, 5 }, spread = 80, count = 6, light = 0, transparency = 0.45 },
		stepRing = { color = "#7fe3ff", radius = 7, time = 0.45 },
		stepIce = 3,
		aura = { at = "Body", tex = "spark", c = { "#ffffff", "#7fe3ff" }, size = { 0.7, 0 }, life = { 0.6, 1.2 },
			speed = { 2, 6 }, rate = 30, spread = 180 },
		idle = { "glacierstomp", "paw" }, every = { 6, 10 },
	},
	AuroraDragon = {
		gait = "serpent", stride = 10, swing = 20, bounce = 0, headBob = 4, walkSpeed = 16, breathe = 0.06,
		waveP = 4, waveY = 7, lean = 6,
		aura = { at = "Seg4", tex = "spark", c = { "#ffffff", "#5effb0" }, size = { 0.9, 0 }, life = { 0.8, 1.6 },
			speed = { 2, 6 }, rate = 40, spread = 180 },
		idle = { "aurora" }, every = { 7, 11 },
	},
	Phoenix = {
		-- Struts like a proud bird, and takes off and flies when it moves fast (flyRun).
		gait = "bird", stride = 2.6, swing = 30, bounce = 0.35, headBob = 12, walkSpeed = 7, breathe = 0.08,
		flapBoost = 1.4, flyRun = true, flyHeight = 7, flyPitch = 42, flyHead = 32, flyTail = 45,
		step = { tex = "fire", c = { "#fffbe6", "#ff8a1f", "#8f1610" }, size = { 1.6, 0 }, life = { 0.4, 0.7 },
			speed = { 1, 3 }, spread = 40, count = 10, accel = Vector3.new(0, 6, 0) },
		stepSpark = { tex = "flamespark", c = { "#fffbe6", "#ffd23a", "#ff4a10" }, size = { 0.9, 0 },
			life = { 0.5, 1 }, speed = { 4, 8 }, spread = 70, count = 10, drag = 2, spin = 300 },
		stepRing = { color = "#ff6a14", radius = 4, time = 0.4 },
		idle = { "rebirth", "flamecry", "wingstretch", "ascend" }, every = { 6, 10 },
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
	if spec.c[3] then
		-- three colours: start, middle, end (white-hot -> orange -> deep red for fire)
		e.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, hex(spec.c[1])),
			ColorSequenceKeypoint.new(0.4, hex(spec.c[2])), ColorSequenceKeypoint.new(1, hex(spec.c[3])) })
	else
		e.Color = ColorSequence.new(hex(spec.c[1]), hex(spec.c[2] or spec.c[1]))
	end
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
	e.RotSpeed = NumberRange.new(-(spec.spin or 90), spec.spin or 90)
	e.EmissionDirection = spec.dir or Enum.NormalId.Top
	if spec.squash then
		e.Squash = seq(spec.squash, spec.squash)
	end
	if spec.orient then
		e.Orientation = Enum.ParticleOrientation[spec.orient]
	end
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
local running = 0 -- 0..1, how much the animal is running (set every frame)
local lightning: (Vector3, Vector3, string, number) -> () -- defined further down
local iceSpikes: (Vector3, number, number, number) -> () -- defined further down

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
	if profile.stepIce and math.random() < 0.35 then
		iceSpikes(Vector3.new(pos.X, groundY(), pos.Z), 2.5, profile.stepIce, 3)
	end
	local b = profile.stepBolt
	if b and running > 0.5 and math.random() < b.chance then
		local hit = Vector3.new(pos.X + math.random(-6, 6), groundY(), pos.Z + math.random(-6, 6))
		lightning(hit + Vector3.new(math.random(-4, 4), 40, math.random(-4, 4)), hit, b.color, 0.35)
		groundRing(hit, b.glow, 4, 0.3)
	end
end

-- A lightning bolt from `from` down to `to`: a jagged line of Neon pieces that flashes and fades.
function lightning(from: Vector3, to: Vector3, color: string, width: number)
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

-- Ice spikes that burst out of the ground in a ring and then melt away.
function iceSpikes(center: Vector3, radius: number, count: number, height: number)
	for i = 1, count do
		local ang = (i / count) * 2 * math.pi + math.random() * 0.3
		local h = height * (0.6 + math.random() * 0.6)
		local p = Instance.new("Part")
		p.Name = "FXIce"
		p.Anchored = true
		p.CanCollide = false
		p.CanQuery = false
		p.CanTouch = false
		p.CastShadow = false
		p.Material = Enum.Material.Glass
		p.Transparency = 0.2
		p.Color = hex(if i % 2 == 0 then "#bff3ff" else "#7fe3ff")
		local base = Vector3.new(center.X + math.cos(ang) * radius, center.Y, center.Z + math.sin(ang) * radius)
		local tilt = CFrame.Angles(math.rad(math.random(-25, 25)), ang, math.rad(math.random(-25, 25)))
		p.Size = Vector3.new(1.2, 0.2, 1.2)
		p.CFrame = CFrame.new(base) * tilt * CFrame.Angles(0, math.rad(45), 0)
		p.Parent = workspace
		local grown = CFrame.new(base) * tilt * CFrame.new(0, h / 2, 0) * CFrame.Angles(0, math.rad(45), 0)
		TweenService:Create(p, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out),
			{ Size = Vector3.new(1.4, h, 1.4), CFrame = grown }):Play()
		task.delay(1.1, function()
			TweenService:Create(p, TweenInfo.new(0.6), { Transparency = 1, Size = Vector3.new(0.3, h, 0.3) }):Play()
		end)
		Debris:AddItem(p, 1.8)
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

-- One-off flat effect lying on the ground (or in the air): a shockwave, a flaring sigil.
local function flatBurst(pos: Vector3, spec, count: number)
	local holder = Instance.new("Part")
	holder.Name = "FXFlat"
	holder.Anchored = true
	holder.CanCollide = false
	holder.CanQuery = false
	holder.CanTouch = false
	holder.Transparency = 1
	holder.Size = Vector3.new(0.2, 0.2, 0.2)
	holder.CFrame = CFrame.new(pos)
	holder.Parent = workspace
	local e = makeEmitter(spec, holder)
	e.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
	e.Speed = NumberRange.new(0.01)
	e.SpreadAngle = Vector2.zero
	e.Acceleration = Vector3.zero
	e:Emit(count)
	Debris:AddItem(holder, spec.life[2] + 0.3)
end

local FIRE3 = { "#fffbe6", "#ff8a1f", "#8f1610" }

-- A beat of burning wings in flight: sparks fly off both wing tips and a ring of heat pushes down.
local function wingbeat()
	for _, side in { "R", "L" } do
		burst("Beat" .. side, "Wing" .. side .. "Flame72", { tex = "flamespark", c = FIRE3, size = { 1.1, 0 },
			life = { 0.4, 0.8 }, speed = { 6, 12 }, spread = 40, drag = 3, dir = Enum.NormalId.Bottom, spin = 300 }, 14)
	end
	flatBurst(part("Body").Position - Vector3.new(0, 3, 0), { tex = "shock", c = { "#ffd23a", "#ff4a10" },
		size = { 3, 20 }, life = { 0.5, 0.5 }, transparency = 0.35, spin = 0 }, 1)
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

-- Rears up with its wings spread wide and calls a ring of lightning down around it.
ACTIONS.storm = {
	time = 3.2,
	flapBoost = 2,
	pose = function(p)
		local rootPose, legs = rearPose(p)
		local k = ease(p, 0.05, 0.9)
		local open = math.min(k * 1.5, 1)
		legs.WingR = CFrame.Angles(0, 0, R(55) * open)
		legs.WingL = CFrame.Angles(0, 0, -R(55) * open)
		return rootPose, legs
	end,
	moments = {
		[0.25] = function()
			local tip = part("HornTip")
			lightning(tip.Position + Vector3.new(0, 50, 0), tip.Position, "#e9fdff", 0.7)
			flash("HornTip", "#bff7ff", 14, 50, 0.7)
			burst("Storm", "HornTip", { tex = "spark", c = { "#ffffff", "#4fe3ff" }, size = { 1.4, 0 },
				life = { 0.6, 1.2 }, speed = { 12, 24 }, spread = 180, drag = 3 }, 70)
		end,
		[0.4] = function()
			for i = 1, 6 do
				local ang = i / 6 * 2 * math.pi + math.random() * 0.4
				local hit = Vector3.new(root.Position.X + math.cos(ang) * 14, groundY(), root.Position.Z + math.sin(ang) * 14)
				task.delay(i * 0.07, function()
					lightning(hit + Vector3.new(math.random(-5, 5), 45, math.random(-5, 5)), hit,
						if i % 2 == 0 then "#e9fdff" else "#ffe14d", 0.45)
					groundRing(hit, "#4fe3ff", 6, 0.4)
				end)
			end
		end,
		[0.82] = function()
			frontHoovesLand(45)
			groundRing(root.Position, "#4fe3ff", 28, 0.9)
			groundRing(root.Position, "#e9fdff", 18, 0.7)
			groundRing(root.Position, "#ffe14d", 10, 0.5)
			flash("Body", "#4fe3ff", 8, 40, 0.6)
		end,
	},
}

-- Lowers its head and charges a step forward: a head-butt with a shockwave.
ACTIONS.headbutt = {
	time = 1.6,
	pose = function(p)
		local lower = ease(p, 0.05, 0.9)
		local lunge = ease(p, 0.35, 0.75)
		return CFrame.new(0, 0, -1.4 * lunge), { Head = CFrame.Angles(-R(28) * lower, 0, 0) }
	end,
	moments = { [0.55] = function()
		local head = part("Head")
		ring(head.CFrame * CFrame.new(0, 0, -3) * CFrame.Angles(R(90), 0, 0), profile.impactColor or "#ffffff", 7, 0.4)
		burst("Butt", "Head", { tex = "smoke", c = { "#e8a070", "#b85532" }, size = { 1.5, 3 }, life = { 0.5, 0.9 },
			speed = { 4, 8 }, spread = 60, dir = Enum.NormalId.Front, light = 0, transparency = 0.4 }, 16)
		groundRing(root.Position, profile.impactColor or "#ffffff", 9, 0.5)
	end },
}

-- Throws its head up and howls, with a cold breath and a ring of frost.
ACTIONS.howl = {
	time = 2.2,
	pose = function(p)
		local up = ease(p, 0.05, 0.95)
		return CFrame.new(0, -0.2 * up, 0), { Head = CFrame.Angles(R(40) * up, 0, 0),
			Tail = CFrame.Angles(R(15) * up, 0, 0) }
	end,
	moments = { [0.35] = function()
		local c = profile.howlColor or { "#ffffff", "#ffffff" }
		local head = part("Head")
		burst("Howl", "Head", { tex = "smoke", c = c, size = { 1, 4 }, life = { 0.8, 1.4 }, speed = { 4, 8 },
			spread = 25, dir = Enum.NormalId.Top, light = 0.5, transparency = 0.4 }, 18)
		burst("HowlSpark", "Head", { tex = "spark", c = c, size = { 0.8, 0 }, life = { 0.8, 1.4 }, speed = { 4, 10 },
			spread = 180 }, 30)
		ring(head.CFrame * CFrame.new(0, 2, 0), c[2], 8, 0.6)
		groundRing(root.Position, c[2], 14, 0.8)
	end },
}

-- Winds up and throws a snowball, which bursts in a puff of snow.
ACTIONS.snowball = {
	time = 1.8,
	pose = function(p)
		local wind = ease(p, 0.05, 0.5)
		local throw = ease(p, 0.4, 0.9)
		return CFrame.Angles(R(6) * wind - R(10) * throw, 0, 0), {
			ArmR = CFrame.Angles(-R(70) * wind + R(130) * throw, 0, 0),
			Head = CFrame.Angles(R(10) * wind, 0, 0),
		}
	end,
	moments = { [0.62] = function()
		local ball = part("Snowball")
		local target = root.Position + root.CFrame.LookVector * 14
		burst("Snow", "Snowball", { tex = "smoke", c = { "#ffffff", "#d6e6f5" }, size = { 1.5, 3.5 },
			life = { 0.6, 1.0 }, speed = { 3, 6 }, spread = 40, dir = Enum.NormalId.Front, light = 0,
			transparency = 0.3 }, 20)
		groundRing(target, "#bfe6ff", 6, 0.5)
		stepPoint.WorldPosition = Vector3.new(target.X, groundY() + 0.3, target.Z)
		if stepFx then
			stepFx:Emit(30)
		end
		ring(CFrame.new(ball.Position), "#ffffff", 4, 0.3)
	end },
}

-- Rears up with its wings spread and lets out a cry: feathers, wind rings and a golden flash.
ACTIONS.skyroar = {
	time = 3.0,
	flapBoost = 2.5,
	pose = function(p)
		local rootPose, legs = rearPose(p)
		local open = math.min(ease(p, 0.05, 0.9) * 1.5, 1)
		legs.WingR = CFrame.Angles(0, 0, R(60) * open)
		legs.WingL = CFrame.Angles(0, 0, -R(60) * open)
		legs.Head = (legs.Head or CFrame.identity) * CFrame.Angles(R(25) * open, 0, 0)
		return rootPose, legs
	end,
	moments = {
		[0.3] = function()
			flash("Head", "#ffe08a", 10, 40, 0.7)
			burst("Feathers", "Body", { tex = "spark", c = { "#ffffff", "#ffc93c" }, size = { 1.2, 0 },
				life = { 1.2, 2.2 }, speed = { 10, 22 }, spread = 180, drag = 2, accel = Vector3.new(0, -3, 0) }, 80)
			local body = part("Body")
			for i = 0, 2 do
				task.delay(i * 0.15, function()
					ring(CFrame.new(body.Position + Vector3.new(0, 3 + i * 3, 0)), if i == 1 then "#ffffff" else "#ffc93c",
						14 + i * 6, 0.6)
				end)
			end
		end,
		[0.8] = function()
			frontHoovesLand(40)
			groundRing(root.Position, "#ffc93c", 26, 0.9)
			groundRing(root.Position, "#ffffff", 16, 0.6)
		end,
	},
}

-- Rears up and stomps: the ground freezes and ice spikes burst up in rings around it.
ACTIONS.glacierstomp = {
	time = 2.6,
	pose = function(p)
		local rootPose, legs = rearPose(p)
		legs.Head = (legs.Head or CFrame.identity) * CFrame.Angles(R(20) * ease(p, 0.05, 0.75), 0, 0)
		return rootPose, legs
	end,
	moments = {
		[0.3] = function()
			burst("Trumpet", "Head", { tex = "spark", c = { "#ffffff", "#7fe3ff" }, size = { 1, 0 }, life = { 0.8, 1.4 },
				speed = { 8, 16 }, spread = 40, dir = Enum.NormalId.Top }, 40)
			flash("Head", "#bff3ff", 8, 30, 0.5)
		end,
		[0.82] = function()
			frontHoovesLand(45)
			local c = Vector3.new(root.Position.X, groundY(), root.Position.Z)
			iceSpikes(c, 10, 12, 7)
			task.delay(0.15, function()
				iceSpikes(c, 16, 16, 5)
			end)
			groundRing(root.Position, "#7fe3ff", 30, 0.9)
			groundRing(root.Position, "#ffffff", 18, 0.6)
			flash("Body", "#7fe3ff", 8, 40, 0.6)
		end,
	},
}

-- Rises, coils, and bursts into the northern lights: rings of every aurora colour, stars and a flash.
ACTIONS.aurora = {
	time = 3.4,
	pose = function(p)
		local k = ease(p, 0.05, 0.95)
		return CFrame.new(0, 3 * k, 0) * CFrame.Angles(R(18) * k, 0, 0), { Head = CFrame.Angles(R(35) * k, 0, 0) }
	end,
	moments = {
		[0.35] = function()
			local head = part("Head")
			flash("Head", "#e9fff6", 14, 60, 0.9)
			burst("Stars", "Head", { tex = "spark", c = { "#ffffff", "#5effb0" }, size = { 1.4, 0 },
				life = { 1.2, 2.4 }, speed = { 10, 24 }, spread = 180, drag = 2 }, 90)
			local colors = { "#5effb0", "#3fd6ff", "#8a7bff", "#ff6bd6" }
			for i, c in colors do
				task.delay(i * 0.12, function()
					ring(CFrame.new(head.Position) * CFrame.Angles(R(90 * (i % 2)), R(45 * i), 0), c, 12 + i * 5, 0.8)
				end)
			end
		end,
		[0.6] = function()
			local colors = { "#5effb0", "#3fd6ff", "#b45cff" }
			for i, c in colors do
				task.delay(i * 0.1, function()
					groundRing(root.Position, c, 16 + i * 8, 0.9)
				end)
			end
		end,
	},
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

-- The Phoenix's idle actions. They use the wing tip, crest and tail tip joints when the model has them.

-- Rebirth: it wraps itself in its burning wings, the fire is sucked into it and it glows white-hot, then it bursts
-- open in a storm of fire: a fireball, a pillar of flame, a shockwave across the ground and a flaring sigil, ash,
-- and glowing feathers drifting down.
ACTIONS.rebirth = {
	time = 4.0,
	pose = function(p)
		local wrap = if p < 0.35 then math.sin(p / 0.35 * math.pi / 2) elseif p < 0.45 then 1
			else math.max(0, 1 - (p - 0.45) / 0.07)
		local settle = if p < 0.75 then 1 else math.cos((p - 0.75) / 0.25 * math.pi / 2)
		local open = if p < 0.45 then 0 else math.min(1, (p - 0.45) / 0.07) * settle
		local tremble = if p > 0.2 and p < 0.45 then math.sin(p * 140) * R(2.5) * wrap else 0
		return CFrame.new(0, -1.0 * wrap + 1.6 * open, 0), {
			WingR = CFrame.Angles(0, R(100) * wrap, -R(25) * wrap + R(70) * open + tremble),
			WingL = CFrame.Angles(0, -R(100) * wrap, R(25) * wrap - R(70) * open - tremble),
			WingTipR = CFrame.Angles(0, R(60) * wrap, -R(10) * wrap + R(25) * open),
			WingTipL = CFrame.Angles(0, -R(60) * wrap, R(10) * wrap - R(25) * open),
			Head = CFrame.Angles(-R(30) * wrap + R(35) * open, 0, 0),
			Tail = CFrame.Angles(-R(10) * wrap + R(20) * open, 0, 0),
			Crest = CFrame.Angles(-R(25) * wrap + R(20) * open, 0, 0),
		}
	end,
	moments = {
		[0.08] = function()
			stream("RebirthIn", "Body", { tex = "implode", c = { "#fff2a8", "#ff6a14" }, size = { 12, 1 },
				life = { 0.7, 0.7 }, speed = { 0, 0 }, rate = 3, transparency = 0.2, spin = 60 }, 1.4)
			stream("RebirthGlow", "Body", { tex = "fire", c = FIRE3, size = { 2.4, 0 }, life = { 0.4, 0.8 },
				speed = { 1, 3 }, spread = 180, rate = 60, accel = Vector3.new(0, 6, 0) }, 1.3)
			flash("Body", "#ff6a14", 3, 20, 1.4)
		end,
		[0.3] = function()
			flash("Body", "#fffbe6", 5, 24, 0.5)
			burst("RebirthCharge", "SunGem", { tex = "glow", c = { "#ffffff", "#ffd23a" }, size = { 2, 10 },
				life = { 0.5, 0.5 }, speed = { 0, 0 }, transparency = 0.3 }, 2)
		end,
		[0.45] = function()
			flash("Body", "#fff2a8", 14, 60, 1.0)
			burst("RebirthCore", "Body", { tex = "core", c = { "#fffbe6", "#ffb52e", "#ff4a10" }, size = { 6, 26 },
				life = { 0.7, 0.9 }, speed = { 0, 0 }, transparency = 0.1, spin = 40 }, 3)
			burst("RebirthFire", "Body", { tex = "fire", c = FIRE3, size = { 5, 0 }, life = { 0.6, 1.2 },
				speed = { 16, 30 }, spread = 180, drag = 3 }, 120)
			burst("RebirthEmbers", "Body", { tex = "flamespark", c = FIRE3, size = { 1.2, 0 }, life = { 1.2, 2.4 },
				speed = { 12, 26 }, spread = 180, drag = 2, accel = Vector3.new(0, 2, 0), spin = 400 }, 160)
			stream("RebirthPillar", "SigilCore", { tex = "fire", c = FIRE3, size = { 4, 0 }, life = { 0.5, 0.9 },
				speed = { 35, 50 }, spread = 6, rate = 140, accel = Vector3.new(0, 10, 0) }, 0.8)
			local ground = Vector3.new(root.Position.X, groundY() + 0.3, root.Position.Z)
			flatBurst(ground, { tex = "shock", c = { "#ffd23a", "#ff4a10" }, size = { 6, 70 }, life = { 0.9, 0.9 },
				transparency = 0.2, spin = 0 }, 1)
			flatBurst(ground, { tex = "vortex", c = { "#fff2a8", "#ff4a10" }, size = { 36, 30 }, life = { 1.8, 1.8 },
				transparency = 0.25, spin = 160 }, 1)
			local body = part("Body")
			for i = 0, 2 do
				task.delay(i * 0.12, function()
					ring(CFrame.new(body.Position + Vector3.new(0, 2 + i * 4, 0)), if i == 1 then "#fff2a8" else "#ff6a14",
						14 + i * 7, 0.6)
				end)
			end
			groundRing(root.Position, "#ff6a14", 30, 0.9)
			groundRing(root.Position, "#fff2a8", 18, 0.6)
		end,
		[0.62] = function()
			burst("RebirthAsh", "Body", { tex = "smoke", c = { "#5a2a1a", "#1a0a05" }, size = { 3, 7 }, life = { 1.2, 2 },
				speed = { 4, 8 }, spread = 180, light = 0, transparency = 0.45, accel = Vector3.new(0, 3, 0) }, 30)
			burst("RebirthFeathers", "Body", { tex = "flamespark", c = FIRE3, size = { 0.9, 0.5 }, life = { 2.5, 3.5 },
				speed = { 6, 12 }, spread = 180, drag = 2.5, accel = Vector3.new(0, -3, 0), squash = 1.6, spin = 120 }, 40)
		end,
	},
}

-- Flame cry: throws its head back, raises its wings and screams a pillar of fire into the sky.
ACTIONS.flamecry = {
	time = 2.8,
	flapBoost = 1.5,
	pose = function(p)
		local up = ease(p, 0, 1)
		local cry = ease(p, 0.3, 0.85)
		return CFrame.new(0, up * 0.8, 0) * CFrame.Angles(R(8) * up, 0, 0), {
			WingR = CFrame.Angles(0, 0, R(55) * up + math.sin(p * 30) * R(6) * cry),
			WingL = CFrame.Angles(0, 0, -R(55) * up - math.sin(p * 30) * R(6) * cry),
			WingTipR = CFrame.Angles(0, 0, R(25) * up),
			WingTipL = CFrame.Angles(0, 0, -R(25) * up),
			Head = CFrame.Angles(R(40) * up + math.sin(p * 50) * R(3) * cry, 0, 0),
			Crest = CFrame.Angles(R(15) * cry, 0, 0),
			Tail = CFrame.Angles(R(18) * up, 0, 0),
		}
	end,
	moments = {
		[0.32] = function()
			flash("Head", "#ffd23a", 8, 40, 1.2)
			stream("CryFire", "Head", { tex = "fire", c = FIRE3, size = { 3.2, 0 }, life = { 0.5, 0.9 },
				speed = { 28, 42 }, spread = 9, rate = 110, accel = Vector3.new(0, 8, 0) }, 1.3)
			stream("CrySparks", "Head", { tex = "flamespark", c = FIRE3, size = { 1, 0 }, life = { 0.8, 1.4 },
				speed = { 20, 34 }, spread = 20, rate = 60, drag = 1, spin = 300 }, 1.3)
			local head = part("Head")
			for i = 0, 3 do
				task.delay(i * 0.18, function()
					ring(CFrame.new(head.Position + Vector3.new(0, 6 + i * 6, 0)),
						if i % 2 == 0 then "#ffd23a" else "#ff6a14", 6 + i * 3, 0.5)
				end)
			end
			groundRing(root.Position, "#ff6a14", 18, 0.8)
		end,
	},
}

-- Wing stretch: stretches one burning wing out low and wide, shakes the sparks off it, then the other one.
ACTIONS.wingstretch = {
	time = 3.6,
	pose = function(p)
		local r = ease(p, 0.02, 0.5)
		local l = ease(p, 0.5, 0.98)
		local shakeR = math.sin(p * 90) * R(4) * ease(p, 0.2, 0.4)
		local shakeL = math.sin(p * 90) * R(4) * ease(p, 0.7, 0.9)
		return CFrame.Angles(0, 0, R(6) * (l - r)), {
			WingR = CFrame.Angles(0, -R(20) * r, R(10) * r + shakeR),
			WingTipR = CFrame.Angles(0, -R(15) * r, -R(18) * r),
			WingL = CFrame.Angles(0, R(20) * l, -R(10) * l - shakeL),
			WingTipL = CFrame.Angles(0, R(15) * l, R(18) * l),
			Head = CFrame.Angles(-R(10) * (r + l), R(35) * r - R(35) * l, 0),
			Tail = CFrame.Angles(0, R(12) * (r - l), 0),
		}
	end,
	moments = {
		[0.3] = function()
			burst("ShakeR", "WingRFlame42", { tex = "flamespark", c = FIRE3, size = { 0.9, 0 }, life = { 0.6, 1.2 },
				speed = { 5, 10 }, spread = 90, drag = 2, accel = Vector3.new(0, -4, 0), spin = 300 }, 30)
		end,
		[0.8] = function()
			burst("ShakeL", "WingLFlame42", { tex = "flamespark", c = FIRE3, size = { 0.9, 0 }, life = { 0.6, 1.2 },
				speed = { 5, 10 }, spread = 90, drag = 2, accel = Vector3.new(0, -4, 0), spin = 300 }, 30)
		end,
	},
}

-- Ascend: crouches, leaps up with a blast of fire and hovers on beating wings, turns once round in a spiral of
-- flame, then drops back down and lands with a shockwave.
ACTIONS.ascend = {
	time = 4.4,
	pose = function(p)
		local crouch = ease(p, 0, 0.2)
		local up = if p < 0.15 then 0 elseif p < 0.28 then math.sin((p - 0.15) / 0.13 * math.pi / 2)
			elseif p < 0.78 then 1 elseif p < 0.9 then math.cos((p - 0.78) / 0.12 * math.pi / 2) else 0
		local spin = if p < 0.32 then 0 elseif p < 0.72 then (1 - math.cos((p - 0.32) / 0.4 * math.pi)) / 2 else 1
		local land = ease(p, 0.88, 1)
		local flap = math.sin(p * 70) * up
		local tip = math.sin(p * 70 - 1.1) * up
		return CFrame.new(0, -0.8 * crouch + 6.5 * up + math.sin(p * 35) * 0.4 * up - 0.6 * land, 0)
			* CFrame.Angles(0, spin * 2 * math.pi, 0), {
			WingR = CFrame.Angles(0, 0, R(40) * flap + R(15) * up + R(20) * crouch),
			WingL = CFrame.Angles(0, 0, -R(40) * flap - R(15) * up - R(20) * crouch),
			WingTipR = CFrame.Angles(0, 0, R(30) * tip),
			WingTipL = CFrame.Angles(0, 0, -R(30) * tip),
			LegL = CFrame.Angles(-R(60) * up, 0, 0),
			LegR = CFrame.Angles(-R(60) * up, 0, 0),
			Head = CFrame.Angles(R(12) * up - R(15) * crouch, 0, 0),
			Tail = CFrame.Angles(R(15) * up, 0, 0),
		}
	end,
	moments = {
		[0.16] = function()
			local ground = Vector3.new(root.Position.X, groundY() + 0.3, root.Position.Z)
			flatBurst(ground, { tex = "shock", c = { "#ffd23a", "#ff4a10" }, size = { 4, 34 }, life = { 0.6, 0.6 },
				transparency = 0.25, spin = 0 }, 1)
			groundRing(root.Position, "#ff6a14", 14, 0.6)
			burst("LaunchFire", "SigilCore", { tex = "fire", c = FIRE3, size = { 3, 0 }, life = { 0.4, 0.8 },
				speed = { 8, 16 }, spread = 70, drag = 2, accel = Vector3.new(0, 6, 0) }, 60)
		end,
		[0.32] = function()
			for _, side in { "R", "L" } do
				stream("Spiral" .. side, "Wing" .. side .. "Flame72", { tex = "fire", c = FIRE3, size = { 2.2, 0 },
					life = { 0.5, 0.9 }, speed = { 0.5, 2 }, spread = 30, rate = 70, accel = Vector3.new(0, 3, 0) }, 1.7)
			end
		end,
		[0.88] = function()
			local ground = Vector3.new(root.Position.X, groundY() + 0.3, root.Position.Z)
			flash("Body", "#ffd23a", 8, 40, 0.6)
			flatBurst(ground, { tex = "shock", c = { "#ffd23a", "#ff4a10" }, size = { 6, 55 }, life = { 0.8, 0.8 },
				transparency = 0.2, spin = 0 }, 1)
			flatBurst(ground, { tex = "vortex", c = { "#fff2a8", "#ff4a10" }, size = { 28, 22 }, life = { 1.4, 1.4 },
				transparency = 0.3, spin = 140 }, 1)
			groundRing(root.Position, "#ff6a14", 24, 0.8)
			groundRing(root.Position, "#fffbe6", 14, 0.6)
			burst("LandSparks", "SigilCore", { tex = "flamespark", c = FIRE3, size = { 1.2, 0 }, life = { 0.6, 1.2 },
				speed = { 14, 24 }, spread = 85, drag = 3, spin = 400 }, 70)
		end,
	},
}

-- ------------------------------------------------------------- update --

-- Flight effects (flyRun animals): a comet trail of fire behind the body, afterburn flames, more ember feathers,
-- a blast on takeoff and a shockwave on landing, and the fire ring on the ground hidden while it flies.
local flight = nil
if profile.flyRun then
	local body = part("Body")
	local half = body.Size.Y / 2
	local top = attachmentOn(body, "FXFlightTop")
	top.Position = Vector3.new(0, half, 0)
	local bottom = attachmentOn(body, "FXFlightBottom")
	bottom.Position = Vector3.new(0, -half, 0)
	local trail = Instance.new("Trail")
	trail.Name = "FlightTrail"
	trail.Attachment0 = top
	trail.Attachment1 = bottom
	trail.Texture = TEX.fire
	trail.TextureMode = Enum.TextureMode.Stretch
	trail.Lifetime = 0.9
	trail.LightEmission = 1
	trail.LightInfluence = 0
	trail.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, hex("#fffbe6")),
		ColorSequenceKeypoint.new(0.3, hex("#ffb52e")), ColorSequenceKeypoint.new(1, hex("#8f1610")) })
	trail.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.1), NumberSequenceKeypoint.new(1, 1) })
	trail.WidthScale = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.2) })
	trail.Enabled = false
	trail.Parent = body
	local back = attachmentOn(body, "FXAfterburn")
	back.Position = Vector3.new(0, 0, body.Size.Z / 2)
	local burn = makeEmitter({ tex = "fire", c = FIRE3, size = { 3, 0 }, life = { 0.3, 0.6 }, speed = { 3, 7 },
		spread = 25, dir = Enum.NormalId.Back, rate = 0 }, back)
	burn.Enabled = true
	local ground, embers = {}, {}
	for _, d in model:GetDescendants() do
		if d:IsA("BasePart") and (d.Name:sub(1, 8) == "FireRing" or d.Name == "SigilCore") then
			table.insert(ground, { part = d, t = d.Transparency })
		elseif d:IsA("ParticleEmitter") and d.Name == "EmberFeathers" then
			table.insert(embers, { e = d, rate = d.Rate })
		end
	end
	flight = { trail = trail, burn = burn, ground = ground, embers = embers, up = false }
end

local function setFlying(up: boolean)
	flight.up = up
	flight.trail.Enabled = up
	for _, g in flight.ground do
		g.part.Transparency = if up then 1 else g.t
		for _, e in g.part:GetChildren() do
			if e:IsA("ParticleEmitter") then
				e.Enabled = not up
			end
		end
	end
	if not fxOn then
		return
	end
	local ground = Vector3.new(root.Position.X, groundY() + 0.3, root.Position.Z)
	if up then
		-- takeoff: a blast of fire pushes off the ground
		flatBurst(ground, { tex = "shock", c = { "#ffd23a", "#ff4a10" }, size = { 4, 40 }, life = { 0.6, 0.6 },
			transparency = 0.25, spin = 0 }, 1)
		groundRing(root.Position, "#ff6a14", 16, 0.6)
		burst("Takeoff", "Body", { tex = "fire", c = FIRE3, size = { 3.5, 0 }, life = { 0.4, 0.8 }, speed = { 10, 18 },
			spread = 50, drag = 2, dir = Enum.NormalId.Bottom }, 50)
	else
		-- landing: a shockwave and the sigil flares up again
		flatBurst(ground, { tex = "shock", c = { "#ffd23a", "#ff4a10" }, size = { 6, 50 }, life = { 0.8, 0.8 },
			transparency = 0.2, spin = 0 }, 1)
		flatBurst(ground, { tex = "vortex", c = { "#fff2a8", "#ff4a10" }, size = { 26, 20 }, life = { 1.4, 1.4 },
			transparency = 0.3, spin = 140 }, 1)
		groundRing(root.Position, "#ff6a14", 22, 0.8)
		groundRing(root.Position, "#fffbe6", 12, 0.5)
		burst("Landing", "SigilCore", { tex = "flamespark", c = FIRE3, size = { 1.2, 0 }, life = { 0.6, 1.2 },
			speed = { 14, 24 }, spread = 85, drag = 3, spin = 400 }, 60)
	end
end

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
local air, lastFlap = 0, 0 -- flight (0 = on the ground, 1 = flying) and the last wing beat, for flyRun animals
local flightClock, flightPhase = 0, 0

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
	running = run
	-- Animals with flyRun take off when they move fast (or when the game sets State = "Fly").
	local airTarget = if profile.flyRun and (run > 0.25 or state == "Fly") then 1 else 0
	air += (airTarget - air) * math.min(1, dt * 2.5)
	-- Flight rhythm: a few strong wing beats, then a glide on spread wings, then beats again.
	flightClock = if air > 0.01 then flightClock + dt else 0
	local flightCyc = flightClock % 4.2
	local flapAmt = if flightCyc < 2.4 then 1 elseif flightCyc < 2.8 then 1 - (flightCyc - 2.4) / 0.4
		elseif flightCyc < 3.9 then 0 else (flightCyc - 3.9) / 0.3
	flapAmt = flapAmt * flapAmt * (3 - 2 * flapAmt)
	flightPhase += dt * 7.5 * (0.3 + 0.7 * flapAmt)
	if flight then
		if not flight.up and air > 0.35 then
			setFlying(true)
		elseif flight.up and air < 0.25 then
			setFlying(false)
		end
		flight.burn.Rate = if fxOn then 45 * air * (0.4 + 0.6 * flapAmt) else 0
		for _, em in flight.embers do
			em.e.Rate = em.rate * (1 + 3 * air)
		end
	end

	local cycles = math.max(effSpeed, walk * walkSpeed * 0.3) / profile.stride
	if profile.maxCycles then
		cycles = math.min(cycles, profile.maxCycles)
	end
	gaitPhase += dt * cycles * 2 * math.pi
	local swing = R(profile.swing) * walk * (1 + run * 0.35)

	-- Idle actions only when standing still.
	if not action and walk < 0.1 and attribute("IdleActions", true) and now > nextAction then
		local idle = profile.idle
		if type(idle) == "table" then
			idle = idle[rng:NextInteger(1, #idle)]
		end
		local a = ACTIONS[idle]
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
				if prev > 0 and s <= 0 and walk > 0.4 and air < 0.5 then
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
	elseif gait == "serpent" then
		-- A long body that ripples like a ribbon: every joint along it swings a little behind the one before.
		local speedUp = 1 + walk * (1 + run)
		local i = 1
		while joints["SegJoint" .. i] do
			local w = t * 1.8 * speedUp - i * 0.6
			pose["SegJoint" .. i] = CFrame.Angles(math.sin(w) * R(profile.waveP or 5),
				math.sin(w * 0.75 + 1) * R(profile.waveY or 7) * (1 + walk * 0.5), 0)
			i += 1
		end
		for _, leg in { "LegFR", "LegFL", "LegBR", "LegBL" } do
			pose[leg] = CFrame.Angles(math.sin(t * 2 + #leg) * R(15), 0, 0)
		end
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
		-- In flight: lifted up, tipped forward so it lies flat in the air, rising with each beat, swaying in the
		-- glide, and banking into turns.
		local flyLift = air * (profile.flyHeight or 4) + math.sin(flightPhase - 0.6) * 0.5 * air * flapAmt
			+ math.sin(t * 1.1) * 0.4 * air * (1 - flapAmt)
		local bank = -math.clamp(turn * 0.35, -0.6, 0.6) * air + math.sin(t * 0.9) * R(4) * air * (1 - flapAmt)
		joints.Root.Transform = CFrame.new(0, hoverY + bounce * (1 - air) + breathe + flyLift, 0)
			* CFrame.Angles(-lean * (1 - air) - R(profile.flyPitch or 0) * air, 0, roll * (1 - air) + bank) * actionRoot
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
			+ R(profile.wingRun or 0) * run
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

	-- Secondary motion (Phoenix): the wing tips trail behind every beat, the far half of the tail ripples like
	-- a flame, the crest flickers and the halo turns. In flight the wings beat hard and the legs tuck in.
	if joints.WingTipR or joints.TailTip or joints.Crest or joints.Halo then
		local boost = 1 + walk * (profile.flapBoost or 0) + flapBoost
		local flapAngle = R(attribute("FlapAngle", 30))
		local beat = t * flapSpeed * boost
		local wingAngle = math.sin(beat) * flapAngle + R(8) * walk
		local tipAngle = math.sin(beat - 0.9) * flapAngle * 0.9 - R(6) * walk
		if air > 0.01 then
			local f = flightPhase
			local flap = math.sin(f)
			-- beating: big strokes with the tips whipping behind; gliding: wings spread flat, tips curled up a little
			-- (the wings rest raised; in the air they come down level with the body)
			local glideWing = -R(34) + math.sin(t * 1.3) * R(3)
			local flyWing = (flap * R(48) - R(16)) * flapAmt + glideWing * (1 - flapAmt)
			local flyTip = (math.sin(f - 1.1) * R(35) - R(4)) * flapAmt + R(12) * (1 - flapAmt)
			wingAngle = wingAngle * (1 - air) + flyWing * air
			tipAngle = tipAngle * (1 - air) + flyTip * air
			if lastFlap > 0 and flap <= 0 and air > 0.6 and flapAmt > 0.5 and fxOn then
				wingbeat()
			end
			lastFlap = flap
			for _, leg in { "LegL", "LegR" } do
				if joints[leg] then
					pose[leg] = (pose[leg] or CFrame.identity):Lerp(CFrame.new(0, 0.6, 0.3) * CFrame.Angles(-R(65), 0, 0), air)
				end
			end
			pose.Tail = (pose.Tail or CFrame.identity) * CFrame.Angles(R(profile.flyTail or 12) * air, 0, 0)
			pose.Head = (pose.Head or CFrame.identity) * CFrame.Angles(R(profile.flyHead or 8) * air, 0, 0)
		end
		for _, side in { "R", "L" } do
			local sgn = if side == "L" then -1 else 1
			if joints["Wing" .. side] then
				pose["Wing" .. side] = CFrame.Angles(0, 0, (wingAngle + R(profile.wingRun or 0) * run * (1 - air)) * sgn)
			end
			if joints["WingTip" .. side] then
				pose["WingTip" .. side] = CFrame.Angles(0, 0, tipAngle * sgn)
			end
		end
		if joints.TailTip then
			pose.TailTip = CFrame.Angles(math.sin(t * 2.2 - 0.9) * R(7) * (1 + air) + R(15) * air,
				math.sin(t * (1.6 + walk * 3) - 1.0) * R(14) * (1 + walk * 0.5), 0)
		end
		if joints.Crest then
			pose.Crest = CFrame.Angles(math.noise(t * 3, 2.7) * R(10) - R(8) * walk - R(20) * air,
				math.noise(t * 2.5, 5.3) * R(8), 0)
		end
		if joints.Halo then
			pose.Halo = CFrame.Angles(0, 0, t * 0.9)
		end
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
