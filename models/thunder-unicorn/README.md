# Thunder Unicorn

Het exclusieve rijdier van de game pass, gebouwd als het pronkstuk van de game. Een storm-blauwe **gevleugelde
eenhoorn** met:

- **Twee grote energievleugels** met platina botten, gouden gewrichten en gloeiende veren. Ze slaan rustig als hij
  stilstaat en gaan **wijd open als hij galoppeert**.
- **Gloeiende bliksemaders** onder zijn vacht, met een stormrune op elke flank.
- **Platina en gouden harnas:** een borstplaat met een gloeiende stormsteen, nekplaten, een gezichtsplaat, wangplaten en
  beenbeschermers met edelstenen.
- **Een kristallen hoorn** met een gouden spiraal, drie zwevende runenringen en een **energiezuil** die uit de punt
  omhoog schiet.
- **Manen en staart van stormwolken en elektrische vlammen**, met bliksemschichten erin.
- **Een runencirkel op de grond** die onder hem ronddraait, met **geladen bollen en kristalscherven** die om hem heen
  zweven, verbonden door elektrische bogen (ook naar zijn hoorn).
- **Gloeiende hoeven** met platina hoefijzers, wolkjes en vlammetjes.

Alles is gemaakt van gewone Parts, dus je hoeft niets te uploaden.

![Thunder Unicorn](../../previews/thunder_unicorn.png)

(De deeltjes, vlammen, lichtsporen, bogen, de energiezuil en het licht zie je niet in deze plaatjes, alleen in
Roblox.)

## Animaties en effecten

Het script **AnimalFX** laat hem bewegen. Het kijkt hoe snel het model beweegt, dus je hoeft niets aan te zetten:

- **Stilstaan:** hij ademt, zijn vleugels slaan langzaam, zijn hoorn knettert, zijn manen vlammen en rommelen, en de
  runencirkel en de bollen draaien rond.
- **Lopen:** vonken, wolkjes en een schokgolf onder elke hoef.
- **Galopperen:** de vleugels gaan wijd open en slaan sneller, lichtsporen trekken achter zijn hoeven, staart en
  vleugelpunten aan, en **naast zijn hoeven slaat af en toe de bliksem in**.
- **Elke paar seconden stilstaan** doet hij een van twee acties:
  - **Thunder:** hij steigert en er slaat een bliksemschicht op zijn hoorn.
  - **Storm:** hij steigert met zijn vleugels gespreid, een enorme bliksemschicht raakt zijn hoorn, er slaan **zes
    bliksems in een kring om hem heen** in, en hij landt met drie schokgolven en een lichtflits.

## In je game zetten

1. Klik in de **Explorer** met de rechtermuisknop op **ServerStorage** (of **ReplicatedStorage**) en kies **Insert
   from File...** → `ThunderUnicorn.rbxm`. Je krijgt een map **Mounts** met het model **ThunderUnicorn**.
2. Het model werkt zoals je andere dieren:
   - **RootPart** is de hitbox en de PrimaryPart. Verplaats het hele model met `PivotTo`; de pivot zit op de grond.
   - **RideAttachment** (in RootPart) is de plek op het zadel waar de speler zit. Gebruik die in je rij-script.
   - **OverheadAttachment** is de plek boven zijn hoofd, voor een naamkaartje.
3. Gebruik het in je mount-script net als je paarden: zet je rij-code (Seat, AlignPosition, of wat je paarden
   gebruiken) op dit model in plaats van op een paard. **Stuur me een screenshot van een paard in de Explorer**, dan
   maak ik de eenhoorn precies zoals je paarden zijn opgebouwd.

## Attributen

| Attribuut | Waarde | Wat het doet |
|---|---|---|
| `Mount` | true | voor je scripts: dit is een rijdier |
| `SpeedMultiplier` | 5 | voor je mount-script: 5x snelheid |
| `WalkSpeed` | 16 | de snelheid (studs/s) van een gewone stap. Sneller = galop |
| `OrbitSpeed` | 0.5 | hoe snel de runencirkel, de bollen en de kristallen ronddraaien (0 = stil) |
| `FlapSpeed`, `FlapAngle` | 1.6, 9 | hoe snel en hoe ver de vleugels slaan als hij stilstaat |
| `State` | "" | "Idle", "Walk" of "Run" om een animatie te forceren |
| `IdleActions` | (aan) | zet op false: geen steigeren met bliksem |
| `FXDistance` | 160 | verder weg dan dit (studs) geen effecten |

## Gemaakt voor telefoons

Ongeveer 690 Parts en 10 bewegende delen: meer dan je andere dieren, want dit is het pronkstuk. Dat gaat prima
zolang er niet tientallen tegelijk rondlopen. Verder een flink aantal kleine ParticleEmitters, zeven lampjes
zonder schaduw en negen Trails.
Kleine onderdelen geven geen schaduw en botsen niet. Ver weg (buiten `FXDistance`) stopt hij met effecten, en nog
verder weg ook met animeren. De bliksems zijn maar een halve seconde te zien en worden daarna opgeruimd.

## Let op

Ik heb het bestand gemaakt met dezelfde rbxm-writer als je andere modellen, de previews gerenderd en het script
gecontroleerd met de Luau-checker. Roblox Studio zelf kan ik niet openen. Gaat er iets mis, kopieer dan de tekst uit
het Output-venster en stuur die op.

## Opnieuw maken

```
cd tools/animal-models
python3 build_mounts.py --rbxm ../../models/thunder-unicorn/ThunderUnicorn.rbxm
```

Het model staat in `tools/animal-models/thunder_unicorn.py`, de animaties in `AnimalFX.lua` (profiel
`ThunderUnicorn` en de acties `thunder` en `storm`).
