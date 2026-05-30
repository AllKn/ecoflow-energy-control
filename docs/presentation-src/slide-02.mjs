import { background, bulletList, colors } from "./theme.mjs";

export async function slide02(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "De eerste bouwlaag: installeerbaar en herstelbaar");
  bulletList(
    slide,
    ctx,
    [
      { text: "HACS-structuur met juiste custom_components-map en manifest.", color: colors.blue },
      { text: "Eerste setup vraagt keys; Configureren begint daarna bij apparaten.", color: colors.green },
      { text: "HomeWizard-import gebruikt bestaande Home Assistant apparaten.", color: colors.amber },
      { text: "Dashboardbestanden meegeleverd en in README gedocumenteerd.", color: colors.amber },
      { text: "Versies, docs en presentatiebronnen worden met tests bewaakt.", color: colors.red },
    ],
    96,
    226,
    900,
  );
  return slide;
}
