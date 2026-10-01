# Mountain Range – concept art

Het volgende gebied na de Dark Woods: een bergketen die je beklimt, zone voor zone. Het is ongeveer **240 × 760
studs** en gaat **120 studs omhoog**, dus ongeveer **4 keer zo groot als de Dark Woods**. De scènes zijn gemaakt in
dezelfde stijl als de eerste concept art van het bos: blokjes met noppen en de HUD erop, zodat het lijkt op een
screenshot uit de game. Het is alleen art: er zijn geen Roblox-modellen gemaakt. De dieren in de scènes zijn snelle
voorbeelden; de echte ontwerpen staan op de dierenkaarten.

## De vijf zones

Elke zone ligt hoger dan de vorige. Je komt erin via een helling met een **speed gate** bovenaan. Een gondel gaat
van de voet van de berg naar de top.

| Zone | Hoe het eruitziet | Speed (voorstel) | Dieren |
|---|---|---|---|
| **Pine Foothills** | groene heuvels, dennen, de ingangspoort "MOUNTAIN RANGE", een basiskamp met tentjes en een kampvuur | – | Pebble Marmot, Pika Puff, Cliff Kid |
| **Canyon Pass** | een rode rotskloof met een rivier, een touwbrug, een waterval en grotten vol paarse kristallen | 25K | Bighorn Ram, Alpine Ibex, Peak Eagle, Geode Tortoise |
| **Alpine Lakes** | turquoise bergmeren, sneeuwplekken, besneeuwde dennen, een bamboebos en het gondelstation | 60K | Snowshoe Hare, Red Panda, Mountain Yak |
| **Frost Ridge** | sneeuw, ijskristallen en een sneeuwstorm die je trager maakt | 120K | Snow Leopard, Frostfang Wolf, Little Yeti, Glacier Mammoth |
| **The Summit** | de top bij nacht onder het noorderlicht, een cirkel van runenstenen en het nest van de griffioen | 250K | Sky Griffin, Aurora Dragon |

## De plaatjes

| Plaatje | Wat je ziet |
|---|---|
| `1-overzicht.png` | Het hele gebied van bovenaf: de vijf zones die steeds hoger liggen, de hellingen met speed gates, de gondel en de bergen eromheen. |
| `2-ingang-pine-foothills.png` | De ingangspoort "MOUNTAIN RANGE", met dennen, het basiskamp en de eerste dieren. |
| `3-canyon-pass-lasso.png` | Een speler gooit zijn lasso naar een Bighorn Ram in de kloof, met de rivier, de grot met de Geode Tortoise en de Peak Eagle hoog in de lucht. |
| `4-alpine-lakes.png` | Het grote bergmeer, de yaks, de Snowshoe Hare en de Red Panda in het bamboebos. |
| `5-frost-ridge.png` | De sneeuwstorm, met ijskristallen, een roedel Frostfang Wolves, de Snow Leopard, de Little Yeti en de Glacier Mammoth. "BLIZZARD! -20% SPEED" |
| `6-the-summit-secret.png` | De top bij nacht: de Aurora Dragon kronkelt door het noorderlicht, de Sky Griffin staat bij zijn nest. "A SECRET ANIMAL APPEARED!" |

## De 16 dieren

`alle-dieren.png` laat ze alle 16 zien. In de map `dieren/` heeft elk dier een eigen kaart met de naam, de
zeldzaamheid, de zone, een beschrijving en welke effecten het in de game zou moeten hebben.

| Zeldzaamheid | Dieren |
|---|---|
| Common | Pebble Marmot, Pika Puff, Cliff Kid, Snowshoe Hare |
| Rare | Bighorn Ram, Alpine Ibex, Red Panda |
| Epic | Peak Eagle, Mountain Yak, Geode Tortoise |
| Legendary | Snow Leopard, Frostfang Wolf, Little Yeti |
| Mythic | Sky Griffin, Glacier Mammoth |
| Secret | Aurora Dragon |

Ze zijn getekend in de stijl van je game (blokjes met noppen, grote glanzende ogen), zodat ze makkelijk als model
te bouwen zijn als je ze goedkeurt.

## Opnieuw maken

```
python3 tools/concept-art/mountain_animals.py   # de dierenkaarten en alle-dieren.png
python3 tools/concept-art/mountain_scenes.py    # de zes scènes (start eerst in tools/viewer: python3 -m http.server 8123)
```
