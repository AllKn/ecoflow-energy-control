import { background, colors, metric, pill } from "./theme.mjs";

export async function slide01(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "Van losse bronnen naar een lokaal energieregelsysteem");
  ctx.addText(slide, {
    text: "EEC app verbindt EcoFlow, PowerStream, prijzen, HomeWizard, weer en scenario's in Home Assistant.",
    x: 72,
    y: 218,
    width: 880,
    height: 72,
    fontSize: 28,
    color: colors.ink,
  });
  metric(slide, ctx, "doel", "1 dashboard", 72, 340, 250, colors.blue);
  metric(slide, ctx, "basis", "lokaal HA", 352, 340, 250, colors.green);
  metric(slide, ctx, "sturing", "voorzichtig", 632, 340, 250, colors.amber);
  pill(slide, ctx, "testmodus eerst", 72, 520, 210, colors.soft, colors.ink);
  pill(slide, ctx, "diagnose zichtbaar", 308, 520, 240, colors.soft, colors.ink);
  pill(slide, ctx, "vriendelijke namen", 574, 520, 260, colors.soft, colors.ink);
  return slide;
}
