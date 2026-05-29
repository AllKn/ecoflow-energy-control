# EEC app

Lokale Home Assistant-integratie voor EcoFlow opslag, PowerStream-sturing, EnergyZero/spotprijzen, HomeWizard-opwekmeting en eenvoudige diagnose per toegevoegd apparaat.

## Kernfuncties

- EcoFlow apparaten ophalen via de EcoFlow Cloud API device-list.
- Gevonden EcoFlow apparaten importeren en daarna zelf typeren als Delta Pro, Delta Pro 3, PowerStream of Smart Plug.
- Per toegevoegd EcoFlow apparaat een API-statussensor:
  - API bereikbaar
  - telemetrie opgehaald of niet
  - laatste foutmelding
  - serienummer en type
  - aantal opgehaalde velden
- Batterijstatus per Delta:
  - SoC
  - laadvermogen
  - ontlaadvermogen
  - netto vermogen
  - status
- PowerStream-status per apparaat:
  - vermogen
  - status
  - fase
- EnergyZero prijzen als standaard prijsbron, inclusief instelbare Quatt-opslag van standaard `0.015 EUR/kWh`.
- Alternatieve prijsbronnen via epexprijzen.nl of epexspot.com blijven beschikbaar.
- Dagelijkse prijs-refresh om 15:00 voor planning tot en met einde volgende dag.
- HomeWizard lokale API voor ruwe opwek, met correctie voor PowerStream-teruglevering.

## Apparaten Beheren

Ga naar:

```text
Instellingen > Apparaten & diensten > EEC app > Configureren
```

Beschikbare acties:

- **EcoFlow apparaten importeren**: haalt apparaten op uit de EcoFlow API en laat je het type kiezen.
- **HomeWizard importeren**: gebruikt bestaande HomeWizard-apparaten uit Home Assistant als opwekbron.
- **Handmatig toevoegen**: alleen nodig als importeren niet lukt.
- **Apparaat wijzigen**: bestaande configuratie aanpassen.
- **Apparaat verwijderen**: apparaat uit deze integratie verwijderen.
- **Basisinstellingen**: prijsbron, Quatt-opslag, weerstad en testmodus.
- **Technische instellingen**: API keys, custom prijsdetails, SMA cloudvelden en technische endpoints.

Bij importeren kies je eerst het gevonden EcoFlow-serienummer en daarna het type. De app controleert de verbinding voordat het apparaat wordt opgeslagen. Alleen bij een Smart Plug wordt gevraagd welke batterij ermee geladen wordt. Dit veld wordt gevuld met de reeds toegevoegde batterij-devices.

## Diagnose

Gebruik in het dashboard:

```text
button.ecoflow_energy_control_applicatie_ecoflow_api_controleren
sensor.ecoflow_energy_control_applicatie_status
```

Daarnaast maakt de integratie per toegevoegd EcoFlow device een sensor aan met naam:

```text
<apparaatnaam> API status
```

Open de attributen van die sensor om te zien:

- `api_connected`
- `telemetry_fields`
- `telemetry_keys`
- `error`
- `serial`
- `device_type`

Als de EcoFlow API wel devices vindt maar telemetrie niet werkt, zie je hier precies welk apparaat faalt en welke fout de quota-uitlezing teruggeeft.

Voor testen buiten Home Assistant is er een losse lokale tool:

```text
tools/ecoflow_api_tester
```

Daarmee kun je device-list en quota-uitlezing rechtstreeks vanaf je eigen machine/netwerk testen.

## Prijzen

Standaard gebruikt de integratie EnergyZero:

```text
https://public.api.energyzero.nl/public/v1/prices
```

De integratie vraagt uurprijzen op voor vandaag en morgen met `energyType=ENERGY_TYPE_ELECTRICITY` en `interval=INTERVAL_HOUR`. De Quatt-opslag van `0.015 EUR/kWh` wordt daar apart bij opgeteld, zodat de opslag zichtbaar en aanpasbaar blijft.

Je kunt in Basisinstellingen terugschakelen naar epexprijzen.nl of epexspot.com. Een eigen prijs-URL blijft mogelijk via Technische instellingen; als die is ingevuld, gaat die voor op de gekozen bron.

Prijsdata wordt dagelijks om **15:00** opgehaald en is ook handmatig te verversen met de prijs-ophaalknop.

## Dashboard

Het primaire dashboard staat in:

```text
dashboards/ecoflow-energy-control.yaml
```

Gebruik dit dashboard als hoofdscherm. Het combineert de volledige flow: actuele status, accu-inhoud, PowerStream-sturing, strategieadvies, prijzen, netto opwek, weer en diagnose. De kaarten zoeken apparaten dynamisch op via EEC-attributen, zodat hardcoded device-namen zoals `Delta Pro` of `PowerStream 1` niet meer nodig zijn.

Voor live validatie na een update kijk je bovenaan naar:

- **Flow**: laat zien of de app klaar is, wat de volgende stap is en of het advies gestart kan worden.
- **Basis**: toont de kernmetingen waarop de keuze rust: netto W, prijs, accu, kWh, teruglevering en zonwaarde.
- **Scenario - nu**: toont het actuele beste scenario, de match met je keuze en de verwachte EUR/uur.
- **Gereedheid > Probleem**: toont de eerste blokkade of waarschuwing die aandacht nodig heeft.
- **Gereedheid > Bewijs**: scheidt databewijs van stuur-bewijs, bijvoorbeeld `6/6 data, sturing gedeeltelijk`.
- **Datacheck**: toont de details per bron als `Probleem` of `Bewijs` niet volledig klaar is.

Optionele detail- en testdashboards staan in:

```text
dashboards/ecoflow-energy-powerstreams.yaml
dashboards/ecoflow-energy-app-style.yaml
dashboards/ecoflow-energy-scenarios.yaml
```

Benodigde frontend-kaarten via HACS:

- `auto-entities`
- `apexcharts-card`

Zonder deze kaarten blijven de entiteiten werken, maar worden de dynamische lijsten of prijsgrafiek niet weergegeven.

## Huidige Versie

`0.5.167`

## EcoFlow Signing

Versie `0.5.1` corrigeert de EcoFlow signing voor quota-uitlezingen: `nonce` is nu een 6-cijferige waarde en `timestamp` is weer de actuele milliseconden-timestamp. Dat voorkomt `8521 signature is wrong` bij quota-routes terwijl device-list wel werkt.

Versie `0.5.2` corrigeert de volgorde van de sign-string: eerst de gesorteerde request-parameters, daarna pas `accessKey`, `nonce` en `timestamp`. Dit is vooral nodig voor quota-routes met `sn` en `params`.

