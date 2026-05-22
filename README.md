# EcoFlow Energy Control

Lokale Home Assistant/HACS-integratie voor:

- EcoFlow Delta Pro en Delta Pro 3 uitlezen via EcoFlow Cloud API
- Twee EcoFlow PowerStreams aansturen via EcoFlow Cloud API
- Nederlandse spotprijzen uitlezen via een JSON-feed
- SMA Sunny Boy omvormers lokaal uitlezen via Modbus TCP
- Een grafisch controlpanel met strategie, drempels, testmodus en handmatige toepassing

## Status

Dit is een eerste werkende basis. Hij start standaard in **testmodus**, zodat commando's naar PowerStream niet meteen worden verzonden. EcoFlow gebruikt per apparaat en firmware verschillende command-payloads. Daarom zijn PowerStream-commando's configureerbaar als JSON-template.

## Installatie via HACS

1. Zet deze map in een Git repository.
2. Voeg de repository in HACS toe als custom repository van type `Integration`.
3. Installeer **EcoFlow Energy Control**.
4. Herstart Home Assistant.
5. Ga naar **Instellingen > Apparaten & diensten > Integratie toevoegen** en kies **EcoFlow Energy Control**.

Handmatig kan ook: kopieer `custom_components/ecoflow_energy_control` naar de `custom_components` map van Home Assistant en herstart.

## EcoFlow instellingen

Vraag in het EcoFlow Developer Portal een `access_key` en `secret_key` aan. Gebruik voor Europa standaard:

```text
https://api-e.ecoflow.com
```

Vul batterijen in als JSON:

```json
[
  {
    "name": "Delta Pro",
    "serial": "JOUW_SERIENUMMER",
    "quotas": ["pd.soc", "pd.inputWatts", "pd.outputWatts", "pd.invOutWatts"]
  },
  {
    "name": "Delta Pro 3",
    "serial": "JOUW_SERIENUMMER",
    "quotas": ["pd.soc", "pd.inputWatts", "pd.outputWatts", "pd.invOutWatts"]
  }
]
```

Vul PowerStreams in als JSON:

```json
[
  {
    "name": "PowerStream 1",
    "serial": "JOUW_SERIENUMMER",
    "max_watts": 800,
    "command": {
      "id": 1,
      "version": "1.0",
      "moduleType": 1,
      "operateType": "WN511_SET_PERMANENT_WATTS_PACK",
      "params": {"permanentWatts": "{{ watts }}"}
    }
  }
]
```

Als EcoFlow voor jouw PowerStream een andere `operateType`, `moduleType` of parameternaam vereist, pas je alleen dit JSON-template aan.

## SMA Sunny Boy

Zet Modbus TCP aan in de lokale webinterface van de SMA omvormer. Meestal is dit poort `502` en unit id `3`.

```json
[
  {
    "name": "Sunny Boy dak",
    "host": "192.168.1.50",
    "port": 502,
    "unit_id": 3
  }
]
```

## Spotprijzen

Standaard staat de feed op:

```text
https://enever.nl/api/stroomprijs_vandaag.php
```

Elke JSON-feed met uurrecords en een prijsveld zoals `prijs`, `price`, `value` of `electricity_price` kan worden gebruikt.

## Controlpanel

De integratie maakt entiteiten aan voor:

- huidige stroomprijs
- totaal SMA-vermogen
- batterij-SoC per ingestelde EcoFlow batterij
- strategie: `self_use`, `export`, `idle`
- testmodus
- goedkope en dure prijsdrempel
- doelvermogen voor terugleveren en eigen gebruik
- knop om de strategie direct toe te passen

Gebruik `dashboards/ecoflow-energy-control.yaml` als startpunt voor een Lovelace-dashboard.

## Strategie

De eerste strategie is eenvoudig en bewust veilig:

- onder de goedkope drempel: PowerStream doelvermogen naar `0 W`
- boven de dure drempel: PowerStream doelvermogen naar het ingestelde terugleverdoel
- daartussen: PowerStream doelvermogen naar het ingestelde eigen-gebruik-doel

Zolang testmodus aan staat, wordt alleen de laatste geplande actie getoond.

## Services

`ecoflow_energy_control.set_powerstream_watts`

```yaml
serial: JOUW_POWERSTREAM_SERIENUMMER
watts: 600
```

`ecoflow_energy_control.apply_strategy`

Past de ingestelde strategie eenmalig toe.

## Belangrijke opmerkingen

- Home Assistant Recorder bewaart de sensordata in je lokale Home Assistant database.
- De SMA-data loopt lokaal via je netwerk.
- EcoFlow-besturing loopt via de EcoFlow Cloud API, omdat EcoFlow voor deze apparaten geen stabiele lokale API aanbiedt.
- Begin altijd met testmodus aan en controleer in de EcoFlow app of het gebruikte command-template klopt voor jouw apparaat.

