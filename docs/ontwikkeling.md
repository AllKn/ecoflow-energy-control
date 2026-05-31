# Ontwikkeling van EEC app

Dit document is bedoeld als naslag voor gebruikers die willen begrijpen hoe EEC app is gegroeid: van een lokale Home Assistant-integratie voor EcoFlow en prijzen naar een dashboard dat apparaten, tarieven, zon, netverbruik en scenario's samenbrengt.

De korte presentatie bij dit document staat in `docs/eec-app-ontwikkeling.pptx`. De bewerkbare slidebron staat in `docs/presentation-src/`. Houd deze presentatie bij bij functionele iteraties, zodat nieuwe gebruikers in een paar minuten de ontwikkellijn kunnen volgen.

## Uitgangspunt

De eerste vraag was praktisch: stuur EcoFlow Delta Pro, Delta Pro 3 en PowerStreams lokaal vanuit Home Assistant, gebruik spotprijzen, meet zonopwek en maak de bediening grafisch begrijpelijk. De belangrijkste ontwerpkeuze is sindsdien gelijk gebleven: Home Assistant blijft het lokale middelpunt, de app toont diagnose waar data ontbreekt, en sturing begint voorzichtig in testmodus.

## Iteraties

### 1. HACS en installatiebasis

De app is opgezet als Home Assistant custom integration onder `custom_components/ecoflow_energy_control`, met manifest, config flow, services, vertalingen en dashboards. Vroege iteraties losten HACS-structuurproblemen op, zoals ontbrekende `manifest.json` en een verkeerde integratiemap.

### 2. EcoFlow Cloud API en device-import

Daarna lag de nadruk op EcoFlow-authenticatie, signing en quota-uitlezing. De app kreeg een API-check, een importflow voor gevonden EcoFlow-devices en debug-attributen zoals quota source, response debug en telemetrievelden. Dit maakte zichtbaar wanneer device-list wel werkte, maar device quota's faalden door bijvoorbeeld `8521 signature is wrong`.

### 3. Persistente apparaten en korte labels

Toegevoegde EcoFlow-, PowerStream- en HomeWizard-apparaten worden persistent opgeslagen en krijgen Home Assistant-devices onder de integratie. Lange labels zijn vervangen door korte rolteksten, terwijl per apparaat een vriendelijke naam kan worden ingesteld. Dashboards gebruiken discovery-attributen in plaats van vaste entity_id's, zodat hernoemen en updates minder breekbaar zijn.

### 4. Batterij- en PowerStream-telemetrie

Voor Delta Pro en Delta Pro 3 is de SoC-herkenning uitgebreid met meerdere mogelijke EcoFlow-velden. Delta Pro 3 gebruikt hoofdaccu en extra accu als aparte attributen waar mogelijk. Batterijvermogen is gesplitst in laden, ontladen, netto vermogen en laadbron, zodat DC-bijladen vanuit een extra batterij niet als net- of zonne-laden wordt gepresenteerd. PowerStream-output is beschermd tegen factor-10 fouten en kan via sliders worden ingesteld.

### 5. Prijzen en Quatt-opslag

EnergyZero is de standaard prijsbron geworden. Daarnaast zijn EPEX-bronnen toegevoegd, inclusief de Quatt-specifieke opslag van `0.015 EUR/kWh`. De app haalt prijsdata dagelijks en doorlopend op, toont actuele, goedkope en dure grenzen, en gebruikt deze grenzen voor scenarioadvies.

### 6. HomeWizard, P1 en netto zon

HomeWizard kan direct via lokale API worden gelezen of via de bestaande Home Assistant HomeWizard-integratie worden geimporteerd. Er is een expliciete rolkeuze toegevoegd: `Totale opwekking` of `P1/netmeter`. P1-netmeterwaarden worden niet meer door de factor-10 bescherming gedeeld, zodat 8 kW verbruik ook als 8 kW zichtbaar blijft.

Omdat PowerStreams terugleveren via dezelfde meting waarop zon zichtbaar kan zijn, corrigeert EEC app de zonopwek met de actuele PowerStream-output. Zo voorkomt de app dat batterijteruglevering ten onrechte wordt gezien als zon en dat de batterijen zichzelf daardoor gaan laden.

### 7. HomeWizard geschiedenis

De officiele HomeWizard lokale API levert actuele metingen, geen historie. HomeWizard meldt dat app-grafieken in de HomeWizard-cloud staan, maar er is geen openbare, gedocumenteerde Energy+ Cloud API voor historische P1-data. Ook met betaalde HomeWizard-geschiedenis is er dus geen ondersteunde cloudroute die EEC app veilig kan gebruiken. Daarom gebruikt EEC app de ondersteunde lokale route: als een P1-meter via de Home Assistant HomeWizard-integratie is geimporteerd, leest EEC app dag-, week- en maandtotalen uit Home Assistant statistics/recorder.