Versie `0.5.3` bewaart toegevoegde devices voortaan in de hoofdconfiguratie in plaats van alleen in options. Dit voorkomt dat apparaten na een update/reload verdwijnen. De displaynaam is ingekort naar `EEC app`, en per-device statusentiteiten heten nu bijvoorbeeld `batterijstatus Delta Pro 3` of `PowerStream <naam>`.

Versie `0.5.4` voegt `epexspot.com` toe als alternatieve prijsbron. De Quatt-opslag van `0.015 EUR/kWh` blijft apart instelbaar en wordt op beide bronnen toegepast. Let op: de officiële realtime EPEX SPOT API is marktdata-abonnement; de publieke epexspot.com bron is een best-effort parser van de market-results pagina.

Versie `0.5.5` maakt EnergyZero de standaard prijsbron. De app haalt EnergyZero-prijzen rechtstreeks op, ondersteunt de bekende `prices`/`timestamp` responsvorm en blijft de Quatt-opslag apart tonen.

Versie `0.5.6` maakt het dashboard minder afhankelijk van entity_id-namen. Batterij- en PowerStream-sensoren krijgen nu eigen `eec_device_type` en `eec_sensor_role` attributen, zodat dynamische dashboardkaarten ook werken als apparaten een eigen naam hebben. De EcoFlow quota-parser accepteert nu ook lijstvormen zoals `{name, value}`.

Versie `0.5.7` forceert een integratie-reload na apparaat toevoegen, wijzigen of verwijderen, zodat Home Assistant de nieuwe entiteiten meteen aanmaakt. EcoFlow apparaten en HomeWizard meters krijgen nu ook eigen Home Assistant devices onder de integratie, met per-device status- en vermogenssensoren.

Versie `0.5.8` maakt het dashboard leesbaarder: batterijen staan in één gegroepeerd overzicht onder elkaar, het controlpanel gebruikt echte knoppen met korte labels, en zichtbare lange applicatienamen zijn ingekort naar `EEC app`.

Versie `0.5.9` verbetert PowerStream-telemetrie: als de geselecteerde quota's geen data opleveren, probeert de integratie automatisch `quota/all`. Geneste EcoFlow responsen worden nu recursief uitgepakt en PowerStream-sensoren tonen mogelijke vermogensvelden in de attributen.

Versie `0.5.10` toont de geladen app-versie op het dashboard, maakt de komende 24 uur stroomprijzen grafisch als staafdiagram en breidt HomeWizard-weergave uit met fasevermogen en import/export energie waar de lokale API die data levert.

Versie `0.5.11` kan HomeWizard-apparaten importeren uit de officiële Home Assistant HomeWizard-integratie. EEC app leest dan de bestaande Home Assistant-entiteiten in plaats van dezelfde meters direct opnieuw via de lokale API te pollen.

Versie `0.5.12` voegt een simulatie-laag toe voor scenario's: optimalisatie eigen gebruik, handelen en een 50%-buffer. De app rekent live geschatte besparing/winst in EUR per uur en cumulatief per dag/week/maand door en levert een apart scenario-dashboard in `dashboards/ecoflow-energy-scenarios.yaml`.

Versie `0.5.13` corrigeert de HomeWizard-import via Home Assistant wanneer die vanuit Apparaat toevoegen wordt gestart en logt inspectiefouten voor HomeWizard-apparaten duidelijker.

Versie `0.5.14` normaliseert PowerStream-vermogens die als deciwatt binnenkomen en breidt de batterij-SoC herkenning uit voor Delta Pro 3-velden zoals `ems.soc`, `bms.soc`, `socLevel` en geneste SoC-velden.

Versie `0.5.15` probeert voor batterijen automatisch `quota/all` als de geselecteerde quota's geen telemetrie opleveren. De per-device API-status toont nu `quota_source` en `response_debug` om te zien wat EcoFlow terugstuurt.

Versie `0.5.16` corrigeert Delta Pro 3 SoC-herkenning: `cmsBattSoc` krijgt prioriteit als hoofdaccu, `bmsBattSoc` wordt als extra accu-attribuut getoond en SoC-grenswaarden zoals `cmsMinDsgSoc` worden niet meer als actuele batterijstand gebruikt.

Versie `0.5.17` verbetert batterij-vermogensherkenning en toont `power_candidates` als diagnose-attribuut bij batterijvermogens. De PowerStream-dashboarddata herstelt een attribuutfout waardoor kaarten leeg konden blijven, en de prijsgrafieken negeren nu ongeldige `n/a` punten zodat ze niet op `loading` blijven hangen.

Versie `0.5.18` vraagt bij batterijen automatisch bredere EcoFlow-telemetrie op als de standaardvelden wel SoC maar geen live vermogen bevatten. Dit helpt vooral bij oudere Delta Pro-modellen die andere veldnamen gebruiken voor laad- en ontlaadvermogen.

Versie `0.5.19` maakt die Delta Pro fallback strenger: een enkel nulveld zoals `inv.inputWatts: 0` telt niet meer als volledige vermogensmeting. De app vraagt dan alsnog bredere batterijtelemetrie op.

Versie `0.5.20` splitst batterij-laadvermogen naar bron. De hoofdwaarde `laadvermogen` telt alleen nog AC- en zonne-input mee; DC/input vanuit een Extra Battery wordt apart zichtbaar via attributen zoals `dc_charge_w`, `unclassified_input_w` en `charge_source`. PowerStream-waarden die zonder ingestelde maximumwaarde als deciwatt binnenkomen, worden nu ook naar watt genormaliseerd.

Versie `0.5.21` gebruikt de actuele publieke EnergyZero API per dag (`public.api.energyzero.nl/public/v1/prices`) en haalt vandaag en morgen apart op. Daardoor worden de uurtarieven weer gevuld in plaats van `n/a/loading`.

Versie `0.5.22` maakt de prijsgrafiek robuuster door de grafiekdata ook op de laagste-prijs sensor te zetten. Daarnaast krijgen PowerStreams een eigen wattage-regelaar op het dashboard en kan per PowerStream in de configuratie worden ingesteld welke Delta Pro erbij hoort.

Versie `0.5.23` voegt een apart PowerStream-dashboard toe met per PowerStream + Delta Pro groep: accupercentage, beschikbare Wh, instelbaar terugleververmogen, strategie en adviesactie op basis van prijsdata en gecorrigeerde HomeWizard-zonopwek.

