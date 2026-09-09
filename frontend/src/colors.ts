const hueCache = new Map<string, number>();

function hashString(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash * 31 + value.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

export function categoryHue(category: string): number {
  let hue = hueCache.get(category);
  if (hue === undefined) {
    hue = (hashString(category.toLowerCase()) * 137.508) % 360;
    hueCache.set(category, hue);
  }
  return hue;
}

export function categoryColor(category: string): { bg: string; fg: string } {
  const hue = categoryHue(category);
  return {
    bg: `hsl(${hue} 85% 93%)`,
    fg: `hsl(${hue} 70% 30%)`,
  };
}
