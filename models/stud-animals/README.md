# Create a Zoo – dieren met noppen (low-poly)

Drie dieren, helemaal in Blender gemaakt, in dezelfde low-poly stijl en met de klassieke Roblox-noppen in de
textuur. De noppen zijn bij alle dieren even groot, zodat ze bij elkaar en bij je map passen.

![Hert](../../previews/stud_deer_views.png)
![Wolf](../../previews/stud_wolf_views.png)
![Konijn](../../previews/stud_rabbit_views.png)

| Dier | Zeldzaamheid | Hoogte | Driehoekjes | Kleuren |
|---|---|---|---|---|
| Deer | Common | 6 studs (met gewei) | 1.028 | bruin, crème buik/borst, wit onder de staart, lichtbruin gewei, donkerbruine hoeven en neus |
| Wolf | Rare | 4,1 studs (tot de oorpunten) | 830 | grijs, donker zadel op de rug, lichte buik/borst/snuit/poten, donkere staartpunt, zwarte neus |
| Rabbit | Common | 3,3 studs (tot de oorpunten) | 584 | bruin, crème buik/borst/snuit, roze binnenkant oren en neus, wit staartje |

Een Roblox-speler is ongeveer 5 studs hoog. Bij alle dieren geldt:

- **Onderdelen:** `Body` (met kop, oren, gewei en staart) en de poten `LegFL`, `LegFR`, `LegBL`, `LegBR`
  (F = voor, B = achter, L = links, R = rechts). De oorsprong van elke poot zit bovenaan, waar hij draait.
  De oorsprong van `Body` ligt op de grond tussen de poten.
- **Richting:** het dier kijkt naar -Y in Blender (je ziet zijn gezicht in de Front view). 1 Blender-eenheid
  = 1 stud.
- **Textuur:** één materiaal met één plaatje van 1024 × 1024.

De wolf en het konijn hebben minder driehoekjes dan het hert. Ze zijn kleiner en hebben geen gewei, dus meer
vlakjes zou je niet zien. Een Roblox-MeshPart mag er tot 20.000 hebben, dus alle drie zijn erg licht.

## De bestanden

Voor elk dier (`Deer`, `Wolf`, `Rabbit`):

| Bestand | Wat het is |
|---|---|
| `<Dier>.blend` | Het Blender-bestand. De textuur zit erin verpakt. |
| `<Dier>.glb` | Het dier voor Roblox Studio (File → Import 3D). |
| `<Dier>Studs.png` | De textuur: vlakke kleuren met noppen. |
| `<Dier>Studs_Golden.png` | Dezelfde textuur in goudkleuren, voor de mutatie "Golden". |
| `<Dier>.rig.json` | De gegevens voor de gewrichten; daarmee wordt `SetupZooAnimals.lua` gemaakt. |

En voor alle dieren samen:

| Bestand | Wat het is |
|---|---|
| `SetupZooAnimals.lua` | Script voor de Command Bar in Studio. Het zet alle drie de dieren klaar. |
| `texture_bands.json` | In welke rijen pixels van elke textuur elke kleur staat. |

De Python-scripts staan in `tools/blender/`: `stud_deer.py`, `stud_wolf.py` en `stud_rabbit.py` beschrijven de
vorm en kleuren, en `stud_animal.py` doet de rest (noppen, textuur, export, plaatjes).

## Hoe het gemaakt is

- **Low-poly:** elk onderdeel is een rij platte "ringen" (rechthoeken met schuine hoeken) die met grote, platte
  vlakken verbonden zijn. Elk vlak is precies plat en krijgt één kleur, zonder verloop. De dieren zijn vlak
  belicht: je ziet de hoekjes.
- **De noppen zitten in de textuur, niet in de 3D-vorm.** Echte 3D-noppen zouden duizenden driehoekjes extra
  kosten. De ingebouwde noppen van Roblox werken ook niet: die bestaan alleen op gewone Parts, niet op MeshParts.
- **Alle noppen zijn even groot en nergens uitgerekt.** Elk vlak krijgt een eigen plekje in de textuur, en alle
  vlakken van een dier staan daar op dezelfde schaal. Het script controleert dat: de verhouding tussen een rand
  in 3D en in de textuur is overal precies 1.
- **De noppen lopen netjes door.** De noppen staan in een raster in het midden van elk vlak en de rijen lopen
  waterpas. Vlakken van dezelfde ring zijn even hoog, dus de rijen liggen rondom een poot of het lijf op gelijke
  hoogte. De rechterkant is het spiegelbeeld van de linkerkant. Smalle schuine randjes hebben geen noppen, zodat
  je geen halve noppen krijgt.