Versie `0.5.24` corrigeert het PowerStream command voor teruglevering: `operateType` wordt vervangen door `cmdCode` voor `WN511_SET_PERMANENT_WATTS_PACK`. Bestaande oude templates worden automatisch genormaliseerd en bij fout `1008` probeert de app een compacte fallback-commandvorm.

Versie `0.5.25` stuurt PowerStream `permanentWatts` standaard als deciwatt, dus 590 W wordt als `5900` verzonden. Mislukte echte commando's worden nu ook zichtbaar in `last_powerstream_command` en `last_powerstream_error`.

Versie `0.5.26` werkt PowerStream dashboardwaarden direct lokaal bij na slider-aanpassing en maakt de Accu/Wh gauges numeriek robuust. Voor Delta Pro + Extra Battery gebruikt de app 7200 Wh als fallbackcapaciteit; voor Delta Pro 3 + Extra Battery 8192 Wh.

Versie `0.5.27` laat PowerStream-groepsstrategieen doorlopend bij elke updatecyclus controleren op prijs, netto HomeWizard-zonopwek en actuele teruglevering. De gecorrigeerde zonwaarde gebruikt nu ook de actuele PowerStream-output uit de API, zodat batterijteruglevering niet als zon wordt gezien.

Versie `0.5.28` beperkt automatische PowerStream-strategieaanpassingen tot maximaal een keer per minuut per PowerStream. De gecorrigeerde opwek is nu een netto waarde: positief betekent netto opwek, negatief betekent netto verbruik.

Versie `0.5.29` verwijdert de HomeWizard import/export-totalen uit de EEC app entiteiten. Alleen relevante status-, totaalvermogen- en fasevermogenmetingen blijven zichtbaar.

Versie `0.5.31` toont batterij-inhoud en waarde rechtstreeks op de Delta Pro/Delta Pro 3 devices, corrigeert HomeWizard-vermogens die als factor 10 te hoog binnenkomen en maakt de weerweergave grafischer met iconen en een 24-uurs temperatuurgrafiek.

Versie `0.5.32` brengt opslag, PowerStream-sturing, scenario's, prijzen, netto opwek en weer samen in één hoofd-dashboard. De app voegt totaal-sensoren toe voor accu-SoC, beschikbare kWh en actuele euro-waarde, plus een beste-scenario sensor. Batterijvermogens krijgen dezelfde factor-10 bescherming als PowerStream/HomeWizard-weergaven.

Versie `0.5.33` maakt het main dashboard robuuster na updates door nieuwe totaal- en scenario-advieskaarten dynamisch op EEC-attributen te vinden in plaats van hardcoded nieuwe entity_id's te gebruiken.

Versie `0.5.34` centraliseert wattage-normalisatie voor PowerStream, HomeWizard en batterijvermogens en voegt lokale verificatietests toe voor factor-10 correcties en de dynamische main-dashboard afspraken.

Versie `0.5.35` maakt de PowerStream- en scenario-beslislogica lokaal testbaar. De uitvoerbare groepsstrategie en het beste-scenario advies gebruiken nu dezelfde policy-helper, met tests voor handelen, laden bij lage prijs/zon, lage batterijbuffer en scenarioselectie.

Versie `0.5.36` voegt een dashboard-gereedheidssensor toe. Het main dashboard toont nu direct of basisdata voor prijzen, batterijen, PowerStreams, netto opwek, weer en scenario's compleet genoeg is voor betrouwbare inzichten.

Versie `0.5.37` maakt de gereedheid grafischer met een numerieke dashboard-score in procenten. Het main dashboard toont deze score als gauge naast de tekststatus, zodat ontbrekende basisdata sneller opvalt.

Versie `0.5.38` voegt een concrete `volgende stap` toe aan de gereedheidsflow. Het main dashboard geeft nu niet alleen score/status, maar ook de eerste actie die nodig is om basisdata of sturing betrouwbaar te maken.

Versie `0.5.39` corrigeert de gereedheidskaart naar een echte grid met losse kaarten, zodat de score-gauge, status en volgende stap grafisch betrouwbaar renderen in Lovelace. De dashboardtest bewaakt dit kaarttype.

Versie `0.5.40` voegt packaging-tests toe voor HACS/Home Assistant updates. De tests bewaken dat `manifest.json`, `APP_VERSION` en de README-versie gelijk blijven en dat de HACS-domainstructuur naar de juiste integratiemap wijst.

Versie `0.5.41` vereenvoudigt de eerste installatiestap. Bij toevoegen van de integratie hoef je alleen naam, EcoFlow access key en secret key in te vullen; prijsbron, Quatt-opslag, weerstad, testmodus en andere defaults worden automatisch gezet en blijven later aanpasbaar via Configureren.

Versie `0.5.42` maakt strategie-keuzes leesbaar in het dashboard. Selecties tonen nu labels zoals `Eigen gebruik`, `Terugleveren`, `Handelen` en `Uit`, terwijl bestaande interne strategiecodes nog steeds worden geaccepteerd.

Versie `0.5.43` neemt testmodus mee in de gereedheidsflow. Als testmodus nog aan staat, toont het main dashboard de app als `gedeeltelijk` klaar met als volgende stap `zet testmodus uit`, zodat duidelijk is dat scenario's nog niet echt sturen.

Versie `0.5.44` maakt de actieknoppen op het main dashboard dynamisch. Start, EcoFlow API-check en prijzen ophalen worden nu gevonden via EEC-attributen in plaats van hardcoded button entity_id's.

Versie `0.5.45` maakt ook de kernkaarten `Nu` en de verwachte zonbesparing dynamischer. Prijs-, netto-opwek-, weer- en besparingssensoren krijgen EEC-discovery-attributen, zodat het main dashboard minder afhankelijk is van vaste entity_id's.

Versie `0.5.46` maakt de weerlijst op het main dashboard ook dynamisch via EEC-attributen. Daarmee blijven weer, zonverwachting en verwachte besparing zichtbaar na hernoemen of opnieuw toevoegen van entiteiten.

Versie `0.5.47` maakt ook de bovenste bedieningskaart op het main dashboard dynamisch. Scenario, testmodus, status en versie worden via EEC-discovery-attributen gevonden, zodat de basisflow minder afhankelijk is van vaste entity_id's.

Versie `0.5.48` splitst PowerStreams op het main dashboard in bediening en live-weergave. Terugleververmogen, gekoppelde accu-SoC, beschikbare Wh en status worden grafischer getoond met gauges, terwijl de instelbare setpoints en strategieen compact bij elkaar blijven.