Deze historie is bedoeld voor inzicht en scenariovergelijking. Voor live-sturing blijft de actuele P1-waarde leidend.

### 8. Weer en zonverwachting

De app ondersteunt Nederlandse steden voor zonverwachting via Open-Meteo. Het dashboard toont nu, 4 uur, 12 uur en 24 uur vooruit, met grafische weerpresentatie. Die verwachting voedt de geschatte opbrengst en de scenario-inschatting.

### 9. Scenario's en simulatie

De scenario's zijn teruggebracht tot logische gebruikerskeuzes:

- `Eigen gebruik`: laad bij zon of lage prijs, ontlaad om dure netstroom te vermijden.
- `Handelen`: gebruik prijsverschillen actiever; laad goedkoop en lever terug op dure momenten.
- `Buffer 50%`: bewaak altijd een minimale batterijreserve.
- `Uit`: stuur niet automatisch en zet PowerStreams naar 0 W.

Scenario's worden live gesimuleerd met prijs, netto zon, P1/netmeter, batterijinhoud en PowerStream-status. Het dashboard toont effect in W, kWh en EUR per uur en per dag/week/maand. Automatische PowerStream-aanpassingen zijn begrensd tot maximaal eens per 10 minuten, zodat het systeem niet onnodig gaat pendelen.

Vanaf versie `0.5.173` staat dezelfde uitleg als korte `Strategie hulp` in het hoofd-dashboard bij `Keuze wijzigen`. Daarmee kan een gebruiker de juiste scenariokeuze maken zonder documentatie of technische attributen te openen.

Vanaf versie `0.5.215` heet die kaart kortweg `Keuze`. De inhoud blijft scenario, testmodus en strategiehulp, maar de titel past beter bij de eenvoudige hoofdflow.

Vanaf versie `0.5.174` heet de actieve prijsstrategie overal `Handelen`. De oude term `Terugleveren` blijft intern als alias werken, maar verdwijnt uit de normale keuzeflow om verwarring met puur terugleververmogen te voorkomen.

### 10. Hoofd-dashboard

Het hoofd-dashboard is de primaire gebruikersflow geworden. Bovenaan staan data-score, automatische status, zekerheid, stroom, startstatus, scenario, testmodus en advies. Daaronder volgen basiswaarden zoals netto opwek/verbruik, P1-status, P1-vermogen, accu-inhoud, batterij in/uit/netto, prijs, weer en uitvoerbaarheid. Voor normaal gebruik is alleen dit dashboard nodig; detaildashboards blijven bestaan voor PowerStreams, scenario's en app-stijltests.

Vanaf versie `0.5.175` zijn de benodigde Lovelace frontend-kaarten vastgelegd in `dashboards/frontend-requirements.yaml`. Dit maakt dashboardproblemen door ontbrekende HACS-kaarten, zoals `Custom element doesn't exist`, sneller herkenbaar en testbaar.

Vanaf versie `0.5.176` staat P1-historie ook in de Datacheck. Als Home Assistant nog geen bruikbare dag-, week- of maandstatistiek heeft voor de geimporteerde P1-meter, wordt dat zichtbaar als waarschuwing in plaats van als lege waarde zonder uitleg.

Vanaf versie `0.5.177` toont de Gereedheid-kaart ook een `Setup %` gauge. Die maakt de minimale basissetup zichtbaar: batterij en prijsbron wegen als noodzakelijk, PowerStream, zonmeter en weerstad als optimalisatie voor betere sturing.

Vanaf versie `0.5.178` is de berekening achter `Setup %` als pure helper getest. Daardoor blijft de simpele setupflow controleerbaar zonder Home Assistant-runtime.

Vanaf versie `0.5.179` staat in de bovenste flow een compacte `Stroom`-tegel. Die combineert netverbruik of levering, accustatus en PowerStream-teruglevering, zodat de gebruiker niet eerst losse P1-, accu- en PowerStream-kaarten hoeft te vergelijken om te zien wat er nu gebeurt.

Vanaf versie `0.5.180` krijgt elk scenario een eigen uitvoerbaarheidsoordeel. Het hoofd-dashboard toont daardoor niet alleen de actie en reden, maar ook of een scenario nu echt kan starten, moet wachten of eerst data nodig heeft.

Vanaf versie `0.5.181` is de bovenste Flow-strip meer gericht op handelen. De gebruiker ziet daar nu `Start` in plaats van `Probleem`; de detaildiagnose blijft lager op het dashboard staan, maar de eerste blik beantwoordt direct of het systeem kan starten.

Vanaf versie `0.5.182` worden de documentatie- en presentatiebestanden strenger bewaakt. Tests controleren dat deze ontwikkelgeschiedenis de actuele versie noemt, dat de korte presentatie en slidebronnen aanwezig zijn en dat tijdelijke buildbestanden niet in de repo blijven staan.

Vanaf versie `0.5.183` is het hoofd-dashboard-contract expliciet getest. `dashboards/ecoflow-energy-control.yaml` is de enige primaire route met `path: ecoflow-energy`; optionele dashboards mogen die route niet claimen.

