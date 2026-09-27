# Hunt an Animal – conceptfoto's

Deze foto's zijn 3D-renders van de Hub en de Hunting Grounds, gebouwd in dezelfde blokstijl met noppen als
de diermodellen. De dieren op de foto's zijn de echte modellen uit `models/HuntAnimalModels.rbxm`. De kaarten
zelf zijn een ontwerp: ze staan nog niet in je Roblox-place.

| Foto | Wat je ziet |
|---|---|
| `1-hub-overzicht.png` | De Hub van bovenaf: het plein met het camerabeeld en de Training Track, 8 dierentuinen in een ring (2 nog vrij), de Hunting Gate met de klok, de Shop, het Bounty Board, het Lucky Wheel, de leaderboards, de VIP-lounge en het Daily Quests-bord. |
| `2-hub-hunting-gate.png` | Spelers wachten bij de Hunting Gate. De grote klok laat "NEXT HUNT 2:34" zien, met de HUD van het spel. |
| `3-hub-dierentuin.png` | Een dierentuin van dichtbij: hokken met dieren, naambordjes met inkomen, zwevende "+$" en gouden collect-pads. |
| `4-hunting-grounds-overzicht.png` | De Hunting Grounds van bovenaf: Base Camp met de Exit Portal, de Sunny Meadow en daaromheen de Whispering Forest, Frostpeak, de Crystal Caverns, de Scorched Canyon en de zwevende Sky Isles. Lichtbundels in de kleur van de zeldzaamheid laten zien waar zeldzame dieren staan. |
| `5-whispering-forest.png` | Een speler met een camera sluipt naar een roedel van 3 wolven (Rare, blauwe bundels). |
| `6-scorched-canyon.png` | De canyon bij zonsondergang met de Sandsnapper, de Emberback Boar, de Thunderhoof en de Phoenix Fox. |
| `7-camera-zoeker-frostpeak.png` | Door de zoeker van de camera: een Frostfang Wolf in Frostpeak, met de richtring, de verwachte sterren, de capture-meter en de Photo Cards. |

Opnieuw maken: `python3 tools/concept-art/scenes.py` schrijft de scènes naar `tools/concept-art/build/`.
Kopieer die, samen met `tools/animal-models/build/animals.json`, naar `tools/viewer/`, doe daar `npm install`,
start een webserver (`python3 -m http.server 8123`) en render met
`node sceneshot.js hub.json overview uit.png`. Daarvoor is Playwright nodig.
