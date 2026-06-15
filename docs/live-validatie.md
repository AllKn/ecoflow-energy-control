# Live-validatie in Home Assistant

Gebruik deze checklist na een HACS-update, herstart of configuratiewijziging. Het doel is niet alleen zien dat de integratie geladen is, maar bewijzen dat EEC app live data gebruikt en alleen stuurt wanneer de basis klopt.

## Snel oordeel

Open het hoofd-dashboard:

```text
dashboards/ecoflow-energy-control.yaml
```

Gebruik in Home Assistant de dashboardroute van het geimporteerde dashboard. Bij de standaard sidebarnaam `Ecoflow App dashboard` is dat:

```text
/ecoflow-app-dashboard/ecoflow-energy
```

Als `/lovelace/ecoflow-energy` op `Overview` uitkomt, gebruik je een oud of verkeerd pad.

Vanaf versie `0.5.255` levert EEC app nog maar één primaire dagelijkse route mee: `Main`. PowerStream-, scenario-, weer- en diagnoseblokken staan lager op die hoofdroute en worden verborgen als er geen passende entiteiten zijn. Vanaf `0.5.284` en `0.5.285` zijn er daarnaast aparte views `Simulatie` en `Energy`, maar die zijn aanvullend en niet nodig voor de normale dagelijkse bediening.

De setup is live bruikbaar als deze punten kloppen:

- **Controle > Setup** vraagt voor basisinzicht alleen om een batterij; `Main` toont of EnergyZero als standaard prijsbron is gebruikt.
- **Flow** toont `Main` als compacte hoofdregel en `Inzicht` als `basis klaar` of beter.
- **Stap** noemt een concrete volgende actie, of geeft aan dat `Advies` gestart kan worden.
- **Basis** toont waarden voor `P1 W`, `Netto W`, `Accu`, `kWh`, `EUR/kWh`, `Terug W` en zonverwachting zonder `unknown` of `unavailable`.
- **Scenario - uitvoering** toont een beste scenario, plan in gewone taal, eventuele blokkade, match met je keuze, uitvoerbaarheid, adviesvermogen en `EUR/u`.
- **Controle > Bewijs** toont databewijs en stuur-bewijs, bijvoorbeeld `6/6 data, sturing klaar` of `6/6 data, sturing gedeeltelijk`.
- **Controle > YAML** toont dezelfde versie als de integratie. Ontbreekt deze tegel, dan is de integratie wel bijgewerkt maar de Lovelace-dashboardconfig nog oud.
- Open in dat geval de attributen van **Controle > Versie**. Daar staan `dashboard_yaml_version`, `dashboard_yaml_marker`, `dashboard_file`, `dashboard_path` en een `dashboard_update_hint`.
- In de ruwe dashboardconfig staat bovenaan `EEC app dashboard yaml version`. Die versie moet gelijk zijn aan de integratieversie.
- Toont **Versie** nog een lager nummer dan de README of `manifest.json`, dan draait Home Assistant nog de vorige HACS-download. Publiceer eerst de nieuwe commit op GitHub, laat HACS opnieuw updaten en herstart daarna Home Assistant.
- Voor publicatie kun je lokaal `python3 tools/release_check.py` uitvoeren. Die check noemt ook welke versie je daarna in Home Assistant bij **Versie** en **YAML** hoort te zien.
- Na `python3 tools/release_check.py` publiceer je de commit gewoon via je normale GitHub-flow (commit/push). HACS pakt die versie daarna op bij de volgende update.
- **Datacheck** heeft geen rode blokkade voor prijzen, batterijen, PowerStreams, P1/netmeter, zon, weer, scenario's of sturing.
- **Scenario hulp** staat pas na `Datacheck` en is naslag; de echte keuze voor scenario en testmodus staat bovenin `Flow`.
- **Handmatig - tools** staat helemaal onderaan en wordt alleen gebruikt voor diagnose, API-checks of bewust handmatig testen.

Lege secundaire kaarten mogen wegblijven. Bij minimale setup is het juist goed als optionele blokken zoals `P1 historie`, PowerStream-details of extra diagnose pas verschijnen wanneer daar entiteiten voor zijn.

Ook grafieken mogen wegblijven wanneer hun bron nog `unknown` of `unavailable` is. Zodra prijs- en weerdata binnenkomen, verschijnen de uurprijs- en weergrafieken vanzelf. Datacheck hoort prijs- en weeruurdata tegelijk te bewaken, zodat een verborgen grafiek altijd een zichtbare oorzaak heeft.