Vanaf versie `0.5.184` staat bovenin de Flow-strip een compacte `Nu`-tegel. Die geeft in een enkele status aan of sturing mag starten, in testmodus draait, geblokkeerd is, afwijkt van het beste advies of wacht op data. Daarmee hoeft de gebruiker minder losse tegels te combineren om te begrijpen wat de app nu gaat doen.

Vanaf versie `0.5.185` is de setupflow verder vereenvoudigd. De app maakt expliciet onderscheid tussen `basisinzicht klaar`, `PowerStream-sturing klaar` en `volledige optimalisatie klaar`. In het hoofd-dashboard staat dit als setupadvies, zodat een gebruiker met minimale instellingen al weet wat werkt en welke ene stap de meeste waarde toevoegt.

Vanaf versie `0.5.186` is de scenarioflow compacter. De kaart `Scenario - nu` toont een `Overzicht` dat het beste scenario, de gekozen strategie, uitvoerbaarheid, vermogen en euro-effect in een enkele statusregel combineert.

Vanaf versie `0.5.187` is de eerste Flow-strip informatiever zonder groter te worden. De losse `Auto`-tegel is bovenin vervangen door `Kort`, een samenvatting van data, scenario, opslag, prijs, zon en volgende actie. `Auto` staat nog steeds in het adviesdetail voor diagnose.

Vanaf versie `0.5.188` is ook de eerste installatie nog eenvoudiger. De initiële config flow vraagt alleen om EcoFlow access key en secret key; de naam `EEC app`, prijsbron, Quatt-opslag, weerstad en testmodus krijgen veilige defaults die later via Configureren aanpasbaar blijven.

Vanaf versie `0.5.189` verklaart de `Nu`-tegel ook de commandobeveiliging. Attributen tonen het minimuminterval voor PowerStream-aanpassingen, de eerste wachtende PowerStream, resterende wachttijd en eventuele commandofout. Zo blijft de hoofdflow simpel, maar is het bewijs achter wachten of sturen direct beschikbaar.

Vanaf versie `0.5.190` maakt de app onderscheid tussen basisinzicht en volledige sturing. De Gereedheid-kaart toont `Inzicht`, gebaseerd op prijsdata en batterij-SoC. Daardoor kan het dashboard al nuttige informatie geven met minimale instellingen, terwijl PowerStream-sturing, zonmeter, weer en testmodus apart als optimalisatie of stuurvoorwaarde zichtbaar blijven.

Vanaf versie `0.5.191` staat dit basisinzicht ook als eerste signaal in de Flow-strip. `Data`/score blijft beschikbaar in `Gereedheid`, maar bovenaan ziet de gebruiker eerst of prijsdata en batterij-SoC voldoende zijn voor bruikbare kerninformatie.

Vanaf versie `0.5.192` toont de eerste Flow-strip ook duidelijker in welke fase de app zit. `Start` is daar vervangen door `Fase`: setup, simuleren, sturen, wachten, uit of fout. De startstatus blijft in het adviesdetail staan voor wie de reden wil zien.

Vanaf versie `0.5.193` wordt de eerste Flow-strip als contract getest. De volgorde van de tien tegels is vastgelegd: Inzicht, Kort, Zeker, Stroom, Nu, EUR/u, Fase, Scenario, Test en Advies. Daarmee blijft de hoofdflow bij latere wijzigingen gericht op snelle basisinformatie en uitvoerbare sturing.

Vanaf versie `0.5.194` is de compacte `Kort`-samenvatting vriendelijker voor minimale setups. Als basisinzicht klaar is maar optionele bronnen of stuurvoorwaarden nog ontbreken, toont de samenvatting `basis klaar` en noemt alleen de volgende optimalisatiestap. Daardoor voelt een werkende basissetup niet onterecht als een fout.

Vanaf versie `0.5.195` maakt `Kort` het verschil tussen inzicht en sturing expliciet. Bij minimale data blijft de samenvatting `basis klaar`; bij een complete stuursetup wordt dat `sturing klaar`, inclusief prijscontext, netto zon/verbruik en het resterende stuurverschil. Daarmee is de bovenste flow beter leesbaar zonder extra tegels.

Vanaf versie `0.5.196` is `Volgende stap` geen losse datacheck meer, maar een samengestelde gebruikersstap. De app weegt setup, live data, testmodus, scenariokeuze en uitvoerbaarheid en toont de ene actie die nu het meeste helpt: basis aanvullen, PowerStream toevoegen, testmodus uitzetten, keuze volgen of `Advies` starten.

Vanaf versie `0.5.197` staat die samengestelde gebruikersstap ook in de bovenste Flow-strip. `Fase` blijft beschikbaar als diagnoseveld, maar de primaire rij toont `Stap`, zodat de gebruiker direct de volgende handeling ziet zonder lager in `Gereedheid` te hoeven kijken.

