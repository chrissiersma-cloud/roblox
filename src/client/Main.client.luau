-- Een LocalScript in StarterPlayerScripts.Client (draait bij elke speler).

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Hello = require(ReplicatedStorage.Shared.Hello)

print(Hello.greet(Players.LocalPlayer.Name))
