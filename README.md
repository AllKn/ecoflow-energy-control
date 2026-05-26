# EcoFlow Energy Control Applicatie

Lokale Home Assistant-integratie voor EcoFlow opslag, PowerStream-sturing, Quatt/EPEX prijzen, HomeWizard-opwekmeting en eenvoudige diagnose per toegevoegd apparaat.

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
- Quatt/EPEX prijzen via epexprijzen.nl, inclusief instelbare opslag van standaard `0.015 EUR/kWh`.
- Dagelijkse prijs-refresh om 15:00 voor planning tot en met einde volgende dag.
- HomeWizard lokale API voor ruwe opwek, met correctie voor PowerStream-teruglevering.

## Apparaten Beheren

Ga naar:

```text
Instellingen > Apparaten & diensten > EcoFlow Energy Control > Configureren
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

## Prijzen

Standaard:

```text
https://epexprijzen.nl/api/v1/prices/quatt-energy/hourly
```

De integratie telt standaard `0.015 EUR/kWh` opslag bij de EPEX-prijs op. Als epexprijzen.nl een andere provider-slug voor Quatt gebruikt, pas je alleen **epexprijzen.nl provider** aan bij Algemene instellingen.

Prijsdata wordt dagelijks om **15:00** opgehaald en is ook handmatig te verversen met **EPEX prijzen ophalen**.

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

`0.5.1`

## EcoFlow Signing

Versie `0.5.1` corrigeert de EcoFlow signing voor quota-uitlezingen: `nonce` is nu een 6-cijferige waarde en `timestamp` is weer de actuele milliseconden-timestamp. Dat voorkomt `8521 signature is wrong` bij quota-routes terwijl device-list wel werkt.
