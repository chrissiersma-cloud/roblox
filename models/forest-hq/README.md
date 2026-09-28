# Create a Zoo – bosdieren, nieuwe low-poly versie

Deze dieren worden gemaakt vanuit jouw referentieblad (`tools/blender/reference/forest_side_views.webp`):

1. De omtrek van elk dier wordt uit het zijaanzicht geknipt en opgedeeld in lijf, poten, oren en gewei.
2. Elk deel wordt in Blender 3D gemaakt in de hoekige low-poly stijl van je plaatjes: platte zijkanten, een
   platte rug en borst en schuin afgesneden randen. Van opzij heeft het model precies de vorm van de tekening;
   de breedte (van voren gezien) komt uit het voor- en achteraanzicht van het hert op het blad.
3. Low-poly: de omtrek wordt eerst met rechte lijnen nagetekend, het model heeft weinig grote, vlakke
   vlakken (ongeveer 3.000 driehoekjes) en elk vlak wordt vlak belicht.
4. De kleuren komen uit de tekening, maar vlak gemaakt: de getekende lijntjes en schaduwstreepjes zijn weg en
   er blijven een paar egale kleuren over (bruin, crème, wit, de vlekken, het gewei). Het oog, de neus en de
   hoeven blijven zoals getekend. Rug, borst en voorkant van de poten zijn egaal, zonder vlekken.

| Dier | Bestand | Driehoekjes | Onderdelen (MeshParts) |
|---|---|---|---|
| Deer | `Deer.glb` | ca. 3.100 | Body (met kop, oren, gewei, staart), LegFL, LegFR, LegBL, LegBR |

![Hert: referentie en 3D-model](../../previews/deer_hq.png)

![Hert: andere kanten](../../previews/deer_hq_views.png)

## In Roblox Studio zetten en als .rbxm opslaan (3 stappen)

1. **Importeren:** ga naar **File** → **Import 3D** (of het tabblad **Avatar** → **Import 3D**), kies `Deer.glb`
   en klik op **Import**. Laat de instellingen zoals ze zijn. Studio uploadt nu de mesh en de textuur naar jouw
   Roblox-account. Het hert verschijnt in de Workspace.
2. **Afmaken met het script:** open **View** → **Command Bar**, plak de hele inhoud van `SetupZooAnimals.lua`
   erin en druk op Enter. In het Output-venster staat "Set up Deer". Het hert staat nu in
   **ReplicatedStorage → ZooAnimals** en is geselecteerd. Het script heeft toegevoegd:
   - een onzichtbare **RootPart** (hitbox en `PrimaryPart`; de pivot zit onder de hoeven),
   - **Motor6D**-gewrichten voor de 4 poten (`LegFL`, `LegFR`, `LegBL`, `LegBR`), zodat je ze kunt animeren,
   - een **OverheadAttachment** boven de kop voor een naambordje,
   - de attributen `AnimalId`, `DisplayName` en `Rarity` en de tag `ZooAnimal`.
3. **Opslaan als .rbxm:** klik in de Explorer met de rechtermuisknop op **Deer** en kies **Save to File...**.
   Dan heb je `Deer.rbxm`, dat je in al je andere places kunt slepen.

**Waarom ik de .rbxm niet zelf kan maken:** een .rbxm bevat de 3D-vorm niet zelf. Er staat alleen een link in
(`MeshId` en `TextureID`, zoals `rbxassetid://123…`) naar de mesh en de textuur op de servers van Roblox. Die
moeten eerst met jouw Roblox-account geüpload worden, en dat doet Studio bij stap 1.

Gaat er iets mis? Kopieer de tekst uit het Output-venster en stuur die op.

Opnieuw maken: `pip install bpy scikit-image scipy pillow` en dan
`python3 tools/blender/deer.py tools/blender/reference/forest_side_views.webp <map>`. Dat schrijft `Deer.glb`,
`Deer.rig.json` (de gewrichten) en `SetupZooAnimals.lua` in die map.
