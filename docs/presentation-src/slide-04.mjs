import { background, bulletList, colors } from "./theme.mjs";

export async function slide04(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "Data betrouwbaar maken");
  bulletList(
    slide,
    ctx,
    [
      { text: "Delta Pro en Delta Pro 3 SoC uit de juiste telemetrievelden.", color: colors.blue },
      { text: "Laden, ontladen en netto vermogen los van elkaar zichtbaar.", color: colors.green },
      { text: "PowerStream en HomeWizard beschermd tegen factor-10 wattfouten.", color: colors.amber },
      { text: "PowerStream-teruglevering wordt van zonopwek afgetrokken.", color: colors.red },
    ],
    96,
    226,
    930,
  );
  return slide;
}
