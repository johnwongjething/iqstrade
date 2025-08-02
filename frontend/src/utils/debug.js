import { ENABLE_DEBUG } from '../config';

// Debug utility that respects the ENABLE_DEBUG flag
class DebugLogger {
  constructor() {
    this.enabled = ENABLE_DEBUG;
  }

  log(...args) {
    if (this.enabled) {
      console.log('[DEBUG]', ...args);
    }
  }

  warn(...args) {
    if (this.enabled) {
      console.warn('[DEBUG]', ...args);
    }
  }

  error(...args) {
    // Always log errors, even in production
    console.error('[ERROR]', ...args);
  }

  group(label) {
    if (this.enabled) {
      console.group(`[DEBUG] ${label}`);
    }
  }

  groupEnd() {
    if (this.enabled) {
      console.groupEnd();
    }
  }

  time(label) {
    if (this.enabled) {
      console.time(`[DEBUG] ${label}`);
    }
  }

  timeEnd(label) {
    if (this.enabled) {
      console.timeEnd(`[DEBUG] ${label}`);
    }
  }
}

// Create singleton instance
const debug = new DebugLogger();

// Export for use throughout the app
export default debug;

// Also export individual methods for convenience
export const { log, warn, error, group, groupEnd, time, timeEnd } = debug; 