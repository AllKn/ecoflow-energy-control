# EcoFlow Energy Control Applicatie

Lokale Home Assistant/HACS-integratie voor EcoFlow, EPEX day-ahead prijzen, SMA clouddata en automatische laad-/terugleverstrategieën.

## Wat deze iteratie doet

- EcoFlow Delta Pro en Delta Pro 3 uitlezen via EcoFlow Cloud API.
- Twee of meer EcoFlow PowerStreams aansturen via EcoFlow Cloud API.
- EcoFlow Smart Plugs toevoegen om bijvoorbeeld een Delta Pro te laden bij voldoende zonnestroom.
- EPEX/day-ahead prijzen automatisch pollen via een externe JSON-feed.
- SMA Sunny Boy/ennexOS omvormers uitlezen via de SMA cloud/API, dus zonder lokale Modbus TCP.
- HomeWizard Energy lokale API uitlezen voor totale opwekking via een P1/kWh-meter/Socket in je LAN.
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

Standaard prijsfeed voor Quatt Energy:

```text
https://epexprijzen.nl/api/v1/prices/quatt-energy/hourly
```

De applicatie telt hier standaard `0.015 EUR/kWh` opslag bij op voor Quatt Energy. In **Algemene instellingen** kun je de provider-slug, interval en opslag aanpassen. Laat `Spotprijs JSON URL` leeg om automatisch deze vorm te gebruiken:

```text
https://epexprijzen.nl/api/v1/prices/{provider}/{hourly|quarterly}
```

Als epexprijzen.nl de provider-slug voor Quatt anders noemt, pas je alleen **epexprijzen.nl provider** aan in de algemene instellingen; de opslag blijft apart instelbaar.

De integratie haalt de prijzen dagelijks om **15:00** opnieuw op, zodat de planning voor de volgende dag beschikbaar komt zodra epexprijzen.nl die publiceert. Je kunt dit ook handmatig triggeren met **EPEX prijzen ophalen**.

## Apparaten toevoegen

Ga na installatie naar:

```text
Instellingen > Apparaten & diensten > EcoFlow Energy Control > Configureren
```

Daar kun je kiezen:

- Algemene instellingen
- Apparaat toevoegen
- EcoFlow apparaten importeren
- Apparaat wijzigen
- Apparaat verwijderen

### Grafische apparaatwizard

Kies **Apparaat toevoegen** en selecteer daarna het type apparaat:

- EcoFlow Delta Pro
- EcoFlow Delta Pro 3
- EcoFlow PowerStream
- EcoFlow Smart Plug
- HomeWizard lokale meter
- SMA cloud omvormer

De integratie controleert de verbinding voordat het apparaat wordt opgeslagen:

- Eerste setup en algemene instellingen: EcoFlow access key + secret key via de EcoFlow device-list
- Delta Pro / Delta Pro 3: serienummer moet in jouw EcoFlow device-list voorkomen
- PowerStream: serienummer moet in jouw EcoFlow device-list voorkomen
- Smart Plug: serienummer moet in jouw EcoFlow device-list voorkomen
- HomeWizard: lokale `http://<ip>/api/v1/data` meting
- SMA: het ingestelde SMA cloud endpoint

Als deze controle faalt, blijft het apparaat uit de configuratie en krijg je een melding in de flow.

Met **Apparaat wijzigen** kun je bestaande apparaten aanpassen zonder ze eerst te verwijderen. De wizard vult de huidige waarden alvast in en controleert bij opslaan opnieuw de verbinding.

Met **EcoFlow apparaten importeren** haalt de integratie eerst de EcoFlow device-list op via je access key en secret key. Daarna kies je een gevonden serienummer en stel je zelf in wat het apparaat in deze applicatie is:

- Delta Pro
- Delta Pro 3
- PowerStream
- Smart Plug

Voor PowerStream kun je direct fase en maximaal vermogen instellen. Voor Smart Plug kun je instellen welke Delta ermee geladen wordt.

## Handmatige controles

Het dashboard bevat nu knoppen voor snelle diagnose:

- **EcoFlow API controleren**: controleert access key, secret key en regio-host via de EcoFlow device-list.
- **EPEX prijzen ophalen**: haalt de prijsfeed direct opnieuw op.

Het resultaat zie je in:

```text
sensor.ecoflow_energy_control_applicatie_status
sensor.ecoflow_energy_control_applicatie_laatste_actie
```

Bij een geslaagde EcoFlow-check staan de gevonden serienummers ook als attribuut `ecoflow_devices` op de status-sensor.

### Delta Pro en Delta Pro 3

Voor een Delta Pro of Delta Pro 3 vul je in:

- naam
- serienummer

De standaard EcoFlow quota's worden automatisch gebruikt.

### PowerStream

Per PowerStream vul je in:

- naam
- serienummer
- maximaal vermogen
- fase waarop de PowerStream teruglevert
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

### HomeWizard lokale opwekmeting

Zet in de HomeWizard Energy app de lokale API aan:

```text
Instellingen > Meters > jouw meter > Local API
```

Voeg daarna in deze integratie een HomeWizard meter toe met:

- naam
- lokaal IP-adres of hostnaam
- rol `Totale opwekking`

De integratie leest lokaal:

