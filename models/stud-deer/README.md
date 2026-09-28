# Create a Zoo – hert met noppen (low-poly)

Een nieuw hert, helemaal in Blender gemaakt, in low-poly stijl en met de klassieke Roblox-noppen in de textuur.

![Hert met noppen: schuin, zijkant, voorkant, bovenkant, dichtbij en Golden](../../previews/stud_deer_views.png)

| | |
|---|---|
| Driehoekjes | 1.028 (Body 532, elke poot 124) |
| Hoogte | 6 studs met gewei (een Roblox-speler is ongeveer 5 studs) |
| Onderdelen | `Body` (met kop, oren, gewei en staart), `LegFL`, `LegFR`, `LegBL`, `LegBR` |
| Textuur | één materiaal, één plaatje van 1024 × 1024 |
| Richting | kijkt naar -Y in Blender (je ziet zijn gezicht in de Front view); 1 Blender-eenheid = 1 stud |

## De bestanden

| Bestand | Wat het is |
|---|---|
| `Deer.blend` | Het Blender-bestand. De textuur zit erin verpakt. |
| `Deer.glb` | Het hert voor Roblox Studio (File → Import 3D). |
| `DeerStuds.png` | De textuur: vlakke kleuren met noppen. |
| `DeerStuds_Golden.png` | Dezelfde textuur in goudkleuren, voor de mutatie "Golden". |
| `SetupZooAnimals.lua` | Script voor de Command Bar in Studio: maakt de gewrichten (Motor6D) voor de poten. |
| `texture_bands.json` | In welke rijen pixels van de textuur elke kleur staat. |

Het Python-script dat alles maakt staat in `tools/blender/stud_deer.py`.

## Hoe het gemaakt is

- **Low-poly:** elk onderdeel is een rij platte "ringen" (rechthoeken met schuine hoeken) die met grote, platte
  vlakken verbonden zijn. Elk vlak is precies plat en krijgt één kleur, zonder verloop. Het hert is vlak belicht:
  je ziet de hoekjes.
- **De noppen zitten in de textuur, niet in de 3D-vorm.** Echte 3D-noppen zouden duizenden driehoekjes extra kosten.
  De ingebouwde noppen van Roblox werken ook niet: die bestaan alleen op gewone Parts, niet op MeshParts.
- **Alle noppen zijn even groot en nergens uitgerekt.** Elk vlak krijgt een eigen plekje in de textuur, en alle
  vlakken staan daar op dezelfde schaal (82 pixels per stud). Het script controleert dat: de verhouding tussen een
  rand in 3D en in de textuur is overal precies 1.
- **De noppen lopen netjes door.** De noppen staan in een raster in het midden van elk vlak en de rijen lopen
  waterpas. Vlakken van dezelfde ring zijn even hoog, dus de rijen liggen rondom een poot of het lijf op gelijke
  hoogte. De rechterkant is het spiegelbeeld van de linkerkant. Smalle schuine randjes hebben geen noppen, zodat
  je geen halve noppen krijgt.
- **Noppengrootte:** de noppen zijn half zo groot als op een gewoon Roblox-blok (om de 0,5 stud). Ik heb ook de
  volle grootte geprobeerd, maar de poten zijn maar ongeveer 0,5 stud breed. Daar paste dan geen enkele hele nop op.
- **Elke kleur heeft een eigen band in de textuur** (rijen pixels van boven naar beneden):

  | Kleur | Rijen |
  |---|---|
  | bruin (lijf) | 0 – 525 |
  | crème (buik, borst, keel, kin, binnenkant oren) | 525 – 749 |
  | wit (onder de staart) | 749 – 781 |
  | lichtbruin (gewei) | 781 – 845 |
  | donkerbruin (hoeven, met noppen) | 845 – 952 |
  | donkerbruin (neus, zonder noppen) | 952 – 973 |
  | zwart (ogen, zonder noppen) | 973 – 1001 |
  | wit (lichtpuntje in de ogen) | 1001 – 1014 |

## In Roblox Studio zetten (3 stappen)

1. **Importeren:** kies **File** → **Import 3D**, kies `Deer.glb` en klik op **Import**. Studio uploadt de mesh
   en de textuur naar jouw account, en het hert verschijnt in de Workspace.
2. **Afmaken met het script:** open **View** → **Command Bar**, plak de hele inhoud van `SetupZooAnimals.lua`
   erin en druk op Enter. In het Output-venster staat dan "Set up Deer". Het script:
   - voegt een onzichtbare **RootPart** toe (hitbox en `PrimaryPart`, met de pivot onder de hoeven);
   - maakt **Motor6D**-gewrichten bovenaan de 4 poten, zodat je ze kunt animeren;
   - zet het hert terug op 6 studs, als Studio het bij het importeren een andere grootte heeft gegeven;
   - zet het hert in **ReplicatedStorage → ZooAnimals**.
3. **Opslaan als .rbxm:** klik met de rechtermuisknop op **Deer** en kies **Save to File...**.

Let op: dit hert heet ook `Deer`, net als het oude hert in `models/forest-hq`. Het script vervangt dus een
`Deer` die al in ReplicatedStorage → ZooAnimals staat.

## Golden maken

- **Klaar plaatje:** upload `DeerStuds_Golden.png` in Studio, bijvoorbeeld via de Asset Manager. Zet daarna de
  **TextureID** van alle 5 MeshParts (`Body`, `LegFL`, `LegFR`, `LegBL`, `LegBR`) op dat plaatje.
- **Zelf een kleur maken:** kleur in een tekenprogramma een band uit de tabel hierboven anders. Gebruik
  "kleurtoon/verzadiging" (hue/saturation), dan blijven de lichtjes en schaduwen van de noppen goed. Of pas
  `GOLDEN` of `PALETTE` bovenin `tools/blender/stud_deer.py` aan en maak alles opnieuw.

## Opnieuw maken of aanpassen

```
pip install bpy numpy pillow scipy
python3 tools/blender/stud_deer.py
```

Dat maakt alle bestanden in deze map opnieuw, en ook `previews/stud_deer_views.png` (duurt ongeveer 2 minuten).
Bovenin het script staan de getallen die je makkelijk kunt veranderen:

- `STUD`: de afstand tussen de noppen (0,5 = half zo groot als op een Roblox-blok, 1,0 = even groot);
- `PALETTE` en `GOLDEN`: de kleuren;
- `FRONT_LEG` en `HIND_LEG`, en de ringen in `build_body()`: de vorm.