Versie `0.5.49` maakt scenario's uitlegbaar en grafischer in het main dashboard. Elk scenario krijgt nu een compacte reden voor het advies, en het dashboard splitst scenario-advies van scenario-effect met gauges voor vermogen en EUR/uur.

Versie `0.5.50` maakt de zelfdiagnose zichtbaarder op het main dashboard. Naast score en volgende stap toont de app nu per databron een Datacheck: prijzen, batterijen, PowerStreams, netto opwek, weer, scenario's en sturing.

Versie `0.5.51` voegt een compact systeemoverzicht toe aan de Gereedheid-kaart. Je ziet direct hoeveel batterijen en PowerStreams live data leveren, hoeveel prijsuren/scenario's beschikbaar zijn en welke kernwaarden de app gebruikt.

Versie `0.5.52` maakt de uitvoerbaarheid van sturing zichtbaarder. De bediening toont nu een aparte sturing-status en laatste actie, inclusief attributen voor PowerStream-fouten, afgeremde strategie-updates en actieve setpoints.

Versie `0.5.53` vereenvoudigt de apparaatconfiguratie. Importeren van EcoFlow en HomeWizard staat nu vóór handmatig toevoegen, en handmatige PowerStream/Smart Plug formulieren vragen niet meer om technische command-JSON; de app gebruikt veilige standaardcommando's en bewaart bestaande custom commands bij wijzigen.

Versie `0.5.54` splitst normale en geavanceerde instellingen. De normale instellingen tonen alleen prijsbron, Quatt-opslag, weerstad en testmodus; API-hosts, keys, custom prijs-URL en SMA-cloudvelden staan in Geavanceerde instellingen.

Versie `0.5.55` voegt extra integriteitschecks toe voor releasebestanden. De testset vangt nu dubbele vertaalkeys, achtergebleven technische command-JSON labels en ontbrekende kernmodules voordat een update naar HACS gaat.

Versie `0.5.56` maakt de automatische prijsgrenzen zichtbaar op het main dashboard. De actuele prijs, goedkope grens en dure grens staan nu samen in `Nu`, zodat scenario-advies op basis van prijs beter te volgen is.

Versie `0.5.57` voegt een strategie-match toe aan het adviesblok. Het main dashboard laat nu zien of de gekozen globale strategie het beste berekende scenario volgt, daarvan afwijkt, uit staat of nog wacht op scenario-data.

Versie `0.5.58` toont vrije opslagruimte in het main dashboard. Naast beschikbare kWh en euro-waarde zie je nu ook vrije kWh en de geschatte waarde/kosten van die ruimte bij de actuele stroomprijs.

Versie `0.5.59` trekt vrije opslagruimte door naar PowerStream-groepen. Per PowerStream + gekoppelde Delta zie je nu ook vrije Wh, zodat duidelijker wordt of die groep nog zon of goedkope stroom kan opslaan.

Versie `0.5.60` gebruikt vrije opslagruimte ook in de PowerStream-groepsbeslissing. De actie-attributen tonen nu of laden/ontladen kan en welke blokkade geldt, bijvoorbeeld geen vrije accuruimte of accu onder minimum.

Versie `0.5.61` voegt een compact flow-advies toe aan het main dashboard. Dit vat gereedheid, testmodus, gekozen strategie, beste scenario, actuele prijs, netto opwek en accu-inhoud samen in één regel, zodat sneller zichtbaar is wat de app nu logisch vindt.

Versie `0.5.62` zet bovenaan het main dashboard een grafische Flow-strip: datascore, advies, scenarioselectie, testmodus en startknop staan naast elkaar. De dashboardtests bewaken nu ook dat de PowerStream-vermogensgauge in watt blijft en niet per ongeluk naar deciwatt-schaal verschuift.

Versie `0.5.63` maakt scenario-advies uitvoerbaarder. Het dashboard krijgt een aparte `Advies`-startknop die het beste berekende scenario selecteert en direct toepast. Het 50%-bufferscenario is nu ook een echte globale en PowerStream-strategie, zodat dit scenario niet alleen zichtbaar maar ook bestuurbaar is.

Versie `0.5.64` maakt `Uit` leidend in de uitvoerflow. Als de globale strategie uit staat, zet de app PowerStreams op 0 W en Smart Plugs uit voordat oude per-PowerStream strategieen nog iets kunnen sturen. Een test bewaakt dat deze veiligheidsvolgorde behouden blijft.

Versie `0.5.65` vereenvoudigt de hoofd-flow op het dashboard. De primaire `Advies`-startknop staat alleen nog in de bovenste Flow-strip; het aparte actieblok heet nu `Handmatig` en bevat alleen handmatige strategie-start, EcoFlow API-check en prijzen ophalen.

Versie `0.5.66` maakt de `Advies`-startknop voorzichtiger. Als het beste scenario alleen `wachten`, `stand-by` of `buffer bewaken` is zonder positief effect, zet de app geen strategie om maar meldt hij dat het advies wacht.

Versie `0.5.67` laat de Flow-strip dezelfde startbaarheidslogica gebruiken als de `Advies`-knop. De flow-samenvatting toont nu `advies wacht` als het beste scenario niet uitvoerbaar is, met attributen `best_actionable` en `start_button_state`.

Versie `0.5.68` maakt de startstatus in de Flow-strip eenduidiger. `start_button_state` kan nu `actie nodig`, `wachten`, `testmodus` of `startbaar` zijn en krijgt een korte `start_button_reason`.

Versie `0.5.69` voegt een losse `startstatus` sensor toe aan de Flow-strip. Daardoor is `actie nodig`, `wachten`, `testmodus` of `startbaar` direct als eigen dashboardtegel zichtbaar, naast het langere flow-advies.

Versie `0.5.70` maakt het hoofd-dashboard expliciet de primaire route. `dashboards/ecoflow-energy-control.yaml` bevat de volledige flow voor status, sturing, scenario's, prijzen, netto opwek, weer en diagnose; de andere dashboards blijven alleen optionele detail- en testweergaven.

Versie `0.5.71` voegt een concreet uitvoerplan toe aan het hoofd-dashboard. Per PowerStream-groep bundelt de app nu actie, advieswattage, huidig wattage, gekoppelde accu, accu-SoC, vrije Wh, blokkades, throttle-status en eventuele commandfout in één dashboard-sensor.

Versie `0.5.72` maakt de Datacheck strenger en duidelijker. PowerStreams worden pas volledig klaar gemeld als de gekoppelde accu en accu-SoC bekend zijn, beperkte PowerStream-telemetrie wordt als waarschuwing getoond, en stuurfouten of de 1-minuut begrenzing verschijnen als concrete volgende stap.

