export const colors = {
  ink: "#17202A",
  muted: "#667085",
  line: "#D7DEE8",
  soft: "#F4F7FB",
  blue: "#1B68B3",
  green: "#2E8B57",
  amber: "#D28A15",
  red: "#C2473B",
  white: "#FFFFFF",
};

export function background(slide, ctx, title, kicker = "EEC app ontwikkeling") {
  ctx.addShape(slide, {
    x: 0,
    y: 0,
    width: 1280,
    height: 720,
    fill: colors.white,
    line: ctx.line(),
  });
  ctx.addText(slide, {
    text: kicker,
    x: 72,
    y: 48,
    width: 480,
    height: 24,
    fontSize: 18,
    color: colors.blue,
    bold: true,
  });
  ctx.addText(slide, {
    text: title,
    x: 72,
    y: 84,
    width: 960,
    height: 100,
    fontSize: 44,
    color: colors.ink,
    bold: true,
    typeface: ctx.fonts.title,
  });
  ctx.addShape(slide, {
    x: 72,
    y: 190,
    width: 1040,
    height: 2,
    fill: colors.line,
    line: ctx.line(),
  });
}

export function pill(slide, ctx, text, x, y, width, fill = colors.soft, color = colors.ink) {
  ctx.addShape(slide, {
    x,
    y,
    width,
    height: 44,
    fill,
    line: { style: "solid", fill: colors.line, width: 1 },
  });
  ctx.addText(slide, {
    text,
    x: x + 16,
    y: y + 10,
    width: width - 32,
    height: 24,
    fontSize: 18,
    color,
    bold: true,
  });
}

export function metric(slide, ctx, label, value, x, y, width, color = colors.blue) {
  ctx.addShape(slide, {
    x,
    y,
    width,
    height: 116,
    fill: colors.soft,
    line: { style: "solid", fill: colors.line, width: 1 },
  });
  ctx.addText(slide, {
    text: value,
    x: x + 20,
    y: y + 22,
    width: width - 40,
    height: 42,
    fontSize: 34,
    color,
    bold: true,
  });
  ctx.addText(slide, {
    text: label,
    x: x + 20,
    y: y + 72,
    width: width - 40,
    height: 28,
    fontSize: 18,
    color: colors.muted,
  });
}

export function bulletList(slide, ctx, items, x, y, width, fontSize = 24) {
  items.forEach((item, index) => {
    const top = y + index * 62;
    ctx.addShape(slide, {
      x,
      y: top + 10,
      width: 14,
      height: 14,
      fill: item.color || colors.blue,
      line: ctx.line(),
    });
    ctx.addText(slide, {
      text: item.text,
      x: x + 30,
      y: top,
      width,
      height: 48,
      fontSize,
      color: colors.ink,
    });
  });
}
