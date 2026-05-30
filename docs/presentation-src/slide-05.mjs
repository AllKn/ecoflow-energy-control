import { background, colors, metric, pill } from "./theme.mjs";

export async function slide05(presentation, ctx) {
  const slide = presentation.slides.add();
  background(slide, ctx, "HomeWizard: live lokaal, historie via Home Assistant");
  metric(slide, ctx, "live", "P1 W", 72, 232, 250, colors.blue);
  metric(slide, ctx, "richting", "net in/uit", 352, 232, 250, colors.green);
  metric(slide, ctx, "P1 historie", "D/W/M", 632, 232, 300, colors.amber);
  ctx.addText(slide, {
    text: "De officiele HomeWizard API biedt actuele metingen. Historie uit Energy+ is niet als openbare cloud-API gedocumenteerd. EEC app importeert daarom bestaande Home Assistant HomeWizard-apparaten en toont vooraf rol plus gevonden meetsoorten zoals totaal W, fase W en kWh-historie.",
    x: 72,
    y: 420,
    width: 960,
    height: 108,
    fontSize: 24,
    color: colors.ink,
  });
  pill(slide, ctx, "officieel ondersteund pad", 72, 570, 300, colors.soft, colors.ink);
  return slide;
}
