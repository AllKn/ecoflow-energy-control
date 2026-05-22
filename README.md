# EcoFlow Energy Control Applicatie

Lokale Home Assistant/HACS-integratie voor EcoFlow, EPEX day-ahead prijzen, SMA clouddata en automatische laad-/terugleverstrategieën.

## Wat deze iteratie doet

- EcoFlow Delta Pro en Delta Pro 3 uitlezen via EcoFlow Cloud API.
- Twee of meer EcoFlow PowerStreams aansturen via EcoFlow Cloud API.
- EcoFlow Smart Plugs toevoegen om bijvoorbeeld een Delta Pro te laden bij voldoende zonnestroom.
- EPEX/day-ahead prijzen automatisch pollen via een externe JSON-feed.
- SMA Sunny Boy/ennexOS omvormers uitlezen via de SMA cloud/API, dus zonder lokale Modbus TCP.
- Apparaten 1 voor 1 toevoegen of verwijderen via het Home Assistant configuratiescherm.
- Een vereenvoudigd controlpanel met strategie, testmodus, laad-/terugleverdoelen en automatische prijsgrenzen.

## Installatie via HACS

1. Publiceer deze repository op GitHub.
2. Voeg de repository in HACS toe als custom repository van type `Integration`.
3. Installeer **EcoFlow Energy Control**.
4. Herstart Home Assistant.
5. Ga naar **Instellingen > Apparaten & diensten > Integratie toevoegen**.
6. Kies **EcoFlow Energy Control**.

## Eerste configuratie

Bij de eerste setup vul je alleen de algemene gegevens in:

- EcoFlow `access_key`
- EcoFlow `secret_key`
- EcoFlow API host, meestal `https://api-e.ecoflow.com`
- Prijsfeed URL
- SMA API host
- SMA API token
- SMA plant id
- SMA endpoint-template
- Testmodus

Standaard prijsfeed:

```text
https://api.stekker.app/api/v1/market_price_forecast?region=NL
```

De integratie accepteert ook andere JSON-feeds met uurprijzen, zolang er velden aanwezig zijn zoals `price`, `forecast`, `price_per_mwh`, `prijs`, `value` en een tijdveld zoals `period_start`, `datetime`, `start` of `timestamp`.

## Apparaten toevoegen

Ga na installatie naar:

```text
Instellingen > Apparaten & diensten > EcoFlow Energy Control > Configureren
```

Daar kun je kiezen:

- Algemene instellingen
- Batterij toevoegen
- PowerStream toevoegen
- SMA omvormer toevoegen
- Smart Plug toevoegen
- Apparaat verwijderen

### Batterij

Voor een Delta Pro of Delta Pro 3 vul je in:

- naam
- serienummer

De standaard EcoFlow quota's worden automatisch gebruikt.

### PowerStream

Per PowerStream vul je in:

- naam
- serienummer
- maximaal vermogen
- command-template

Standaard command-template:

```json
{
  "id": 1,
  "version": "1.0",
  "moduleType": 1,
  "operateType": "WN511_SET_PERMANENT_WATTS_PACK",
  "params": {
    "permanentWatts": "{{ watts }}"
  }
}
```

EcoFlow wijzigt command-payloads soms per firmware of apparaatserie. Daarom is dit bewust instelbaar.

### SMA omvormer

Voor SMA gebruik je de internet/API-route in plaats van lokale Modbus. Vul eerst bij algemene instellingen je SMA API token en plant id in.

Per omvormer vul je daarna in:

- naam
- SMA device id

Het standaard endpoint-template is:

```text
/monitoring/v1/plants/{plant_id}/devices/{device_id}/measurements/recent
```

Als jouw SMA Developer API of ennexOS endpoint een ander pad gebruikt, pas je alleen dit template aan.

### Smart Plug

Per Smart Plug vul je in:

- naam
- serienummer
- welke batterij ermee geladen wordt
- aan-command-template
- uit-command-template

De strategie zet Smart Plugs aan zodra de gemeten SMA-opwek boven de ingestelde zonnedrempel komt. Daarmee kun je bijvoorbeeld een Delta Pro automatisch laten laden bij zonneschijn.

## Controlpanel

Gebruik het voorbeeld:

[dashboards/ecoflow-energy-control.yaml](dashboards/ecoflow-energy-control.yaml)

De dashboard-entiteiten gebruiken nu de `_applicatie` naam, bijvoorbeeld:

```yaml
sensor.ecoflow_energy_control_applicatie_stroomprijs_nu
select.ecoflow_energy_control_applicatie_strategie
number.ecoflow_energy_control_applicatie_laadstekkers_aan_vanaf_zon
```

Als Home Assistant andere entity_id's maakt, zoek dan bij **Instellingen > Apparaten & diensten > Entiteiten** op `EcoFlow Energy Control Applicatie` en pas de YAML daarop aan.

## Strategie

De prijs wordt niet meer handmatig ingesteld. De integratie pollt de prijsfeed en berekent automatisch:

- goedkope prijsgrens: onderste kwart van de opgehaalde uurprijzen
- dure prijsgrens: bovenste kwart van de opgehaalde uurprijzen

Gedrag:

- goedkope uren: PowerStream doel naar `0 W`
- dure uren: PowerStream doel naar `teruglever doel`
- tussenliggende uren: PowerStream doel naar `eigen gebruik doel`
- voldoende zon: Smart Plugs aan om ingestelde Delta Pro's te laden

Begin altijd met **testmodus aan**. Dan zie je de geplande acties zonder dat de PowerStreams of Smart Plugs echt worden aangestuurd.

## Services

PowerStream vermogen instellen:

```yaml
service: ecoflow_energy_control.set_powerstream_watts
data:
  serial: JOUW_POWERSTREAM_SERIENUMMER
  watts: 600
```

Smart Plug schakelen:

```yaml
service: ecoflow_energy_control.set_smart_plug
data:
  serial: JOUW_SMART_PLUG_SERIENUMMER
  on: true
```

Strategie eenmalig toepassen:

```yaml
service: ecoflow_energy_control.apply_strategy
```

## Belangrijk

- Home Assistant Recorder bewaart de sensordata lokaal in je Home Assistant database.
- EcoFlow-besturing loopt via EcoFlow Cloud.
- SMA loopt in deze iteratie via de SMA cloud/API, niet meer via lokale Modbus.
- Controleer command-templates altijd eerst in testmodus.

