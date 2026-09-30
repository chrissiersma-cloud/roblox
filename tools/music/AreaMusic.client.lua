-- AreaMusic: plays the music of the area the player is in, and crossfades when they walk into another area.
--
-- Put this LocalScript in StarterPlayer > StarterPlayerScripts. It needs:
--   * Sounds inside this script, one per area (Forest, DarkWoods). Paste your audio ID in each SoundId.
--   * workspace.MusicZones: parts that cover the areas. A part's Name says which Sound plays there
--     ("Forest" or "DarkWoods"). You can use several parts with the same name for one area.
-- Standing in no zone? Then the Sound named in the attribute DefaultArea plays (empty = silence).

local Players = game:GetService("Players")
local SoundService = game:GetService("SoundService")
local TweenService = game:GetService("TweenService")

local FADE = 2.5 -- seconds of crossfade
local RESTART_AFTER = 60 -- a track that was silent this long starts again from the beginning

local player = Players.LocalPlayer
local zones = workspace:WaitForChild("MusicZones")

local sounds: { [string]: Sound } = {}
local volumes: { [string]: number } = {}
local stoppedAt: { [string]: number } = {}
for _, child in script:GetChildren() do
	if child:IsA("Sound") then
		sounds[child.Name] = child
		volumes[child.Name] = child.Volume
		child.Looped = true
		child.Volume = 0
		child.Parent = SoundService
	end
end

-- The zones are only for this script: hide them.
local function hide(part: Instance)
	if part:IsA("BasePart") then
		part.Transparency = 1
	end
end
for _, part in zones:GetDescendants() do
	hide(part)
end
zones.DescendantAdded:Connect(hide)

local function areaAt(position: Vector3): string?
	for _, zone in zones:GetDescendants() do
		if zone:IsA("BasePart") and sounds[zone.Name] then
			local p = zone.CFrame:PointToObjectSpace(position)
			local half = zone.Size / 2
			if math.abs(p.X) <= half.X and math.abs(p.Y) <= half.Y and math.abs(p.Z) <= half.Z then
				return zone.Name
			end
		end
	end
	local default = script:GetAttribute("DefaultArea")
	if typeof(default) == "string" and sounds[default] then
		return default
	end
	return nil
end

local current: string? = nil
local tweens: { [string]: Tween } = {}

local function fadeTo(name: string, volume: number)
	local sound = sounds[name]
	if tweens[name] then
		tweens[name]:Cancel()
	end
	if volume > 0 and not sound.IsPlaying then
		if os.clock() - (stoppedAt[name] or -math.huge) > RESTART_AFTER then
			sound.TimePosition = 0
		end
		sound:Resume()
	end
	local tween = TweenService:Create(sound, TweenInfo.new(FADE, Enum.EasingStyle.Sine), { Volume = volume })
	tweens[name] = tween
	tween.Completed:Connect(function(state)
		if state == Enum.PlaybackState.Completed and volume == 0 then
			sound:Pause()
			stoppedAt[name] = os.clock()
		end
	end)
	tween:Play()
end

while true do
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		local area = areaAt(root.Position)
		if area ~= current then
			for name in sounds do
				fadeTo(name, if name == area then volumes[name] else 0)
			end
			current = area
		end
	end
	task.wait(0.25)
end
