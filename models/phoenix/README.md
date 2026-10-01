# Phoenix – vernieuwd

`Phoenix.rbxm` is de nieuwe Phoenix (Mythic), opnieuw gebouwd van gewone Parts in dezelfde stijl als de andere
dieren: 617 parts, ongeveer 23 studs hoog met zijn vleugels omhoog. Het `AnimalId` is `Phoenix`, dus hij kan de
oude Phoenix vervangen.

![De Phoenix](../../previews/phoenix_hero.png)
![Van drie kanten](../../previews/phoenix.png)

(De plaatjes laten geen deeltjes zien. In het spel komen daar het vuur, de vonken en de sporen bij.)

## Wat erin zit

- **Lijf:** karmijnrood, met rijen borstschubben die van oranje naar witheet lopen. Er zitten lagen veren op de
  rug en flanken, en een rok van vlammen over de poten.
- **Kop:**
  - Een gouden haaksnavel, gloeiende ogen onder boze gloeiende wenkbrauwen en wangveren die naar achter wijzen.
  - Een kam van zeven vlammenpluimen.
  - Een zonnekrans achter de kop en een kraag van vlammenveren om de nek.
- **Vleugels:** twee grote vleugels met lagen veren. Uit elke slagpen likt een vlammentong.
- **Staart:** zeven lange pluimen met veren aan beide kanten. Ze zwaaien naar achter en omhoog en eindigen elk in
  een gloeiend vlammenoog.
- **Poten:** goud met schubben, vlammende enkelbanden en zwarte klauwen.
- **Om hem heen:** acht gloeiende veren die rondjes vliegen en een ring van vuur op de grond.

## Effecten

- **Vuur:** echt vuur (ParticleEmitters) op de kam, de vleugels, de staart, de enkels en de ring op de grond.
  Er komen ook vlammen van zijn rug.
- **Vonken en hitte:** vonken die omhoog zweven, wat hittewaas en vonken die van de vleugels vallen.
- **Licht:** vuurlicht dat pulseert. De ogen, wenkbrauwen en het staartoog pulseren mee.
- **Sporen en beams:** vuursporen achter de vleugelpunten, de staart en de rondvliegende veren. Twee spiralen
  van vuur (beams) draaien omhoog vanaf de vleugels.
- **Lopen:** het `AnimalFX`-script laat hem lopen als een vogel. Bij elke stap komen er vlammen, vonken en een
  ring van vuur. De vleugels klapperen zacht en de staart zwaait.
- **Idle-actie "rebirth" (nieuw):**
  1. Hij slaat zijn vleugels om zich heen en duikt in elkaar.
  2. Hij gloeit steeds heter en trilt.
  3. Hij barst open in een storm van vuur, met een felle flits, vuurringen die omhoog gaan, grote ringen op de
     grond en een wolk as.

  Soms doet hij in plaats daarvan "wingspread".

## Instellingen (attributen op het Model)

| Attribuut | Standaard | Wat het doet |
|---|---|---|
| `WalkSpeed` | 7 | hoe snel hij loopt |
| `FlapSpeed` | 1,3 | hoe snel de vleugels zacht klapperen |
| `FlapAngle` | 9 | hoe ver ze klapperen (graden) |
| `OrbitSpeed` | 0,7 | hoe snel de vuurveren rond draaien |
| `TailSway` | 9 | hoe ver de staart zwaait |

## Opnieuw bouwen

```
cd tools/animal-models
python3 build_phoenix.py --rbxm ../../models/phoenix/Phoenix.rbxm
```

Het model staat in `tools/animal-models/phoenix.py`, de animatie in `AnimalFX.lua` (profiel `Phoenix` en de actie
`rebirth`). Omdat `AnimalFX.lua` in alle dieren zit, zijn de andere `.rbxm`-bestanden (Dark Woods, paarden,
Thunder Unicorn, bergdieren) ook opnieuw gebouwd.
