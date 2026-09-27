-- Een Script in ServerScriptService.Server (draait op de server).

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Hello = require(ReplicatedStorage.Shared.Hello)

print(Hello.greet("server"))