Vanaf versie `0.5.198` is die scheiding ook in de dashboardindeling doorgevoerd. De dubbele `Volgende stap` is uit `Gereedheid` gehaald; daar staat nu `Fase` als diagnose. De bovenste flow blijft voor de eerste actie, de lagere gereedheidskaart voor bewijs en oorzaak.

Vanaf versie `0.5.199` is ook de dubbele `Inzicht`-tegel uit `Gereedheid` verwijderd. `Inzicht` blijft bovenaan het eerste signaal; `Gereedheid` blijft een diagnosekaart voor setup, bronnen, probleem, bewijs, score en fase.

Vanaf versie `0.5.200` is de advies-taal scherper. `Advies` is alleen nog de primaire actieknop bovenaan. De setuptegel heet `Setup advies` en de detailkaart heet `Uitleg`, zodat actie, inrichting en toelichting niet door elkaar lopen.

Vanaf versie `0.5.201` is `Gereedheid` nog compacter. De ruwe dashboardstatus is uit de kaart gehaald; score, klaar-status, bronnen, probleem, bewijs en fase blijven over als de zichtbare diagnose.

Vanaf versie `0.5.202` is `Uitleg` ontdubbeld ten opzichte van `Scenario - nu`. De scenariokaart blijft de plek voor keuze, meting, zekerheid, volgende actie en uitvoerbaarheid. `Uitleg` focust op de verklaring achter starten, auto-status, uitvoerplan, dagwaarde en laatste sturing.

Vanaf versie `0.5.203` is de detailvolgorde aangepast. Na `Gereedheid` komt eerst `Uitleg`, daarna pas `Datacheck`. Daardoor ziet de gebruiker eerst de gewone verklaring en alleen daarna de ruwe bronchecks.

Vanaf versie `0.5.204` zijn de lagere detailblokken minder dubbel. `Basis` blijft de plek voor actuele netto waarden, prijs en accu. De oude `Nu`-kaart is versmald naar `Prijsgrenzen`, en `Opslag totaal` is versmald naar `Opslag waarde` met vrije ruimte en euro-waarde.

Vanaf versie `0.5.205` is live-validatie expliciet gemaakt in `docs/live-validatie.md`. Die checklist beschrijft per hoofdkaart welk bewijs nodig is in Home Assistant: Flow, Basis, Scenario - nu, Gereedheid, Datacheck, EcoFlow, HomeWizard en echte PowerStream-sturing.

Vanaf versie `0.5.206` staat live-validatie ook bovenaan in de Flow-strip. De tegel `Live` vervangt daar de dubbele zekerheidsgauge en toont direct `live klaar`, `testmodus`, `sturing beperkt`, `data nodig`, `actie nodig` of `geen bewijs`.

Vanaf versie `0.5.207` is de eerste Flow-tegel `Inzicht` niet meer alleen een technische prijs-plus-accu-check. De tegel benoemt nu de gebruikersfase: basis nodig, data nodig, inzicht klaar, sturing beperkt, testmodus, startbaar, optimaliseren of sturing klaar.

Vanaf versie `0.5.208` werkt `Scenario - nu > Overzicht` meer als een compact strategieplan. De zichtbare regel vergelijkt bij afwijking jouw gekozen scenario met het beste advies, en de attributen tonen het gekozen plan, het beste plan, reden, vermogen en EUR/u.

Vanaf versie `0.5.209` maakt `Live` expliciet verschil tussen basisbewijs en volledige sturing. Een minimale setup met prijsdata en batterij-SoC kan nu `basis live` tonen, terwijl ontbrekende PowerStreams, zon of weer als optimalisatie zichtbaar blijven.

Vanaf versie `0.5.210` gebruikt de `Bronnen`-tegel gewone bronlabels in plaats van interne keys. Daardoor leest een waarschuwing als `prijzen: geen actuele prijs` of `weer: geen uurverwachting`, zonder dat de gebruiker technische checknamen hoeft te kennen.

Vanaf versie `0.5.211` klinkt de `Probleem`-tegel minder streng bij minimale setups. Als basisinzicht werkt en alleen aanbevolen bronnen ontbreken, toont de app `optimalisatie` in plaats van `let op`, zodat de gebruiker ziet dat de basis werkt.

Vanaf versie `0.5.212` heet die zichtbare tegel `Aandacht`. De onderliggende technische rol blijft `dashboard_problem`, zodat bestaande dashboards compatible blijven, maar de hoofdflow gebruikt een vriendelijker label.

Vanaf versie `0.5.213` gebruikt `Aandacht` ook bij volledig groene status positieve taal. De tegel toont dan `alles ok` in plaats van `geen probleem`, zodat de hoofdflow minder foutgericht leest.

Vanaf versie `0.5.214` heet de zichtbare kaart `Gereedheid` voortaan `Controle`. De kaart bevat setup, bronnen, aandacht, bewijs, score en fase; de nieuwe titel past beter bij die bredere diagnosefunctie.

