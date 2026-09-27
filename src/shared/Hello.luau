-- Een ModuleScript in ReplicatedStorage.Shared.
-- Zowel de server als de client kunnen deze code gebruiken.

local Hello = {}

function Hello.greet(name: string): string
	return `Hallo, {name}!`
end

return Hello