```text
http://<homewizard-ip>/api/v1/data
```

Gebruik bij voorkeur een HomeWizard kWh-meter of Energy Socket die echt de zonnepanelen/opwek meet. De integratie leest `active_power_w` en, indien aanwezig, `active_power_l1_w`, `active_power_l2_w` en `active_power_l3_w`.

### Smart Plug

Per Smart Plug vul je in:

- naam
- serienummer
- welke batterij ermee geladen wordt
- aan-command-template
- uit-command-template

De strategie zet Smart Plugs aan zodra de gecorrigeerde opwek boven de ingestelde zonnedrempel komt. Daarmee kun je bijvoorbeeld een Delta Pro automatisch laten laden bij zonneschijn.

## Opwekcorrectie voor PowerStream

Als een of twee PowerStreams terugleveren, kan een totaalmeting lijken alsof er meer zon is dan er werkelijk is. Dat kan een foutieve lus veroorzaken:

1. PowerStream levert bijvoorbeeld `600 W` terug.
2. De totaalmeting ziet extra teruglevering.
3. De laadlogica denkt dat de zon schijnt.
4. De Smart Plug wordt aangezet en de Delta Pro begint te laden.

Daarom rekent de integratie met:

```text
gecorrigeerde opwek = HomeWizard opwek ruw - door deze app aangestuurde PowerStream-teruglevering
```

Voorbeeld:

```text
HomeWizard opwek ruw: 1400 W
PowerStream 1: 600 W
PowerStream 2: 600 W
Gecorrigeerde opwek: 200 W
```

De Smart Plug-laaddrempel gebruikt deze gecorrigeerde waarde, niet de ruwe meting. Per PowerStream kun je ook een fase kiezen, zodat fasecorrectie later zichtbaar en uitbreidbaar blijft.

## Controlpanel

Gebruik het voorbeeld:

[dashboards/ecoflow-energy-control.yaml](dashboards/ecoflow-energy-control.yaml)

Het dashboard toont de EcoFlow-apparaten nu grafischer:

- batterijlading per Delta als gauge
- laadvermogen per Delta
- ontlaadvermogen per Delta
- netto vermogen per Delta, negatief is laden en positief is ontladen
- PowerStream vermogen per apparaat
- PowerStream status, zoals `terugleveren` of `stand-by`
- Quatt/EPEX prijzen van nu tot en met het einde van morgen
- laagste en hoogste uurprijs in dezelfde prijsgrafiek

Voor de prijsgrafiek gebruikt het voorbeeld-dashboard `custom:apexcharts-card`. Installeer die kaart via HACS Frontend als je hem nog niet hebt. Zonder die kaart blijven de prijs-sensoren wel werken, maar de grafiekkaart wordt niet getoond.

Na deze update moet Home Assistant opnieuw worden gestart, omdat er nieuwe sensoren per batterij, per PowerStream en voor de prijsplanning worden aangemaakt.

De dashboard-entiteiten gebruiken nu de `_applicatie` naam, bijvoorbeeld:

```yaml
sensor.ecoflow_energy_control_applicatie_stroomprijs_nu
select.ecoflow_energy_control_applicatie_strategie
number.ecoflow_energy_control_applicatie_laadstekkers_aan_vanaf_gecorrigeerde_zon
sensor.ecoflow_energy_control_applicatie_homewizard_opwek_ruw
sensor.ecoflow_energy_control_applicatie_powerstream_teruglevering
sensor.ecoflow_energy_control_applicatie_opwek_gecorrigeerd
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
- voldoende gecorrigeerde zon: Smart Plugs aan om ingestelde Delta Pro's te laden

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

## Eenvoudiger update-pad

Als je via GitHub en HACS werkt:

1. Upload alleen de gewijzigde bestanden naar GitHub via **Add file > Upload files** of sleep de hele inhoud van de projectmap opnieuw naar GitHub.
2. Commit de wijziging op GitHub.
3. Ga in Home Assistant naar **HACS > EcoFlow Energy Control**.
4. Klik op de drie puntjes.
5. Kies **Redownload** of **Update information** en daarna installeren/downloaden.
6. Herstart Home Assistant.

Als HACS de update niet meteen ziet, verhoog dan de versie in:

```text
custom_components/ecoflow_energy_control/manifest.json
```

Deze iteratie staat op versie `0.4.7`.

### Config flow could not be loaded

Vanaf `0.4.6` laadt de configuratieflow externe API-helpers pas wanneer je de bijbehorende stap gebruikt. Dit voorkomt dat een ontbrekend helperbestand of API-module de hele integratiehandler blokkeert.

Blijft Home Assistant toch melden `Invalid handler specified`, open dan:

```text
Instellingen > Systeem > Logs
```

Zoek op:

```text
custom_components.ecoflow_energy_control.config_flow
```

De eerste Python foutregel daaronder is de oorzaak.

### Entiteiten blijven unavailable

Vanaf versie `0.4.1` maakt een fout in een losse bron niet meer alle entiteiten unavailable. Controleer dan deze entiteit:

```text
sensor.ecoflow_energy_control_applicatie_status
```

De attributen van deze sensor tonen welke bron faalt, bijvoorbeeld `prices`, `homewizard_<ip>`, `sma_<device_id>` of `battery_<serial>`.
