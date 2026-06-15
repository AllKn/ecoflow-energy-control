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
      { text: "Flow/Basis/Sleutelkaarten zijn compacter en beter scanbaar voor dagelijkse bediening.", color: colors.amber },
      { text: "0.5.286 laat beginners direct aangesloten Delta-zonnepanelen als Wp invoeren.", color: colors.amber },
      { text: "0.5.287 toont Delta-zon als tekststatus; cijfers blijven context.", color: colors.amber },
      { text: "0.5.288 valideert Delta-panelen als geheel getal van 0 tot 10000 Wp.", color: colors.amber },
      { text: "0.5.289 stuurt setupadvies naar Delta-zonnepanelen invullen of zonmeter toevoegen.", color: colors.amber },
      { text: "0.5.290 maakt lege Delta-zontegels actiegericht met Wp-setuphint.", color: colors.amber },
      { text: "0.5.291 toont per Delta welke panelen zijn ingevuld en waar nog niets staat.", color: colors.amber },
      { text: "0.5.292 zet de Delta-panelenroute ook zichtbaar in de dashboard-Snelstart.", color: colors.amber },
      { text: "0.5.293 licht Batterij wijzigen zelf toe met Wp-voorbeeld en 0 als geen panelen.", color: colors.amber },
      { text: "0.5.294 onderscheidt Delta toevoegen van Wp invullen bij lege zonstatus.", color: colors.amber },
      { text: "0.5.295 toont Delta-zon ook in Context, zodat Wp-invoer zichtbaar meetelt in advies.", color: colors.amber },
      { text: "De Versie-sensor toont ook de verwachte dashboard-YAML.", color: colors.green },
      { text: "Dashboardtests blokkeren oude labels en dubbele kerntegels.", color: colors.green },
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