- **Noppengrootte:** de noppen zijn half zo groot als op een gewoon Roblox-blok (om de 0,5 stud). Met de volle
  grootte past er geen enkele hele nop op de poten, want die zijn maar ongeveer 0,5 stud breed.
- **Elke kleur heeft een eigen band in de textuur** (rijen pixels van boven naar beneden). Zwart = de ogen,
  "lichtpuntje" = het witte puntje in de ogen; de ogen en de neus hebben geen noppen.

  | Hert | Rijen | | Wolf | Rijen | | Konijn | Rijen |
  |---|---|---|---|---|---|---|---|
  | bruin | 0 – 525 | | grijs | 0 – 508 | | bruin | 0 – 624 |
  | crème | 525 – 749 | | licht | 508 – 816 | | crème | 624 – 811 |
  | wit (staart) | 749 – 781 | | donker (rug, oren, staartpunt) | 816 – 958 | | wit (staart) | 811 – 870 |
  | lichtbruin (gewei) | 781 – 845 | | neus | 958 – 980 | | roze (oren) | 870 – 941 |
  | donkerbruin (hoeven) | 845 – 952 | | zwart | 980 – 1010 | | neus | 941 – 966 |
  | neus | 952 – 973 | | lichtpuntje | 1010 – 1024 | | zwart | 966 – 1006 |
  | zwart | 973 – 1001 | | | | | lichtpuntje | 1006 – 1022 |
  | lichtpuntje | 1001 – 1014 | | | | | | |

## In Roblox Studio zetten (3 stappen)

1. **Importeren:** kies **File** → **Import 3D** en kies `Deer.glb`, `Wolf.glb` en `Rabbit.glb` (samen of één
   voor één). Klik op **Import**. Studio uploadt de meshes en de texturen naar jouw account, en de dieren
   verschijnen in de Workspace.
2. **Afmaken met het script:** open **View** → **Command Bar**, plak de hele inhoud van `SetupZooAnimals.lua`
   erin en druk op Enter. In het Output-venster staat dan per dier "Set up Deer" enzovoort. Het script:
   - voegt een onzichtbare **RootPart** toe (hitbox en `PrimaryPart`, met de pivot onder de poten);
   - maakt **Motor6D**-gewrichten bovenaan de 4 poten, zodat je ze kunt animeren;
   - zet elk dier terug op zijn eigen grootte, als Studio het bij het importeren anders heeft gemaakt;
   - zet de dieren in **ReplicatedStorage → ZooAnimals**.
3. **Opslaan als .rbxm:** klik met de rechtermuisknop op een dier en kies **Save to File...**.

Let op: deze dieren heten `Deer`, `Wolf` en `Rabbit`, net als de oudere versies in `models/forest` en
`models/forest-hq`. Het script vervangt dus een dier met dezelfde naam dat al in ReplicatedStorage → ZooAnimals
staat.

## Golden maken

- **Klaar plaatje:** upload `<Dier>Studs_Golden.png` in Studio, bijvoorbeeld via de Asset Manager. Zet daarna
  de **TextureID** van alle 5 MeshParts van dat dier (`Body`, `LegFL`, `LegFR`, `LegBL`, `LegBR`) op dat
  plaatje.
- **Zelf een kleur maken:** kleur in een tekenprogramma een band uit de tabel hierboven anders. Gebruik
  "kleurtoon/verzadiging" (hue/saturation), dan blijven de lichtjes en schaduwen van de noppen goed. Of pas
  `GOLDEN` of `PALETTE` bovenin het script van het dier aan en maak het opnieuw.

## Opnieuw maken of aanpassen

```
pip install bpy numpy pillow scipy
python3 tools/blender/stud_deer.py
python3 tools/blender/stud_wolf.py
python3 tools/blender/stud_rabbit.py
```

Elk script maakt de bestanden van zijn dier in deze map opnieuw, en ook `SetupZooAnimals.lua` en
`previews/stud_<dier>_views.png` (duurt ongeveer 2 minuten per dier). Wat je makkelijk kunt veranderen:

- bovenin elk dierscript: `PALETTE` en `GOLDEN` (de kleuren) en de tabellen `FRONT_LEG` en `HIND_LEG` (de poten);
  in `build_body()` staan de ringen van het lijf, de kop en de rest;
- bovenin `stud_animal.py`: `STUD`, de afstand tussen de noppen (0,5 = half zo groot als op een Roblox-blok,
  1,0 = even groot). Dat geldt voor alle dieren tegelijk, zodat ze bij elkaar passen.
