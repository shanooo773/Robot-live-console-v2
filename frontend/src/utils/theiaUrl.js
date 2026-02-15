/**
 * Build same-origin Theia URL to avoid cross-origin issues
 * @param {number|string} theiaPort - The Theia IDE port number
 * @param {string} path - Optional path to append (default: "/")
 * @returns {string|null} - Complete Theia URL using same origin, or null if port is invalid
 */
export function buildTheiaUrl(theiaPort, path = "/") {
  const origin = window.location.origin; // https://anybot.brainswarmrobotics.com
  const port = String(theiaPort || "").trim();
  if (!/^\d+$/.test(port)) {
    console.error("Invalid theiaPort:", theiaPort, "- must be a numeric port");
    return null; // Return null to let calling code handle the error
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${origin}/theia/${port}${normalizedPath}`;
}
