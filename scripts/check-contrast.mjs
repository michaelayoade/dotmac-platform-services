import { portalColors } from "../packages/design-tokens/dist/index.mjs";

const MIN_CONTRAST = 4.5;

function hexToRgb(hex) {
  const normalized = hex.startsWith("#") ? hex.slice(1) : hex;
  const value = normalized.length === 3
    ? normalized.split("").map((c) => c + c).join("")
    : normalized;
  return {
    r: parseInt(value.slice(0, 2), 16),
    g: parseInt(value.slice(2, 4), 16),
    b: parseInt(value.slice(4, 6), 16),
  };
}

function channelToLinear(value) {
  const c = value / 255;
  return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function relativeLuminance({ r, g, b }) {
  const rl = channelToLinear(r);
  const gl = channelToLinear(g);
  const bl = channelToLinear(b);
  return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl;
}

function contrastRatio(foreground, background) {
  const fg = relativeLuminance(hexToRgb(foreground));
  const bg = relativeLuminance(hexToRgb(background));
  const lighter = Math.max(fg, bg);
  const darker = Math.min(fg, bg);
  return (lighter + 0.05) / (darker + 0.05);
}

const failures = [];

for (const [variant, scheme] of Object.entries(portalColors)) {
  for (const mode of ["light", "dark"]) {
    const text = scheme.text[mode];
    const background = scheme.background[mode];
    const surface = scheme.surface[mode];

    const checks = [
      { label: `${variant}:${mode}:text/background`, fg: text, bg: background },
      { label: `${variant}:${mode}:text/surface`, fg: text, bg: surface },
    ];

    for (const check of checks) {
      const ratio = contrastRatio(check.fg, check.bg);
      if (ratio < MIN_CONTRAST) {
        failures.push(`${check.label} = ${ratio.toFixed(2)} (min ${MIN_CONTRAST})`);
      }
    }
  }
}

if (failures.length) {
  console.error("Contrast checks failed:");
  failures.forEach((entry) => console.error(`- ${entry}`));
  process.exit(1);
}

console.log("Contrast checks passed.");