Vanaf versie `0.5.215` heet de kaart `Keuze wijzigen` voortaan `Keuze`. Daarmee leest het hoofd-dashboard minder als een formulier en meer als een compact bedieningspaneel.

Vanaf versie `0.5.216` heet de batterijkaart `Accu's - in/uit` en toont die per batterij ook de laadbron. Daardoor staan actuele input, output, netto vermogen, batterijstatus en laadherkomst bij elkaar zonder extra detaildashboard.

Vanaf versie `0.5.217` toont `Scenario - nu` ook `Plan`. Deze tegel haalt het gekozen of beste scenarioplan uit de attributen naar de kaart zelf, zodat actie, reden en verwacht EUR/u direct leesbaar zijn.

Vanaf versie `0.5.218` toont `Plan` bij niet-uitvoerbare scenario's ook de zichtbare blokkade. De status `Sturen` heet in de scenariokaart voortaan `Uitvoerbaar`, zodat duidelijker is of het advies echt kan worden toegepast.

Vanaf versie `0.5.219` is `Scenario - nu` compacter. Losse vergelijkingstegels voor beste scenario, match, keuze en gemiste EUR/u zijn vervangen door de combinatie `Overzicht` en `Plan`; de details blijven als attributen beschikbaar voor diagnose.

Vanaf versie `0.5.220` heet de detailkaart `Uitleg` voortaan `Waarom`. Dubbele regels voor flow-overzicht, kort advies en dagwaarde zijn verwijderd, zodat deze kaart alleen nog verklaart waarom de app wel of niet start en wat de sturing doet.

Vanaf versie `0.5.221` heet een minimale maar werkende setup zichtbaar `basis klaar` in plaats van `beperkt`. Batterij plus prijsbron is genoeg voor basisinzicht; PowerStream, zonmeter en weerstad blijven aanbevolen voor sturing en optimalisatie.

Vanaf versie `0.5.222` toont `Controle` geen apart `Setup advies` meer. De bovenste `Stap`-tegel is de enige primaire gebruikersactie; `Controle` blijft bedoeld voor status, score, bronnen, bewijs en fase.

Vanaf versie `0.5.223` zijn de scenariodetailkaarten samengevoegd. `Scenario's - details` toont per scenario actie, uitvoerbaarheid, reden, vermogen, EUR/u en dagwaarde in een compacte grid, terwijl `Scenario - nu` de dagelijkse samenvatting blijft.

Vanaf versie `0.5.224` heet de handmatige actiekaart `Handmatig - tools`. Daarmee blijft duidelijk dat strategie-start, EcoFlow API-check en prijzen ophalen hulpgereedschap zijn, terwijl de dagelijkse route via `Flow`, `Stap` en `Scenario - nu` loopt.

Vanaf versie `0.5.225` is `Basis` weer strakker op live-inzicht gericht. P1-dag-, week- en maandtotalen zijn verplaatst naar `P1 historie`, zodat actuele netstroom, prijs, accu en PowerStream-teruglevering niet mengen met langere totalen.

Vanaf versie `0.5.226` staan `Flow`, `Basis` en `Scenario - nu` weer direct onder elkaar. De actuele beslissing komt daardoor meteen na de live kernmetingen; `P1 historie` blijft op hetzelfde dashboard staan, maar als secundaire context onder het scenario.

Vanaf versie `0.5.227` is de dubbele bediening weggehaald. Scenario en testmodus staan alleen nog in de bovenste `Flow`; de lagere kaart heet `Scenario hulp` en geeft uitleg bij de strategieen zonder opnieuw instellingen te tonen.

Vanaf versie `0.5.228` staat `Scenario hulp` onder `Controle`. De dagelijkse route toont daardoor eerst metingen, scenario, P1-historie en bewijs; uitleg bij de strategieen blijft beschikbaar, maar staat niet meer tussen scenario en statuscontrole.

Vanaf versie `0.5.229` staat `Handmatig - tools` helemaal onderaan het hoofd-dashboard. De knoppen voor handmatige strategie-start, EcoFlow API-check en prijzen ophalen blijven bereikbaar als diagnose- of testgereedschap, maar komen niet meer tussen de gewone meet- en besliskaarten.

Vanaf versie `0.5.230` wordt de dagelijkse dashboardroute expliciet getest. De volgorde van hoofdkaarten is nu een contract: eerst live inzicht en scenario, daarna status en uitleg, dan details, diagnose en helemaal onderaan de handmatige tools.

Vanaf versie `0.5.231` beschrijft de live-validatiechecklist ook de rol van `Scenario hulp` en `Handmatig - tools`. Daarmee is niet alleen de UI eenvoudiger, maar ook het bewijsproces: normale bediening loopt via `Flow`, hulp is naslag en handmatige tools zijn diagnose.

