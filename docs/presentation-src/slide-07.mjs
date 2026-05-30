import { background, bulletList, colors } from "./theme.mjs";

export async function slide07(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "Waar de gebruiker nu naar kijkt");
  bulletList(
    slide,
    ctx,
    [
      { text: "Bovenaan: Main, Inzicht, Live, Stroom, Nu, Stap, Scenario en Test.", color: colors.blue },
      { text: "Main combineert status, stap, energie, scenario en bewijs.", color: colors.blue },
      { text: "Flow gebruikt tile-kaarten voor een rustiger bedienpaneel.", color: colors.green },
      { text: "Basissetup vraagt alleen batterij; EnergyZero is standaard.", color: colors.green },
      { text: "Main en Setup advies tonen wanneer EnergyZero default is.", color: colors.green },
      { text: "Korte EEC-labels houden de dashboardflow scanbaar.", color: colors.green },
      { text: "Live benoemt getest welke bron bewijs of sturing nog beperkt.", color: colors.green },
      { text: "Setup toont zichtbaar wat al kan: basisinzicht, sturing of optimalisatie.", color: colors.green },
      { text: "Stap en Live wijzen naar dezelfde ontbrekende live-bron.", color: colors.blue },
      { text: "Flow, Basis en Scenario - nu vormen de directe dagelijkse route.", color: colors.blue },
      { text: "P1 historie staat lager als context, niet in de beslisroute.", color: colors.green },
      { text: "Lege secundaire kaarten blijven verborgen bij minimale setup.", color: colors.green },
      { text: "Grafieken verschijnen pas wanneer prijs- of weerdata beschikbaar is.", color: colors.green },
      { text: "Datacheck benoemt nu ook ontbrekende of te korte grafiekbronnen.", color: colors.green },
      { text: "Losse testdashboards zijn opgeruimd; de hoofdroute blijft leidend.", color: colors.green },
      { text: "Datacheck gebruikt tegels, zodat bronstatus sneller scanbaar is.", color: colors.green },
      { text: "Grafiek-generators vermijden variabelebotsingen in ApexCharts.", color: colors.green },
      { text: "Controle toont YAML-versie om oude Lovelace-imports te herkennen.", color: colors.green },
      { text: "De dashboard-YAML begint met dezelfde versie als de integratie.", color: colors.green },
      { text: "De YAML-tegel heeft een document-check-icoon en expliciete marker.", color: colors.green },
      { text: "Manifest-links wijzen naar dezelfde GitHub-bron als HACS.", color: colors.green },
      { text: "Releasecheck bewijst lokaal welke versie HA moet tonen.", color: colors.green },
      { text: "Een schoon zip-pakket maakt handmatige GitHub-upload haalbaar.", color: colors.green },
      { text: "Het uploadpakket bevat ook tests als verificatiecontract.", color: colors.green },
      { text: "Release-manifest legt checksums per pakketbestand vast.", color: colors.green },
      { text: "Dashboardtests blokkeren oude labels en dubbele kerntegels.", color: colors.green },
      { text: "De Versie-sensor toont ook de verwachte dashboard-YAML.", color: colors.green },
      { text: "Scenario - nu is compact: overzicht, plan, uitvoerbaarheid en waarde.", color: colors.amber },
      { text: "Scenario-details bundelen actie, reden, vermogen en EUR-effect.", color: colors.amber },
      { text: "Eerst bewijs en datacheck; Scenario hulp blijft naslag.", color: colors.blue },
      { text: "Waarom verklaart start, automodus, context en uitvoerplan.", color: colors.blue },
      { text: "README en checklist benoemen de juiste dashboardroute.", color: colors.red },
    ],
    96,
    226,
    930,
  );
  return slide;
}
