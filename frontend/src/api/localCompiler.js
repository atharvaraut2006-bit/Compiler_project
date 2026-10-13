/**
 * DEPRECATED / REMOVED: In-browser local compiler fallback.
 *
 * As part of the genuine PIM compiler audit, silent mock fallbacks have been removed.
 * All compilation requests are sent exclusively to the authentic Python backend service.
 */
export function runLocalCompilation() {
  throw new Error("Local mock compiler has been disabled. The application requires the authentic Python compiler backend.");
}