Als de browserconsole bij de grafieken `Identifier 'end' has already been declared` meldt, draait nog een dashboard-YAML van voor versie `0.5.257`.

## Flow

De bovenste Flow-strip is de eerste gebruikersroute.

De status-, scenario- en testmoduskaarten zijn bewust `tile`-kaarten: grotere klikvlakken, duidelijke iconen en minder tekstuele lijstweergave. `EUR/u` blijft een gauge en `Advies` blijft een knop.

- `Main`: combineert status, volgende stap, energiebeeld, scenario en live-bewijs.
- `Inzicht`: toont de gebruikersfase, van `basis nodig` tot `sturing klaar`.
- `Live`: bewijst of basisdata live is, volledige sturing klaar is, of alleen optimalisatie ontbreekt.
- `Stroom`: combineert netverbruik of levering, accu en PowerStream-teruglevering.
- `Flow-hints`: als een kaart niet meteen duidelijk is, controleer eerst de korte toelichttekst boven de kaartgroepen.
- `Nu`: vertelt of EEC app mag sturen, wacht, testmodus gebruikt of geblokkeerd is.
- `Stap`: toont de ene meest logische gebruikersactie en gebruikt dezelfde eerste ontbrekende live-bron als `Live` wanneer data of sturing blokkeert.
- `Scenario`: toont de gekozen strategie.
- `Test`: moet bewust aan staan tijdens testen en uit staan voor echte sturing.
- `Advies`: start het beste scenario alleen als de stuurvoorwaarden kloppen.

Als `Stap` steeds om dezelfde bron vraagt, open dan `Datacheck` en de bijbehorende apparaatstatus.

## Basis

Deze kaart moet de kernmetingen tonen waarop de strategie rust.

- `P1 W`: actuele netmeterwaarde. Positief is verbruik van net, negatief is levering aan net.
- `Netto W`: gecorrigeerde opwek of verbruik. PowerStream-teruglevering wordt hiervan afgetrokken, zodat accu-teruglevering niet als zon wordt gezien.
- `Accu`: gewogen batterijpercentage van toegevoegde Delta Pro/Delta Pro 3 batterijen.
- `kWh`: beschikbare energie in de batterijen, inclusief extra batterij als die bekend of als fallback-capaciteit ingesteld is.
- `EUR/kWh`: actuele stroomprijs inclusief ingestelde Quatt-opslag.
- `Terug W`: actuele totale PowerStream-teruglevering.

Een lege of nulwaarde is alleen goed als dat fysiek klopt. Bij verbruik van 8 kW moet `P1 W` dus ook rond 8000 W liggen en niet rond 800 W.

Dag-, week- en maandtotalen van de P1-meter staan bewust in `P1 historie` onder de datacheck; `Basis` blijft gericht op live waarden die direct invloed hebben op het actuele scenario.

## Scenario - uitvoering

Deze kaart bewijst of de app de gemeten situatie kan vertalen naar een actie.

- `Overzicht`: de korte planregel; bij afwijking zie je jouw gekozen actie naast het beste advies.
- `Plan`: het gekozen of beste plan in gewone taal, inclusief blokkade als het niet uitvoerbaar is.
- `Meting`: of prijs, accu, P1/netmeter, zon en PowerStream-data genoeg zijn.
- `Zeker`: korte reden voor de betrouwbaarheid van het advies.
- `Volgende`: de concrete actie, bijvoorbeeld laden, ontladen, wachten of vasthouden.
- `EUR/u`: geschatte waarde van de huidige actie.

Als deze kaart `data nodig` toont, is het dashboard niet klaar voor automatische sturing.

## Controle

Gebruik deze kaart als compact bewijsblok.

- `Score`: totale datakwaliteit.
- `Klaar`: oordeel of de setup alleen inzicht geeft, in testmodus staat of echt kan sturen.
- `Bronnen`: eerste ontbrekende of beperkte bron met gewone labels zoals `prijzen`, `weer` of `sturing`.
- `Aandacht`: eerste blokkade, optimalisatiepunt of waarschuwing; bij een groene setup staat hier `alles ok`.
- `Bewijs`: samenvatting van live databronnen en stuurstatus.
- `first_missing_label` en `first_missing_message`: eerste bron die live bewijs of sturing nog beperkt.
- `Fase`: setup, simuleren, sturen, wachten, uit of fout.

`Bewijs` is de belangrijkste regel na een update. `data klaar` zonder `sturing klaar` betekent dat het dashboard informatief is, maar dat automatische PowerStream-sturing nog niet volledig bewezen is.