Versie `0.5.73` voegt een compacte `Auto`-status toe aan de Flow-strip. Deze tegel laat direct zien of automatische sturing actief, uit, testmodus, wachtend, afwijkend of geblokkeerd is en geeft als attribuut de reden en het beste scenario mee.

Versie `0.5.74` laat de Flow-strip direct reageren op de testmodus-schakelaar. De runtime-testmodus wordt nu ook in de dashboard-readiness gebruikt, zodat `Auto`, `Start`, `Datacheck` en `Volgende stap` niet blijven hangen op de oude configuratiewaarde.

Versie `0.5.75` voegt een packaging-check toe die bewaakt dat de README ook een changelogregel heeft voor de actuele HACS-versie. Zo blijft het updatepad controleerbaar en is per release zichtbaar wat er in de hoofdflow is veranderd.

Versie `0.5.76` voegt regressietests toe voor veilig opslaan vanuit de configuratieflow. Algemene en geavanceerde instellingen moeten bestaande apparaten blijven mergen en daarna de integratie herladen, zodat updates en simpele instellingen niet per ongeluk device-lijsten kwijtraken.

Versie `0.5.77` voegt een service-integriteitscheck toe. De test bewaakt dat alle runtime-acties uit het dashboard ook als Home Assistant-service bestaan, in `services.yaml` staan en in de integratie worden geregistreerd.

Versie `0.5.78` verrijkt de PowerStream-bediening op het hoofd-dashboard. De teruglever-slider en groepsstrategie tonen nu ook gekoppelde accu, vrije Wh, reden van het advies, throttling en eventuele strategie-commandfout als attributen.

Versie `0.5.79` behoudt de laatste PowerStream-commanddiagnose na gewone polling. `last_powerstream_command` en `last_powerstream_error` blijven zichtbaar in het hoofd-dashboard totdat een nieuw commando ze overschrijft.

Versie `0.5.80` maakt prijs- en scenario-advies beter uitlegbaar. De actuele prijs- en scenario-sensoren tonen nu ook goedkope/dure prijsgrenzen en gecorrigeerde netto-opwek als attributen, zodat het hoofd-dashboard duidelijker laat zien waarop een advies is gebaseerd.

Versie `0.5.81` verrijkt de 4/12/24-uurs zonverwachting. De weersensoren tonen nu ook horizon, weerlabel, icoon, iconenreeks, temperatuur, bewolking en uurdata als attributen, zodat de weer- en scenario-invoer in het hoofd-dashboard beter te controleren is.

Versie `0.5.82` maakt de prijs-Datacheck dashboardgerichter. De app waarschuwt nu ook als er wel ruwe prijsrecords zijn, maar de komende-uren prijsgrafiek leeg of te kort is.

Versie `0.5.83` maakt de weer-iconenreeks dynamisch. Het hoofd-dashboard gebruikt nu een eigen `komende uren` weersensor in plaats van een hardcoded markdownverwijzing naar `sensor.ecoflow_energy_control_applicatie_zon_nu`.

Versie `0.5.84` beperkt overgebleven hardcoded dashboard-entiteiten tot ApexCharts-bronnen. De temperatuurkaart gebruikt nu de `komende uren` weersensor en een dashboardtest bewaakt welke vaste grafiekbronnen nog toegestaan zijn.

Versie `0.5.85` voegt een dashboardtest toe voor de volledige gebruikersflow: zien, kiezen, sturen en begrijpen. Daarmee blijft het hoofd-dashboard beschermd tegen ontbrekende kernrollen voor status, scenario's, knoppen, prijzen, netto-opwek, opslag en weer.

Versie `0.5.86` maakt ook de optionele PowerStream-, app-stijl- en scenario-dashboards dynamischer. Oude vaste entiteiten voor zon, prijs, status, HomeWizard en versie zijn vervangen door EEC-discovery-attributen, met tests die terugval naar die fragiele namen blokkeren.

Versie `0.5.87` voegt een compacte `Waarom`-tegel toe aan het adviesblok van het hoofd-dashboard. Deze vat prijsniveau, netto zon/verbruik, beschikbare opslag en de gekozen beste actie samen, zodat de scenarioflow sneller te begrijpen is.

Versie `0.5.88` maakt EcoFlow-apparaten importeren eenvoudiger. De app stelt nu automatisch een apparaattype voor op basis van EcoFlow metadata zoals productnaam, model en device type, zodat je meestal alleen hoeft te controleren en bevestigen.

Versie `0.5.89` maakt PowerStream-sturing beter uitlegbaar. Handmatige slider/service-acties, strategie-acties en `strategie uit` worden nu als commandobron bewaard en zichtbaar gemaakt in de PowerStream-context.

Versie `0.5.90` maakt de Datacheck concreter. Elke readiness-check bevat nu detailattributen, zoals prijsuren, grafiekuren, ingestelde/live apparaten, netto opwek, weeruren, scenario-aantal, testmodus en laatste PowerStream-bron.

Versie `0.5.91` maakt de Datacheck direct leesbaar in het hoofd-dashboard. Elke check toont nu in de entity-regel zelf `status: melding`, terwijl de losse status en detailwaarden als attributen beschikbaar blijven.

Versie `0.5.92` geeft Datacheck-regels dynamische iconen. Klaar, gedeeltelijk, actie nodig en onbekend krijgen elk een herkenbaar icoon, zodat het hoofd-dashboard sneller scanbaar is.

Versie `0.5.93` maakt de batterij-Datacheck strenger. Batterijtelemetrie telt pas als volledig bruikbaar als er ook een actuele SoC/batterijstand is gevonden; SoC-instellingen zoals minimum, maximum, backup of reserve worden niet meer als batterijstatus gezien.

Versie `0.5.94` maakt het hoofd-overzicht en de totale opslag strenger gekoppeld aan ingestelde apparaten. Alleen batterijen die in EEC app zijn toegevoegd tellen nog mee in totale SoC/kWh/euro's, en het overzicht toont hoeveel ingestelde accu's echt een SoC leveren.

Versie `0.5.95` koppelt ook het uitvoerplan op het hoofd-dashboard strikt aan ingestelde PowerStreams. Het adviesblok toont daardoor alleen groepen die je in EEC app hebt toegevoegd, met fallback naar de ingestelde naam, fase en gekoppelde accu als live data nog ontbreekt.