Vanaf versie `0.5.232` staat diezelfde route ook in de README-validatiesamenvatting. Na een update ziet de gebruiker daar meteen dat `Flow > Advies` de normale route is, terwijl `Scenario hulp` naslag is en `Handmatig - tools` alleen diagnose of bewust testen ondersteunt.

Vanaf versie `0.5.233` is de tekst van het eerste configuratiescherm aangescherpt. De gebruiker ziet nu meteen dat alleen EcoFlow Cloud API keys nodig zijn en dat prijzen, weer, testmodus en apparaten later via `Configureren` worden ingesteld.

Vanaf versie `0.5.234` is ook het Configureren-menu duidelijker apparaatgericht. De titel stuurt de gebruiker naar eerst apparaten importeren of toevoegen; basisinstellingen en technische instellingen blijven later in de lijst staan.

Vanaf versie `0.5.235` is de HomeWizard-importtekst aangescherpt. De app stuurt gebruikers naar bestaande Home Assistant HomeWizard-apparaten voor P1/netmeter of opwekbron, in plaats van te suggereren dat dezelfde meter opnieuw lokaal moet worden ingesteld.

Vanaf versie `0.5.236` toont de HomeWizard-importlijst meer bewijs voordat een apparaat wordt opgeslagen. De keuze vermeldt de voorgestelde rol en gevonden meetsoorten, zodat sneller zichtbaar is of je een P1/netmeter, zonmeter of ongeschikte bron selecteert.

Vanaf versie `0.5.237` gebruikt de bovenste `Kort`-tegel dezelfde bronanalyse als `Bronnen` en `Aandacht`. Daardoor ziet de gebruiker bij een gedeeltelijke setup direct welke bron de flow beperkt, zonder eerst naar de lagere diagnosekaarten te gaan.

Vanaf versie `0.5.238` maakt de setupstatus onderscheid tussen wat nodig is voor basisinzicht, wat nodig is voor PowerStream-sturing en wat alleen optimalisatie verbetert. Zo blijft de minimale route klein: batterij plus prijsbron geeft al inzicht; PowerStream, zonmeter en weer maken de flow rijker.

Vanaf versie `0.5.239` staat die capability ook zichtbaar in de `Setup`-tegel op het hoofd-dashboard. De gebruiker hoeft daardoor geen attributen te openen om te zien of de app alleen basisinzicht heeft of ook kan sturen.

Vanaf versie `0.5.240` begint de scenariokaart `Plan` met de actuele uitvoerbaarheid. Daardoor zie je in dezelfde regel niet alleen welk scenario logisch is, maar ook of de app nu echt mag sturen, simuleert, wacht op data of uit staat.

Vanaf versie `0.5.241` is die uitvoerbaarheidstekst lokaal testbaar gemaakt in de policy-laag. Daarmee is niet alleen het dashboardcontract bewaakt, maar ook de beslisregel achter de zichtbare scenarioprefixes.

Vanaf versie `0.5.242` gebruikt ook de aparte `Uitvoerbaar`-tegel dezelfde policy-helper. `Plan` en `Uitvoerbaar` tonen daardoor geen afwijkende termen meer voor dezelfde stuurtoestand.

Vanaf versie `0.5.243` benoemt de live-validatie de eerste ontbrekende bron direct. De bovenste `Live`-tegel en `Controle > Bewijs` laten daardoor sneller zien of bijvoorbeeld prijzen, batterijen, PowerStreams, P1 historie, weer of sturing de volgende verificatiestap is.

Vanaf versie `0.5.244` is die live-bewijs samenvatting als pure health-helper getest. Daarmee wordt de zichtbare melding niet alleen statisch bewaakt, maar ook inhoudelijk gecontroleerd op bronmelding en fallback.

Vanaf versie `0.5.245` gebruikt ook de primaire `Stap`-tegel deze live-bewijscontext. Daardoor wijzen `Live` en `Stap` naar dezelfde eerstvolgende bron als live data of sturing nog blokkeert.

Vanaf versie `0.5.246` staat bovenaan de Flow-strip een `Main`-samenvatting. Die combineert status, stap, energie, scenario en bewijs in een hoofdregel, terwijl de oude losse `Kort`-tegel uit de bovenste route verdwijnt.

Vanaf versie `0.5.247` gebruikt de bovenste Flow-strip ingebouwde Home Assistant `tile`-kaarten voor de status- en keuze-elementen. Daardoor voelt de eerste route meer als een bedienpaneel, zonder extra frontend-afhankelijkheden toe te voegen.

Vanaf versie `0.5.248` is de minimale setup weer een stap kleiner. EnergyZero geldt ook in de setupstatus als standaard prijsbron, waardoor de basisroute alleen nog een batterij hoeft te vragen; live prijsdata blijft daarna via de Datacheck bewezen.

Vanaf versie `0.5.249` is die standaardkeuze ook zichtbaar in het dashboard. `Main` en `Setup advies` laten zien wanneer EnergyZero impliciet is gebruikt, zodat minder instellingen niet voelt als verborgen gedrag.

