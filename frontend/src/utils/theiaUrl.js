/**
 * Build same-origin Theia URL to avoid cross-origin issues
 * @param {number|string} theiaPort - The Theia IDE port number
 * @param {string} path - Optional path to append (default: "/")
 * @returns {string} - Complete Theia URL using same origin
 */
export function buildTheiaUrl(theiaPort, path = "/") {
  const origin = window.location.origin; // https://anybot.brainswarmrobotics.com
  const port = String(theiaPort || "").trim();
  if (!/^\d+$/.test(port)) {
    console.warn("Invalid theiaPort:", theiaPort);
    return `${origin}/theia/`;
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${origin}/theia/${port}${normalizedPath}`;
}
