/**
 * Theia container pre-warming utility.
 *
 * Calls GET /theia/status immediately after login or app startup so that
 * containers are started (and ideally ready) before the user clicks
 * Preview/Booking IDE, preventing first-click 502/Bad Gateway errors.
 *
 * Only one warmup loop runs at a time per browser session (guard flag).
 * The loop polls with increasing backoff and stops when:
 *   - preview_status === 'running' && preview_ready === true
 *   - (if has_active_booking) booking_status === 'running' && booking_ready === true
 *   - OR after MAX_DURATION_MS (60 s) – logs a warning but doesn't throw.
 */

const BACKOFF_DELAYS_MS = [1000, 2000, 3000, 5000]; // delays between polls
const MAX_DURATION_MS = 60_000; // absolute timeout

let _abortController = null; // tracks the active warmup so it can be cancelled

/**
 * Start a background Theia warmup loop for the given auth token.
 * Safe to call multiple times – a running loop is cancelled first.
 *
 * @param {string} token - JWT bearer token
 */
export function startTheiaWarmup(token) {
  if (!token) return;

  // Cancel any previous warmup before starting a new one
  stopTheiaWarmup();

  const controller = new AbortController();
  _abortController = controller;

  _runWarmup(token, controller).catch((err) => {
    if (err.name !== 'AbortError') {
      console.warn('[TheiaWarmup] Unexpected error during warmup:', err);
    }
  });
}

/**
 * Stop any currently running warmup loop (e.g. on logout).
 */
export function stopTheiaWarmup() {
  if (_abortController) {
    _abortController.abort();
    _abortController = null;
  }
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

async function _runWarmup(token, controller) {
  const signal = controller.signal;
  const deadline = Date.now() + MAX_DURATION_MS;
  let delayIndex = 0;

  console.log('[TheiaWarmup] Starting pre-warm loop');

  while (Date.now() < deadline) {
    if (signal.aborted) return;

    let status = null;
    try {
      const response = await fetch('/theia/status', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        signal,
      });

      if (response.ok) {
        status = await response.json();
      } else {
        console.warn(`[TheiaWarmup] /theia/status returned HTTP ${response.status}`);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.warn('[TheiaWarmup] Fetch error:', err.message);
    }

    if (status && _isReady(status)) {
      console.log('[TheiaWarmup] Containers ready – stopping warm-up loop');
      if (_abortController === controller) _abortController = null;
      return;
    }

    // Wait before next poll (with backoff, capped at last entry)
    const delay = BACKOFF_DELAYS_MS[Math.min(delayIndex, BACKOFF_DELAYS_MS.length - 1)];
    delayIndex++;

    await _sleep(delay, signal);
    if (signal.aborted) return;
  }

  console.warn('[TheiaWarmup] Timed out waiting for containers to be ready (60 s)');
  if (_abortController === controller) _abortController = null;
}

function _isReady(status) {
  const previewReady =
    status.preview_status === 'running' && status.preview_ready === true;

  if (!previewReady) return false;

  if (status.has_active_booking) {
    return status.booking_status === 'running' && status.booking_ready === true;
  }

  return true;
}

function _sleep(ms, signal) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    if (signal) {
      signal.addEventListener('abort', () => {
        clearTimeout(timer);
        reject(Object.assign(new Error('Aborted'), { name: 'AbortError' }));
      }, { once: true });
    }
  });
}
