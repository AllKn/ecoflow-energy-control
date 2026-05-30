import { background, colors, metric } from "./theme.mjs";

export async function slide03(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "EcoFlow: importeren, controleren, zichtbaar maken");
  metric(slide, ctx, "API-check", "auth + devices", 72, 230, 300, colors.blue);
  metric(slide, ctx, "import", "type kiezen", 410, 230, 300, colors.green);
  metric(slide, ctx, "telemetrie", "status per device", 748, 230, 300, colors.amber);
  ctx.addText(slide, {
    text: "De app toont per apparaat of de API werkt, welke velden EcoFlow teruggeeft en wat de minimale setup nu kan: basisinzicht, sturing of volledige optimalisatie. Zo blijft de hoofdroute klein.",
    x: 72,
    y: 420,
    width: 930,
    height: 120,
    fontSize: 25,
    color: colors.ink,
  });
  return slide;
}
