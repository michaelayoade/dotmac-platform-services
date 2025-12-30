const DEFAULT_FALLBACK_COLOR = "#000000";

export function hslToHex(hue: number, saturation: number, lightness: number) {
  const s = saturation / 100;
  const l = lightness / 100;
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((hue / 60) % 2) - 1));
  const m = l - c / 2;

  let r = 0;
  let g = 0;
  let b = 0;

  if (hue >= 0 && hue < 60) {
    r = c;
    g = x;
  } else if (hue >= 60 && hue < 120) {
    r = x;
    g = c;
  } else if (hue >= 120 && hue < 180) {
    g = c;
    b = x;
  } else if (hue >= 180 && hue < 240) {
    g = x;
    b = c;
  } else if (hue >= 240 && hue < 300) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }

  const toHex = (value: number) =>
    Math.round((value + m) * 255)
      .toString(16)
      .padStart(2, "0");

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
}

export function getCssHslColorHex(variableName: string, fallback = DEFAULT_FALLBACK_COLOR) {
  if (typeof window === "undefined") {
    return fallback;
  }

  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(variableName)
    .trim();
  if (!raw) {
    return fallback;
  }

  const parts = raw.split(/[\\s/]+/).filter(Boolean);
  const hue = Number.parseFloat(parts[0]);
  const saturation = Number.parseFloat(parts[1]);
  const lightness = Number.parseFloat(parts[2]);

  if ([hue, saturation, lightness].some(Number.isNaN)) {
    return fallback;
  }

  return hslToHex(hue, saturation, lightness);
}