Vanaf versie `0.5.250` zijn globale EEC-entiteiten bewust korter zichtbaar. De app laat in dashboards labels als `check prijzen`, `testmodus` en `advies starten` zien, terwijl batterij-, PowerStream- en HomeWizard-entiteiten hun ingestelde vriendelijke apparaatnaam blijven gebruiken. Ook is de live route naar het hoofd-dashboard gedocumenteerd, omdat Home Assistant het dashboard via de gekozen sidebarroute opent en oude `/lovelace/...` links naar `Overview` kunnen terugvallen.

Vanaf versie `0.5.251` is de hoofdroute verder aangescherpt. `P1 historie` en `Scenario hulp` staan niet meer tussen de actuele beslissing en het bewijs; de gebruiker ziet eerst live flow, basiswaarden, scenario, controle, uitleg en datacheck. Historie en hulp blijven op hetzelfde dashboard staan, maar als secundaire context.

Vanaf versie `0.5.252` verbergt het hoofd-dashboard lege secundaire kaarten. Daardoor blijft dezelfde ene dashboardroute bruikbaar bij minimale instellingen: ontbrekende optionele bronnen leveren geen lege blokken op, terwijl diagnose en detailcontext vanzelf verschijnen zodra de bijbehorende entiteiten bestaan.

Vanaf versie `0.5.253` geldt dat ook voor de grafische apexcharts-kaarten. De uurprijzen- en weergrafiek worden pas getoond als hun bronentiteiten beschikbaar zijn. Zo blijft de minimale flow visueel rustig, maar blijft de grafische analyse meteen beschikbaar zodra prijs- en weerdata binnenkomen.

Vanaf versie `0.5.254` controleert Datacheck ook of de uurverwachting lang genoeg is om de weergrafiek te vullen. Daardoor verdwijnt een lege grafiek uit beeld, terwijl de gebruiker in Datacheck ziet of weerdata ontbreekt, te kort is of klaar staat.

Vanaf versie `0.5.255` levert de app geen losse PowerStream-, app-stijl- of scenario-dashboards meer mee. De relevante detailblokken blijven op het hoofd-dashboard staan, lager dan de dagelijkse beslisroute, zodat de gebruiker niet meer hoeft te kiezen tussen meerdere dashboards.

Vanaf versie `0.5.256` is Datacheck geen tekstlijst meer maar een grid met tegels. De bronstatus blijft dynamisch op dezelfde readiness-checks gebaseerd, maar is visueel sneller te scannen op het ene hoofd-dashboard.

Vanaf versie `0.5.257` zijn de ApexCharts data-generators aangepast zodat prijs- en weergrafieken geen lokale JavaScript-variabelen meer herdeclareren. Dat voorkomt dat de grafiekkaart leeg blijft door `Identifier 'end' has already been declared`.

Vanaf versie `0.5.258` heeft `Controle` een `YAML`-tegel. Die toont de versie van de geimporteerde dashboardconfig, zodat na een HACS-update zichtbaar is of Home Assistant nog een oude Lovelace-config gebruikt.

Vanaf versie `0.5.259` staat dezelfde dashboardversie ook als commentaar op de eerste regel van `dashboards/ecoflow-energy-control.yaml`. Bij handmatig controleren of opnieuw importeren is daardoor meteen te zien welke Lovelace-YAML wordt gebruikt.

Vanaf versie `0.5.260` is de `YAML`-tegel visueel herkenbaarder door een document-check-icoon, een statusattribuut en een expliciete YAML-marker. Daarmee valt de dashboardconfig-check sneller op naast de gewone integratieversie.

Vanaf versie `0.5.261` verwijst de Home Assistant manifest-informatie naar de publieke GitHub-repository `AllKn/ecoflow-energy-control`. HACS, documentatie en foutmeldingen wijzen daardoor naar dezelfde updatebron.

Vanaf versie `0.5.262` is er een lokale updatecontrole via `tools/release_check.py`. Die controleert voor publicatie of manifest, README, app-versie, dashboard-YAML, HACS-domein en GitHub-links dezelfde release beschrijven en noemt welke versie na de update in Home Assistant zichtbaar moet zijn.

Vanaf versie `0.5.263` is er ook `tools/build_release_package.py`. Die maakt een schoon zip-pakket voor handmatige GitHub-upload zonder `.git`, caches of lokale bestanden, zodat HACS dezelfde gevalideerde inhoud kan ophalen.

Vanaf versie `0.5.264` neemt dat releasepakket ook de testbestanden mee. Daardoor blijft de GitHub-repository bij handmatige upload niet alleen bruikbaar voor HACS, maar ook als volledige verificatiebron voor de dashboard- en integratiecontracten.

Vanaf versie `0.5.265` bevat het releasepakket ook `release-manifest.json` met versie, domein, bestandslijst, bestandsgroottes en SHA256-checksums. Daarmee is handmatige GitHub-upload beter te vergelijken met de lokaal gevalideerde inhoud.