Versie `0.5.96` maakt het uitvoerplan bruikbaarder bij beperkte telemetrie. Als live PowerStream-data ontbreekt, rekent het dashboard alsnog een fallback-advies uit met dezelfde strategiehelper als de echte sturing, inclusief reden, advies-wattage, laad/ontlaadblokkades en gekoppelde batterijstatus waar beschikbaar.

Versie `0.5.97` maakt het uitvoerplan directer uitvoerbaar. Per PowerStream-groep toont het dashboard nu het verschil tussen huidig en geadviseerd wattage, of een commando nodig is, en hoeveel groepen moeten bijsturen.

Versie `0.5.98` maakt bijsturen zichtbaar in de bovenste Flow-strip. Het hoofd-dashboard toont nu een wattage-gauge voor het totale verschil tussen huidig en geadviseerd PowerStream-vermogen en een tegel met het aantal groepen dat een commando nodig heeft.

Versie `0.5.99` maakt de Flow-strip rustiger en de bijstuur-gauge logischer. De bovenste kaart gebruikt nu minder kolommen en de gauge toont het absolute aantal watt dat nog moet veranderen, met de richting als attribuut in het uitvoerplan.

Versie `0.5.100` maakt bijsturen per PowerStream-groep zichtbaar. Het live PowerStreams-blok toont nu naast huidig vermogen ook advies-wattage en resterend verschil per groep, zodat je direct ziet welke PowerStream nog moet opschuiven.

Versie `0.5.101` voegt per PowerStream-groep een compacte bijstuurstatus toe. In `PowerStreams - live` zie je nu direct of een groep `ok`, `bijsturen`, `wacht` of `fout` is, naast de wattage-gauges.

Versie `0.5.102` maakt die bijstuurstatus betrouwbaarder bij ontbrekende live PowerStream-data. Een groep zonder bekende actuele uitgangswaarde wordt niet meer als `ok` getoond, maar blijft op `wacht` of `bijsturen` afhankelijk van het adviesvermogen.

Versie `0.5.103` voegt een compacte `volgende actie` toe aan de hoofdflow. Het main dashboard toont nu in gewone taal welke PowerStream als eerste bijgestuurd wordt, welk doelwattage geldt, of waarom de app wacht.

Versie `0.5.104` maakt de `volgende actie` beslislogica lokaal testbaar buiten Home Assistant. De testset controleert nu concreet de volgorde fout, wachten, bijsturen, vasthouden en stand-by, zodat het main dashboard voorspelbaar blijft.

Versie `0.5.105` maakt `volgende actie` eerlijker over uitvoerbaarheid. Testmodus, onvolledige datacheck en scenario-uit blokkeren nu zichtbaar een PowerStream-commando, zodat het main dashboard niet suggereert dat er echt gestuurd wordt wanneer dat niet zo is.

Versie `0.5.106` voegt een korte `uitvoerbaar` status toe aan de Flow-strip en het Advies-blok. Je ziet nu direct `kan sturen`, `testmodus`, `data nodig`, `scenario uit`, `wacht` of `fout` naast de langere volgende actie.

Versie `0.5.107` voegt een compacte `Bronnen`-tegel toe aan de Gereedheid-kaart. Die toont de eerste ontbrekende of beperkte databron, of `alle bronnen ok`, zodat je minder in de losse Datacheck-regels hoeft te zoeken.

Versie `0.5.108` voegt `Scenario keuze` toe aan het Advies-blok. Deze regel vergelijkt het gekozen scenario met het beste advies en toont direct of je keuze volgt of afwijkt, inclusief het geschatte verschil in EUR/u.

Versie `0.5.109` maakt de `Scenario keuze` logica lokaal testbaar buiten Home Assistant. De testset bewaakt nu concreet `uit`, `wachten`, `volgt advies` en `wijkt af` inclusief het EUR/u verschil.

Versie `0.5.110` maakt ook de `Bronnen`-samenvatting lokaal testbaar buiten Home Assistant. De readiness-tests bewaken nu `alle bronnen ok`, eerste blocking issue, eerste warning issue en lege bronchecks.

Versie `0.5.111` versterkt de HACS/release-controle. De packaging-tests bewaken nu ook dat alle API-bronnen en alle meegeleverde dashboards bestaan, en dat de dashboards in de README vindbaar blijven.

Versie `0.5.112` bewaakt de korte naamgeving in gebruikerszichtbare bestanden. Dashboards, vertalingen en manifest moeten `EEC app` blijven gebruiken en mogen niet terugvallen naar de lange oude applicatienaam.

Versie `0.5.113` bewaakt de dashboard-HACS-afhankelijkheden. De dashboardtests lezen nu alle gebruikte `custom:*` kaarten en controleren dat de vereiste frontend-kaarten in de README vermeld blijven.

Versie `0.5.114` houdt de vaste dashboard-entiteiten stabiel na de korte naamswijziging naar `EEC app`. Nieuwe installaties krijgen nog steeds de object-id's die de meegeleverde grafieken en knoppen verwachten, zodat prijs- en weergrafieken niet door een andere naamgeving op `loading` blijven hangen.

Versie `0.5.115` maakt de datacheck strenger voor PowerStreams. De hoofdflow telt alleen nog PowerStream-data, stuurfouten en 1-minuut wachttijden mee van apparaten die in EEC app zijn toegevoegd, zodat vreemde of oude API-data het main dashboard niet onterecht klaar of geblokkeerd maakt.

Versie `0.5.116` maakt stuurproblemen in de hoofdflow concreter. Het uitvoerplan en de sturing-status tonen nu de eerste PowerStream met fout of wachttijd, inclusief naam, serienummer, foutmelding en resterende throttle-seconden, en negeren daarbij niet-ingestelde apparaten.

Versie `0.5.117` voegt een compact `flow overzicht` toe aan het main dashboard. Deze ene regel bundelt databronstatus, prijscontext, netto zon/verbruik, beschikbare accu, beste scenario en eerstvolgende stuuractie, zodat de basisinzichten sneller zichtbaar zijn zonder extra instellingen.

Versie `0.5.118` maakt het `flow overzicht` grafischer. De tegel krijgt nu een korte dashboardstatus en dynamisch icoon voor `kan sturen`, `testmodus`, `data nodig`, `scenario uit`, `wacht`, `fout` of `stand-by`, in plaats van technische blokkadecodes.

Versie `0.5.119` voegt een compacte `flow_phase` toe aan het `flow overzicht`. Daarmee is direct zichtbaar of de app in `setup`, `simuleren`, `sturen`, `wachten`, `uit`, `fout` of `stand-by` zit.

