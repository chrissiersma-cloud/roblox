# Frost Peak – het ronde bergengebied

`FrostPeakArea.rbxm` is het complete nieuwe gebied: één groot rond dal (bijna 700 studs breed) met in het midden de
berg van je referentieplaatje. Het is gebouwd met de Frost Peak-decorset, in dezelfde gladde low-poly stijl als
Critter Woods en Dark Woods.

![De berg vanaf de ingang](../../previews/frost_peak_area_image.png)
![Het hele gebied](../../previews/frost_peak_area_overview.png)
![De watervallen](../../previews/frost_peak_area_falls.png)
![Het pad langs de kliffen](../../previews/frost_peak_area_path.png)
![De grot](../../previews/frost_peak_area_cave.png)
![Van bovenaf](../../previews/frost_peak_area_top.png)

## Hoe het in elkaar zit

Van buiten naar binnen:

- **De rand**: een ring van hoge kliffen met sneeuw rondom het hele gebied. De ingang is een stenen boog (bij de
  `EntranceSpawn`), met een wegwijzer en lantaarns.
- **Het dal**: een ringpad met hekjes en lantaarns, een dennenbos, rotsen, sneeuwhopen, een bevroren meer en een
  kampvuur. Twee beekjes lopen naar de rand en eindigen in watervallen. Ze hebben touwbruggen.
- **De rivier**: een turquoise ring om de berg heen, met ijsschotsen, mist en drie touwbruggen.
- **De berg**: vijf ringen van blauwgrijze rotszuilen met sneeuw erop. De randen golven, zodat het geen taart wordt.
  - Op elke ring staan dennen.
  - Er vallen ruim 30 brede watervallen naar beneden, met een beekje erboven en een plas met ijs eronder.
  - Houten trappen gaan langs de kliffen omhoog naar paden met hekjes en lantaarns, en op de derde ring naar de grot.
  - Bovenop staat de besneeuwde top.

## In Studio zetten

1. Sleep `FrostPeakArea.rbxm` in Studio. Er komt één Model `FrostPeakArea` in Workspace.
2. Verplaats het met `PivotTo` naar een lege plek. Het draaipunt ligt in het midden, op de grond.
3. Spelers komen binnen bij het Part `EntranceSpawn`. Zet je teleport daarheen.
4. Je dieren en spawnpunten kun je kwijt op de ringen van de berg en in het dal. De berg is stoer genoeg voor de
   mythic dieren bovenop.

De mappen in het model zijn `Ground`, `Mountain`, `Rim`, `Water`, `Paths`, `Trees` en `Decor`.

## Telefoons

- Het gebied telt ongeveer 33.700 parts. Dat is veel, dus **zet `Workspace.StreamingEnabled` aan**. Dan laadt een
  telefoon alleen wat in de buurt is.
- Bomen en kliffen hebben `LevelOfDetail = StreamingMesh`, zodat ze ver weg als simpele vorm getekend worden.
- Alleen grote stukken hebben botsing (CanCollide). Kleine details zoals sneeuw, scheuren en ijspegels hebben geen
  botsing en geen schaduw.
- Water is half doorzichtig plastic, geen Glass.

Wil je het lichter maken? Haal dan wat dennen uit `Trees` of `Decor` weg. Daar zitten de meeste parts.

## Opnieuw bouwen

```
python3 tools/frost-peak-kit/build_frost_area.py --rbxm models/frost-peak-area/FrostPeakArea.rbxm
```

Alles staat bovenaan `tools/frost-peak-kit/build_frost_area.py`, dus het is makkelijk aan te passen:

- `TIERS`: grootte en hoogte van de ringen.
- `EXTRA_FALLS`: de watervallen.
- `STAIRS`: de trappen.
- `RIM`: de grootte van het dal.
