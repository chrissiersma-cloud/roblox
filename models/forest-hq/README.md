# Create a Zoo – bosdieren, nieuwe hoge kwaliteit (werk in uitvoering)

Deze dieren worden gemaakt vanuit jouw referentieblad (`tools/blender/reference/forest_side_views.webp`):

1. De omtrek van elk dier wordt uit het zijaanzicht geknipt en opgedeeld in lijf, poten, oren en gewei.
2. Elk deel wordt in Blender 3D gemaakt in de hoekige low-poly stijl van je plaatjes: platte zijkanten, een
   platte rug en borst en schuin afgesneden randen. Van opzij heeft het model precies de vorm van de tekening;
   de breedte (van voren gezien) komt uit het voor- en achteraanzicht van het hert op het blad.
3. De tekening zelf wordt de textuur, zodat vlekken, ogen en schaduwen kloppen. Vlakken die naar voren of
   naar boven kijken (rug, borst, voorkant van de poten) krijgen een rustige versie zonder vlekken, net als
   op het schuine plaatje.

| Dier | Bestand | Driehoekjes | Onderdelen (MeshParts) |
|---|---|---|---|
| Deer | `Deer.glb` | ca. 10.700 | Body (met kop, oren, gewei, staart), LegFL, LegFR, LegBL, LegBR |

![Hert: referentie en 3D-model](../../previews/deer_hq.png)

Het setup-script (gewrichten, RootPart) is nog niet aangepast aan deze nieuwe dieren. Dat komt zodra alle
dieren goedgekeurd zijn. Je kunt `Deer.glb` al wel importeren via **Import 3D** om hem in Studio te bekijken.

Opnieuw maken: `pip install bpy scikit-image scipy pillow` en dan
`python3 tools/blender/deer.py tools/blender/reference/forest_side_views.webp <map>`.
