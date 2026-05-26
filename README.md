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

- **Algemene instellingen**: API keys, prijsprovider, Quatt-opslag, SMA instellingen en testmodus.
- **EcoFlow apparaten importeren**: haalt apparaten op uit de EcoFlow API en laat je het type kiezen.
- **Apparaat toevoegen**: handmatig toevoegen.
- **Apparaat wijzigen**: bestaande configuratie aanpassen.
- **Apparaat verwijderen**: apparaat uit deze integratie verwijderen.

Bij importeren kies je eerst het gevonden EcoFlow-serienummer en daarna het type. Alleen bij een Smart Plug wordt gevraagd welke batterij ermee geladen wordt. Dit veld wordt gevuld met de reeds toegevoegde batterij-devices.

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
https://api.energyzero.nl/v1/energyprices
```

De integratie vraagt uurprijzen op voor vandaag en morgen met `usageType=1`, `interval=4` en standaard `inclBtw=false`. De Quatt-opslag van `0.015 EUR/kWh` wordt daar apart bij opgeteld, zodat de opslag zichtbaar en aanpasbaar blijft.

Je kunt in Algemene instellingen terugschakelen naar epexprijzen.nl of epexspot.com. Een eigen prijs-URL blijft mogelijk; als die is ingevuld, gaat die voor op de gekozen bron.

Prijsdata wordt dagelijks om **15:00** opgehaald en is ook handmatig te verversen met de prijs-ophaalknop.

## Dashboard

Het voorbeeld-dashboard staat in:

```text
dashboards/ecoflow-energy-control.yaml
```

Het dashboard gebruikt dynamische kaarten zodat hardcoded device-namen zoals `Delta Pro` of `PowerStream 1` niet meer nodig zijn.

Benodigde frontend-kaarten via HACS:

- `auto-entities`
- `apexcharts-card`

Zonder deze kaarten blijven de entiteiten werken, maar worden de dynamische lijsten of prijsgrafiek niet weergegeven.

## Huidige Versie

`0.5.13`

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
