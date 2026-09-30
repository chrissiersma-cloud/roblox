# Create a Zoo – conceptfoto's

Deze foto's zijn 3D-renders in dezelfde blokstijl met noppen als de diermodellen. De dieren op de foto's zijn
de echte modellen uit `models/HuntAnimalModels.rbxm`. De kaart zelf is een ontwerp: die staat nog niet in je
Roblox-place.

## De spelloop (zoals Steal an Egg, maar met een lasso)

1. **Train je snelheid** op de loopband voor je dierentuin.
2. **Ga de wildernis in.** Die bestaat uit biomen op een rij. Hoe verder weg, hoe meer snelheid je nodig hebt,
   en elke biome wordt bewaakt door een reusachtige bewaker.
3. **Gooi je lasso** om een wild dier.
4. **Ren terug naar je dierentuin.** Met een dier aan je lasso ben je langzamer. Als de bewaker je inhaalt,
   ben je het dier kwijt, en andere spelers kunnen het van je afpakken met een knuppel of een berenval.
5. **Zet het dier in een hok en tem het.** Pas dan zie je zijn mutatie (bijvoorbeeld Golden). Daarna verdient
   het geld per seconde.
6. **Koop upgrades** en word sneller, zodat je in verdere biomen zeldzamere dieren kunt vangen.
7. **Elke 5 minuten** komen alle wilde dieren opnieuw tevoorschijn.

## De foto's

| Foto | Wat je ziet |
|---|---|
| `1-lobby-overzicht.png` | De lobby: een laan met aan beide kanten 4 dierentuinen, met een loopband voor elke dierentuin. Bij de spawn staan de boog "Create a Zoo!", de Lasso Shop en de Gear Shop. Aan het eind van de laan staat de boog "To the Wild" met de klok "Animals respawn in 2:34". |
| `2-jouw-dierentuin.png` | Jouw dierentuin: hokken met dieren, bordjes met het inkomen per seconde, een Golden Thunderhoof, het bordje "Zoo lvl" en een speler die op de loopband traint (+1 speed). |
| `3-de-wildernis-overzicht.png` | De wildernis van bovenaf: Sunny Meadow, Whispering Forest, Scorched Desert, Frostpeak, Volcano, Crystal Caverns en Sky Isles. Tussen de biomen staan speed-poorten, en in elke biome staat een reuzenbewaker met een rode zone om zich heen. |
| `4-lasso-gooien.png` | In de woestijn gooit een speler zijn lasso naar een Thunderhoof (Legendary), terwijl de reuzen-Sandsnapper toekijkt. Op een bordje staat "10K recommended". |
| `5-terugrennen-met-dier.png` | Een speler rent terug met een wolf aan zijn lasso. De reuzenbeer zit hem achterna, een andere speler staat klaar met een knuppel en op de grond ligt een berenval. |
| `6-speed-poort.png` | De poort naar Frostpeak: "40K speed recommended". Je bent te langzaam, dus eerst trainen. |
| `7-dier-getemd.png` | Een dier is getemd in je dierentuin: "Golden Thunderhoof · Legendary · $5,000/s". |

## Dark Woods

Het donkere bos, met de 12 dieren uit `models/dark-woods/DarkWoodsAnimals.rbxm` en de bomen, varens, rotsen en
gloeiende paddenstoelen uit `models/forest-kit/CritterWoodsKit.rbxm`. Het is avond: maanlicht, paarse lucht, mist en
overal gloeiende dingen. Hoe verder je het bos in gaat, hoe zeldzamer de dieren.

| Foto | Wat je ziet |
|---|---|
| `8-dark-woods-overzicht.png` | Het hele gebied van bovenaf: de boog "Dark Woods", een kronkelpad met gloeiende paddenstoelen door de **Deep Woods**, en helemaal achterin **The Heart**: een open plek met een maanstraal, een vijver en de Ancient Tree. |
| `9-dark-woods-ingang.png` | De ingang vanaf het pad: de boog van donkere boomstammen met het bord "Dark Woods · Deep Woods & The Heart" en lantaarns. Achter de boog zie je de Mossback Toad en de Shroom Snail (Common). |
| `10-dark-woods-lasso.png` | Diep in het bos gooit een speler zijn lasso om een Umbra Panther (Mythic), met de schaduwcirkel om hem heen. |
| `11-dark-woods-het-hart.png` | The Heart: de Nightshade Drake (Secret) zweeft in de maanstraal boven de vijver, de Mossking Elk (Mythic) staat bij de heksenkring en de Ancient Tree staat erachter. "A SECRET ANIMAL APPEARED!" |

Waar de dieren staan, van de ingang naar achteren: Mossback Toad en Shroom Snail (Common), Night Hedgehog en
Duskbat (Uncommon), Hollow Badger en Glowmoth (Rare), Barkling (Epic), Wisp Lynx en Moonraven (Legendary),
Umbra Panther (Mythic), en in The Heart de Mossking Elk (Mythic) en de Nightshade Drake (Secret).

Opnieuw maken: `python3 tools/concept-art/dark_woods_scenes.py` schrijft `tools/concept-art/build/dark_woods_world.json`
en `tools/animal-models/build/dark_woods.json`. Kopieer die twee naar `tools/viewer/` en render met
`node sceneshot.js dark_woods_world.json overview uit.png` (of: path, lasso, heart).

Opnieuw maken: `python3 tools/concept-art/scenes.py` schrijft de wereld naar `tools/concept-art/build/world.json`.
Kopieer dat bestand, samen met `tools/animal-models/build/animals.json`, naar `tools/viewer/`, doe daar
`npm install`, start een webserver (`python3 -m http.server 8123`) en render met
`node sceneshot.js world.json lobby uit.png` (of: zoo, wild, lasso, escape, gate, tame). Daarvoor is Playwright nodig.
