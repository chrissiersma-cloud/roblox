# Muziek – Forest en Dark Woods

Twee soundtracks voor je gebieden. Allebei zijn het **naadloze loops**: het einde loopt precies over in het
begin, dus met `Looped = true` hoor je geen gat of sprong.

| Bestand | Sfeer | Lengte |
|---|---|---|
| `Forest.ogg` | **Avontuur.** Een fluit met het hoofdthema, harp, pizzicato en galopperende strijkers, hoorns, taiko-trommels en vogeltjes. D groot, 112 BPM. | 1:43 |
| `DarkWoods.ogg` | **Donker avontuur in een grot.** Een speeldoos-melodie, een lage cello die blijft doorlopen, een spookachtig koor, hoorns, trommels als een hartslag, druppelend water en een enorme grot-echo. D klein, 88 BPM. | 1:49 |

De `.mp3`-bestanden zijn om te luisteren. Upload de **`.ogg`**-bestanden naar Roblox: die loopen zonder klikje.
Bij een mp3 zit er altijd een heel klein stilte-stukje aan het begin.

Beide nummers zijn even hard gemaakt (-15 LUFS). Als je van het ene gebied naar het andere loopt, wordt de muziek
dus niet ineens harder of zachter.

## Uploaden

1. Ga naar **create.roblox.com → Creations → Development Items → Audio** en klik op **Upload Asset**. Of in
   Studio: **View → Asset Manager → Bulk Import**.
2. Kies `Forest.ogg`, en daarna `DarkWoods.ogg`.
3. Kopieer het ID van elk geluid (het getal in de link).

Is je game van een **groep**? Upload de audio dan bij die groep, anders mag de game het niet afspelen.

## Afspelen per gebied met AreaMusic

`AreaMusic.rbxm` speelt vanzelf de goede muziek af in elk gebied, en laat de muziek zacht overvloeien als je
een ander gebied in loopt.

1. Klik in de Explorer met de rechtermuisknop op **Workspace** → **Insert from File...** → `AreaMusic.rbxm`.
2. Je krijgt twee dingen:
   - **AreaMusic** (een LocalScript). Sleep het naar **StarterPlayer → StarterPlayerScripts**.
   - **MusicZones** (een model met twee doorzichtige blokken, `Forest` en `DarkWoods`). Laat dit in de Workspace.
3. Open AreaMusic, klik op het Sound **Forest** en zet bij **SoundId** `rbxassetid://` + je ID, bijvoorbeeld
   `rbxassetid://1234567890`. Doe hetzelfde bij **DarkWoods**.
4. Verplaats en vergroot het blok **Forest** zodat het het hele bos bedekt, en het blok **DarkWoods** zodat
   het de Dark Woods bedekt. Is een gebied een rare vorm? Zet dan meer blokken in MusicZones met dezelfde naam.
   Tijdens het spelen worden de blokken onzichtbaar.

Handig om te weten:

- Buiten alle blokken (bijvoorbeeld in de hub) is het stil. Wil je daar toch een nummer, zet dan bij AreaMusic
  het attribuut **DefaultArea** op `Forest` of `DarkWoods`. Is het bos een aparte place? Dan heb je geen blokken
  nodig: zet DefaultArea op `Forest`.
- Te hard of te zacht? Verander de **Volume** van het Sound (0.5 is standaard).
- Ben je langer dan een minuut weg uit een gebied, dan begint de muziek daar weer bij het begin.
- MusicZones staat op `ModelStreamingMode = Persistent`, zodat het ook werkt als StreamingEnabled aan staat.

## Opnieuw maken

De muziek is helemaal met code gemaakt (`tools/music/synth.py` zijn de instrumenten, `soundtracks.py` de
nummers), dus er zitten geen samples van anderen in.

```
pip install numpy scipy soundfile lameenc
python3 tools/music/soundtracks.py            # audio/Forest.ogg/.mp3 en audio/DarkWoods.ogg/.mp3
python3 tools/music/build_area_music.py       # audio/AreaMusic.rbxm
```
