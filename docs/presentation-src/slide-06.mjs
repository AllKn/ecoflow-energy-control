import { background, colors, metric } from "./theme.mjs";

export async function slide06(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "Scenario's als gewone keuzes");
  metric(slide, ctx, "Eigen gebruik", "besparen", 72, 230, 250, colors.green);
  metric(slide, ctx, "Handelen", "prijsverschil", 352, 230, 250, colors.blue);
  metric(slide, ctx, "Buffer 50%", "reserve", 632, 230, 250, colors.amber);
  metric(slide, ctx, "Uit", "0 W", 912, 230, 180, colors.red);
  ctx.addText(slide, {
    text: "De app simuleert effect in W, kWh en EUR. Plan en Uitvoerbaar gebruiken dezelfde geteste taal voor sturen, testmodus, datagaten en wachten.",
    x: 72,
    y: 430,
    width: 940,
    height: 90,
    fontSize: 26,
    color: colors.ink,
  });
  return slide;
}