Versie `0.5.120` maakt die flowfase ook zichtbaar als eigen `Fase`-tegel in de bovenste Flow-strip. Zo hoef je de attributen van `flow overzicht` niet te openen om te zien waar de app in de flow zit.

Versie `0.5.121` maakt de flowfase-, status- en icoonlogica lokaal testbaar buiten Home Assistant. De policy-tests bewaken nu alle zichtbare fases van het main dashboard, zodat de simpele flow voorspelbaar blijft.

Versie `0.5.122` laat gecorrigeerde HomeWizard-fasewaarden ook negatief worden wanneer verbruik hoger is dan zonopwek na aftrek van PowerStream-teruglevering. Daardoor blijft de flow zien of er netto opwek of netto verbruik is, zonder factor-10 correcties te verliezen.

Versie `0.5.123` voegt bovenaan het hoofd-dashboard een zichtbare `EUR/u` flow-tegel toe. Deze toont de actuele verwachte waarde van het beste scenario en bewaart als attributen welk scenario wint, wat de reden is en hoeveel het afwijkt van de gekozen strategie.

Versie `0.5.124` voegt een compacte `Keuze`-tegel toe aan de bovenste Flow-strip. Daarmee zie je direct of de gekozen strategie het advies volgt, daarvan afwijkt, uit staat of wacht op scenario-data.

Versie `0.5.125` voegt een `Klaar`-tegel toe aan de bovenste Flow-strip. Deze combineert datakwaliteit, testmodus, gekozen strategie, scenario-advies en uitvoerbaarheid tot één oordeel: klaar, actie nodig, testmodus, afwijkend, wachten, uit of stand-by.

Versie `0.5.126` maakt het `Klaar`-oordeel lokaal testbaar buiten Home Assistant. De policy-tests bewaken nu alle zichtbare klaar-statussen en iconen, terwijl de sensor alleen nog de geteste beslisregel aan het dashboard koppelt.

Versie `0.5.127` vereenvoudigt de apparaatflow: `HomeWizard via Home Assistant` staat alleen nog als aparte importactie in Configureren en niet meer dubbel onder handmatig apparaat toevoegen.

Versie `0.5.128` zet de concrete `Volgende stap` ook bovenaan in de Flow-strip als `Stap`. Daardoor zie je naast `Klaar` direct welke actie nodig is om de app betrouwbaar te laten sturen.

Versie `0.5.129` maakt de bovenste Flow-strip rustiger. Technische stuurdetails en scenario/testmodus-keuzes blijven in de detailblokken zichtbaar, maar bovenaan staan alleen nog de kernsignalen: data, klaar, stap, overzicht, advies, waarde, keuze, start, auto en de primaire adviesknop.

Versie `0.5.130` borgt die rustige hoofdflow met een dashboardtest. De bovenste Flow-strip mag maximaal 10 EEC-tegels bevatten, zodat nieuwe technische details niet ongemerkt terug naar de primaire flow kruipen.

Versie `0.5.131` maakt PowerStream toevoegen eenvoudiger: als er precies één Delta-batterij bekend is, wordt die automatisch als gekoppelde batterij voorgeselecteerd. Bij nul of meerdere batterijen blijft de keuze expliciet.

Versie `0.5.132` borgt de 1-minuut begrenzing op automatische PowerStream-strategiecommando's met een lokale regressietest. De app bewaart per PowerStream de laatste strategie-aanpassing en geeft resterende wachttijd door aan dashboard en diagnostiek.

Versie `0.5.133` laat ook handmatig gestarte scenario's via dezelfde begrensde PowerStream-uitvoer lopen als de automatische strategie. Daardoor respecteren `Start` en `Advies` dezelfde 1-minuut wachttijd en blijft commanddiagnose zichtbaar in het dashboard.

Versie `0.5.134` zet direct onder de Flow-strip een compact grafisch `Basis` blok. Daarin staan netto opwek/verbruik, actuele prijs, totale accu, beschikbare kWh, PowerStream-teruglevering en verwachte zonwaarde bij elkaar, zodat de belangrijkste inzichten zichtbaar zijn zonder door detailkaarten te zoeken.

Versie `0.5.135` voegt een compact grafisch `Scenario - nu` blok toe aan het main dashboard. Dit toont het beste scenario, de match met de gekozen strategie, uitvoerbaarheid, adviesvermogen, EUR/u en dagwaarde als directe dashboardwaarden voor het actuele advies.

Versie `0.5.136` zet `Scenario - nu` direct onder `Basis` in de primaire dashboardflow. Zo staan beslissing, kernmetingen en actuele scenariokeuze bovenaan bij elkaar, terwijl de latere kaarten vooral detail en diagnose blijven.

Versie `0.5.137` vereenvoudigt de configuratievolgorde. In Configureren staan apparaten importeren en toevoegen nu bovenaan, terwijl algemene en geavanceerde instellingen pas daarna komen. Zo loopt de normale installatie sneller naar data op het dashboard.

Versie `0.5.138` voegt een compacte `live bewijs` sensor toe. De Gereedheid-kaart toont nu hoeveel databronnen echt bewezen werken met live data, inclusief bronstatussen als attributen, zodat de stap van lokale tests naar Home Assistant-validatie zichtbaarder wordt.

Versie `0.5.139` maakt `live bewijs` duidelijker door databewijs en stuur-bewijs te scheiden. De sensor toont nu direct hoeveel databronnen werken en of sturing klaar, gedeeltelijk of geblokkeerd is, zodat testmodus en echte uitvoering niet door elkaar lopen.

Versie `0.5.140` werkt de README bij op de huidige simpele flow: eerst apparaten importeren/toevoegen, daarna instellingen finetunen. De README bevat nu ook een korte live-validatiecheck voor `Flow`, `Basis`, `Scenario - nu`, `Gereedheid > Bewijs` en `Datacheck`.

Versie `0.5.141` maakt scenario-uitkomsten eerlijker bij ontbrekende invoer. Scenario-attributen tonen nu `input_ready` en `input_warnings`, en de redenregel noemt ontbrekende prijsdata, prijsgrenzen of accu-SoC zodat nulwaarden niet als volledig advies overkomen.

Versie `0.5.142` zet die invoerstatus ook zichtbaar in `Scenario - nu`. De nieuwe compacte `Input`-tegel toont direct `ok`, `beperkt` of `wachten`, met attributen voor ontbrekende prijsdata, prijsgrenzen, accu-SoC en netto zonvermogen.

