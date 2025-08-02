import { ENABLE_DEBUG } from '../config';

class PerformanceMonitor {
  constructor() {
    this.enabled = ENABLE_DEBUG;
    this.metrics = new Map();
    this.startTimes = new Map();
  }

  start(label) {
    if (this.enabled) {
      this.startTimes.set(label, performance.now());
    }
  }

  end(label) {
    if (this.enabled && this.startTimes.has(label)) {
      const startTime = this.startTimes.get(label);
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      this.metrics.set(label, duration);
      console.log(`[PERF] ${label}: ${duration.toFixed(2)}ms`);
      
      this.startTimes.delete(label);
      return duration;
    }
    return 0;
  }

  measure(label, fn) {
    if (this.enabled) {
      this.start(label);
      const result = fn();
      this.end(label);
      return result;
    }
    return fn();
  }

  async measureAsync(label, fn) {
    if (this.enabled) {
      this.start(label);
      const result = await fn();
      this.end(label);
      return result;
    }
    return fn();
  }

  getMetrics() {
    return Object.fromEntries(this.metrics);
  }

  clearMetrics() {
    this.metrics.clear();
    this.startTimes.clear();
  }

  // Monitor debug statement impact
  monitorDebugImpact() {
    if (!this.enabled) return;

    const originalLog = console.log;
    const originalWarn = console.warn;
    let logCount = 0;
    let warnCount = 0;

    console.log = (...args) => {
      logCount++;
      originalLog.apply(console, args);
    };

    console.warn = (...args) => {
      warnCount++;
      originalWarn.apply(console, args);
    };

    // Report after 5 seconds
    setTimeout(() => {
      console.log(`[PERF] Debug statements in 5s: ${logCount} logs, ${warnCount} warnings`);
      console.log = originalLog;
      console.warn = originalWarn;
    }, 5000);
  }
}

const performanceMonitor = new PerformanceMonitor();

export default performanceMonitor;
export const { start, end, measure, measureAsync, getMetrics, clearMetrics, monitorDebugImpact } = performanceMonitor; 