Vanaf versie `0.5.266` bewaakt de dashboardtest extra dat oude live-dashboardlabels zoals `Gereedheid` en `Keuze wijzigen` niet terugkeren in de meegeleverde YAML. Ook wordt in `Scenario - nu` gecontroleerd dat kerntegels zoals `Input` niet dubbel worden gedefinieerd.

Vanaf versie `0.5.267` staan dashboard-updatehints ook op de bestaande `Versie`-sensor. Daardoor kan een gebruiker bij een oude dashboardimport alsnog zien welke dashboard-YAML versie verwacht wordt, welke marker bovenaan de YAML hoort te staan en dat het hoofd-dashboard opnieuw geïmporteerd of vervangen moet worden.

Vanaf versie `0.5.268` krijgt de eerste tegel in `Controle` expliciet de korte naam `Overzicht`. Daardoor blijft het hoofd-dashboard compact, ook wanneer Home Assistant nog een oude lange entiteitnaam in de registry bewaart.

Vanaf versie `0.5.269` ruimt de integratie bij het laden oude lange Home Assistant registry-namen op wanneer ze nog met `EcoFlow Energy Control applicatie` beginnen. Het scenario-detailblok gebruikt daarnaast korte tegels, zodat oude registry-namen de simpele dashboardflow niet meer overheersen.
Vanaf versie `0.5.271` is Smart Plug als onderdeel van de ene main flow uitgebreid met automatisch tijdvensterschema: elk plug-item kan nu `schema_on` en `schema_off` behouden. De coordinator past dit schema automatisch toe tijdens elke update, en device-status toont die velden plus berekende geplande status.
Vanaf versie `0.5.272` is de HomeWizard-metersanering defensiever gemaakt tijdens opstart: bij legacy of incomplete roldata gebruikt de integratie een veilige fallback i.p.v. te crashen tijdens het instellen.
Vanaf versie `0.5.273` is de zonvoorspellingshorizon in de coordinator tijdzone-bestendig gemaakt (aware/naive datumvergelijkingen), waardoor de updatecyclus stabiel blijft bij forecast-rijen uit de weerbron.
Vanaf versie `0.5.274` is het hoofd-dashboard opnieuw herschikt voor uitlegbaarheid en minimale achtergrondkennis: Flow, Basis en Scenario-flows hebben extra korte toelichtingsteksten, en secundaire blokken zijn compacter en duidelijker gesplitst. Daarmee blijft de productieflow met één dashboard bruikbaar zonder mini-tegeloverload.
Vanaf versie `0.5.275` heeft de dashboardflow een extra productiewaardige leesbaarheidsronde gehad: minder losse mini-tegels en meer gecategoriseerde `entities`-lijsten in Basis en Controle, met extra routehints en inline uitleg via tooltip-achtige markdownregels zodat een nieuwe gebruiker direct kan starten zonder expertkennis.
Vanaf versie `0.5.277` is Flow opnieuw hertekend naar één duidelijke lijn: eerst een compacte statuslijst, daarna één-koloms control-acties en duidelijke labelregels, naar voorbeeld van veel gebruikte EMS-dashboard flows. Daardoor blijft de route meteen hanteerbaar op mobiel zonder kleine onleesbare knoppen.
Vanaf versie `0.5.278` zijn de Flow-waarde en Zekerheid-kaarten teruggebracht naar reguliere `entities`-regels. Dat voorkomt de Home Assistant `Configuration error` die ontstond bij een dynamische gauge via `custom:auto-entities`.
Vanaf versie `0.5.279` synchroniseert de integratie het meegeleverde dashboard automatisch naar de Lovelace-opslag onder `ecoflow-app-dashboard`. Daardoor gaan dashboardtitel en inhoud mee met een HACS-update/reload, zonder handmatig plakken in de raw editor.
Vanaf versie `0.5.280` is er handmatige noodbediening toegevoegd: `Teruglevering naar 0` zet alle PowerStreams direct op 0 W en zet hun groepstrategie op idle. De Smart Plug voor Delta Pro-laden staat daarnaast als schakelaar in het handmatige blok en gebruikt de actuele EcoFlow-status als beginstand wanneer die quota beschikbaar is.

## Huidige stand

EEC app werkt nu als lokale energieregisseur binnen Home Assistant. De app combineert EcoFlow Cloud API, EnergyZero/EPEX-prijzen, HomeWizard live-data, Home Assistant P1-historie, weerverwachting en scenarioadvies. Waar data ontbreekt, toont de app diagnose in plaats van stil te falen.

## Bijhouden per iteratie

Werk bij elke functionele iteratie drie plekken bij:

- `README.md`: korte versiegeschiedenis en actuele versie.
- `docs/ontwikkeling.md`: gebruikersvriendelijke toelichting op de ontwikkellijn.
- `docs/eec-app-ontwikkeling.pptx` en `docs/presentation-src/`: korte presentatie voor een snelle rondleiding.