Versie `0.5.143` maakt de uitvoerbaarheidstaal in de hoofdflow strakker. `Kan sturen` verschijnt nu alleen wanneer er echt een PowerStream-setpointcommando nodig is; `hold` en `stand-by` blijven zichtbaar als rustige status zonder onnodig stuurcommando.

Versie `0.5.144` maakt PowerStream-vermogens beter verifieerbaar. De app bewaart nu of het zichtbare vermogen uit echte telemetrie komt of uit een opgeslagen/gestuurd doel, en het uitvoerplan wacht op een gemeten waarde wanneer alleen een doelwaarde bekend is.

Versie `0.5.145` maakt die meetzekerheid zichtbaar in het hoofd-dashboard. `Scenario - nu` en `Advies` krijgen een compacte `Meting`-status die toont of PowerStream-waarden echt gemeten zijn, nog op meting wachten, beperkt zijn, een fout hebben of dat er geen PowerStreams zijn.

Versie `0.5.146` voegt een zichtbare `Zeker`-score toe aan `Scenario - nu`. Deze gauge combineert bronstatus, scenario-input, PowerStream-meetzekerheid en uitvoerbaarheid tot een simpele betrouwbaarheidsscore voor het actuele advies.

Versie `0.5.147` maakt die score uitlegbaar zonder attributen te openen. `Scenario - nu` en `Advies` tonen nu ook `Zekerheid`: de belangrijkste reden achter een lagere of middelmatige score, of `advies betrouwbaar` als de score hoog genoeg is.

Versie `0.5.148` maakt de primaire startflow duidelijker. Bovenaan staat nu naast `Start` een zichtbare `Waarom`-tegel met de reden waarom de `Advies`-knop wel of niet zinvol is; de automatische status is verplaatst naar het detailblok `Advies`.

Versie `0.5.149` voegt een zichtbare `Setup`-status toe aan `Gereedheid`. Deze tegel toont of de minimale inrichting compleet is en noemt de eerstvolgende ontbrekende stap, zoals batterij, prijsbron, PowerStream, zonmeter of weerstad.

Versie `0.5.150` maakt de financiële impact van het actuele advies compacter zichtbaar. `Scenario - nu` krijgt een `Totalen`-tegel met het geschatte dag-, week- en maand-effect van het beste scenario.

Versie `0.5.151` maakt zichtbaar wat een afwijkende scenariokeuze kost. `Scenario - nu` krijgt een `Mis EUR/u`-gauge die de geschatte gemiste waarde per uur toont wanneer de gekozen strategie afwijkt van het beste scenario.

Versie `0.5.152` zet de besliscontext hoger in het hoofd-dashboard. Het `Basis`-blok toont nu ook `Context`: prijsniveau, netto zon/verbruik, beschikbare accu en de actie van het beste scenario in één regel.

Versie `0.5.153` maakt de bovenste flow directer bedienbaar. `Scenario` en `Test` staan nu in de primaire `Flow`-strip naast het advies en de startknop, terwijl de startuitleg in het detailblok `Advies` blijft.

Versie `0.5.154` maakt de primaire flow uitvoergerichter. De bovenste strip toont nu `Kan sturen` in plaats van een dubbele klaar-status, zodat direct zichtbaar is of het advies echt een PowerStream-actie kan uitvoeren; de algemene klaar-status staat bij `Gereedheid`.

Versie `0.5.155` haalt de financiele impact naar de primaire flow. De bovenste strip toont nu `Totalen` met het geschatte dag-, week- en maand-effect van het beste scenario; het langere flow-overzicht staat in het detailblok `Advies`.

Versie `0.5.156` maakt de primaire flow zekerder leesbaar. De bovenste strip toont nu `Zeker` als betrouwbaarheidsgauge voor het actuele scenarioadvies; de concrete vervolgstap blijft zichtbaar in `Gereedheid`.

Versie `0.5.157` ruimt de bediening in het hoofd-dashboard op. De kaart `Keuze wijzigen` bevat alleen nog de echte keuzes `Scenario` en `Testmodus`; status, versie, sturing en laatste actie staan nu bij `Gereedheid` en `Advies`.

Versie `0.5.158` maakt de compacte scenariokaart uitvoerbaarder. `Scenario - nu` toont nu `Volgende`, de eerstvolgende PowerStream-actie uit het uitvoerplan; de losse `Dag EUR` staat in het detailblok `Advies`.

Versie `0.5.159` maakt de hoofdregel `Advies` concreter. De tekst combineert nu het beste scenario met de eerstvolgende PowerStream-actie uit het uitvoerplan en de actuele EUR/uur-waarde.

Versie `0.5.160` maakt de configuratieflow menselijker. Het optiescherm gebruikt nu duidelijkere labels zoals `Basisinstellingen`, `Technische instellingen` en `Handmatig toevoegen`, en de importstappen leggen kort uit dat apparaten worden gecontroleerd voordat ze worden opgeslagen.

Versie `0.5.161` trekt die vereenvoudigde termen door naar de README. De apparaatbeheer-sectie gebruikt nu dezelfde labels als Home Assistant en vermeldt expliciet dat importapparaten worden gecontroleerd voordat ze worden opgeslagen.

Versie `0.5.162` maakt diagnose sneller scanbaar. `Gereedheid` krijgt een `Probleem`-tegel die de eerste blokkade of waarschuwing uit de datachecks samenvat, zodat je niet meteen de hele Datacheck-lijst hoeft te lezen.

Versie `0.5.163` werkt de live-validatie in de README bij. De controlevolgorde noemt nu expliciet `Gereedheid > Probleem`, daarna `Bewijs` en pas daarna de detailregels in `Datacheck`.

Versie `0.5.164` maakt de `Probleem`-tegel leesbaarder. Interne checkkeys zoals `prices` en `powerstreams` worden nu als gewone labels getoond, zoals `prijzen`, `PowerStreams`, `netto opwek` en `sturing`.

Versie `0.5.165` brengt blokkades nog dichter bij de startflow. De bovenste `Flow`-strip toont nu `Probleem`; de losse `Keuze`-status is verplaatst naar `Scenario - nu`, naast `Match` en `Mis EUR/u`.

Versie `0.5.166` maakt de `Probleem`-tegel nog duidelijker. De tekst begint nu met `blokkeert` bij echte actie nodig en met `let op` bij waarschuwingen, gevolgd door het leesbare bronlabel.

Versie `0.5.167` zet de automatische stuurstatus direct in de bovenste `Flow`-kaart. De tegel `Auto` laat nu meteen zien of de app actief stuurt, in testmodus staat, wacht, uit staat, afwijkt of geblokkeerd is.