## Scenario hulp

Deze kaart is naslag, geen tweede bedieningspaneel.

- Scenario en testmodus worden bovenin `Flow` gekozen.
- `Scenario hulp` legt alleen uit wanneer `Eigen gebruik`, `Handelen`, `Buffer 50%` of `Uit` logisch is.
- Als je de strategie wilt wijzigen, doe dat in `Flow`; gebruik deze kaart alleen om de keuze te begrijpen.

## Datacheck

De Datacheck toont de ruwe status per bron als tegels.

- `Prijzen`: uurprijzen moeten vandaag en morgen bevatten.
- `Batterijen`: elke batterij moet live SoC hebben.
- `PowerStreams`: elke PowerStream moet gekoppeld zijn aan een batterij en actuele of bruikbare fallback-data hebben.
- `Zon`: HomeWizard-opwek moet gecorrigeerd zijn voor PowerStream-teruglevering.
- `P1 historie`: mag waarschuwing geven als Home Assistant nog onvoldoende statistiek heeft, maar live sturing gebruikt de actuele P1-waarde.
- `Weer`: moet uren vooruit bevatten voor zonverwachting.
- `Scenario's`: moet meerdere scenario's kunnen doorrekenen.
- `Sturing`: moet testmodus, laatste commando, laatste fout en commandowachttijd verklaren.

## EcoFlow bewijs

Open per EcoFlow-apparaat de `API status` sensor.

Een batterij is bewezen als:

- `api_connected` waar is.
- `telemetry_fields` groter dan 0 is.
- `soc` of `selected_soc` klopt met de EcoFlow app.
- `charge_w`, `discharge_w` en `net_w` logisch veranderen bij laden of ontladen.
- `error` leeg is.

Een PowerStream is bewezen als:

- `api_connected` waar is.
- de PowerStream als PowerStream is getypeerd en aan de juiste batterij is gekoppeld.
- het actuele vermogen in watt klopt en niet factor 10 te hoog is.
- een sliderwijziging in testmodus als laatste commando zichtbaar wordt.
- een echte sliderwijziging buiten testmodus geen EcoFlow-fout teruggeeft.

## HomeWizard bewijs

Voor P1/netmeter moet de geïmporteerde HomeWizard-bron echt de P1-meter zijn, niet een losse zonmeter of socket.

- Bij normaal verbruik toont EEC app `verbruik van net`.
- Bij negatieve P1-waarde toont EEC app `levering aan net`.
- Grote verbruikspieken blijven groot; een 8 kW verbruik hoort rond 8000 W te staan.
- HomeWizard-zon wordt gecorrigeerd met PowerStream-output, zodat teruglevering uit batterijen niet als zon wordt geteld.

Historie komt niet uit een publieke HomeWizard Energy+ cloud API. EEC app gebruikt Home Assistant statistics voor geïmporteerde P1-meters.

## Sturing bewijzen

Test eerst veilig:

1. Zet `Test` aan.
2. Verander een PowerStream-slider of druk `Advies`.
3. Controleer dat `Laatste sturing` en `Sturing` het commando tonen zonder echte aanpassing.
4. Zet `Test` uit.
5. Herhaal één wijziging en controleer dat de PowerStream-uitgang zichtbaar meebeweegt.

Automatische strategiecommando's worden maximaal eens per 10 minuten verstuurd. Als `Nu` of `Sturing` wacht meldt, controleer dan de resterende wachttijd voordat je opnieuw test.

`Handmatig - tools` staat bewust onderaan het dashboard. Gebruik deze knoppen alleen als je gericht wilt testen of diagnose wilt doen; de normale route loopt via `Flow > Advies`.

## Klaar voor live sturen

EEC app is klaar voor live sturing als:

- `Flow` geen blokkerende stap meer toont.
- `Basis` actuele waarden zonder lege kernvelden toont.
- `Scenario - nu` een uitvoerbare actie toont.
- `Waarom` de startreden en eventuele uitvoerplanblokkade verklaart zonder dubbele scenariowaarden.
- `Controle > Bewijs` databronnen en sturing als klaar of bewust testmodus toont.
- `Datacheck` geen blokkade voor prijzen, batterijen, PowerStreams of P1/netmeter toont.
- Testmodus bewust uit staat.
- `Handmatig - tools` niet nodig is voor normale bediening.
- De eerste echte PowerStream-aanpassing zichtbaar is in Home Assistant en in de EcoFlow app.
