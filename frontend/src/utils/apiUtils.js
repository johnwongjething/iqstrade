// API Utilities with Debouncing for Concurrent User Support
import { getHKNowISO } from './timezoneUtils';

// Debounce function to limit API calls
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Rate limiting for API calls
class APIRateLimiter {
  constructor(maxCalls = 10, timeWindow = 1000) { // 10 calls per second
    this.maxCalls = maxCalls;
    this.timeWindow = timeWindow;
    this.calls = [];
  }

  canMakeCall() {
    const now = Date.now();
    // Remove old calls outside the time window
    this.calls = this.calls.filter(time => now - time < this.timeWindow);
    return this.calls.length < this.maxCalls;
  }

  recordCall() {
    this.calls.push(Date.now());
  }

  async waitForSlot() {
    while (!this.canMakeCall()) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
}

// Global rate limiter
const apiRateLimiter = new APIRateLimiter();

// Enhanced API call function with rate limiting and retry logic
export const apiCall = async (url, options = {}, retries = 3) => {
  // Wait for rate limit slot
  await apiRateLimiter.waitForSlot();
  apiRateLimiter.recordCall();

  const config = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    credentials: 'include', // Include cookies for JWT
    ...options
  };

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await fetch(url, config);
      
      // Handle different response types
      if (response.status === 401) {
        // Unauthorized - redirect to login
        window.location.href = '/login';
        throw new Error('Authentication required');
      }
      
      if (response.status === 429) {
        // Rate limited - wait and retry
        if (attempt < retries) {
          await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
          continue;
        }
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
      
    } catch (error) {
      if (attempt === retries) {
        console.error(`API call failed after ${retries} attempts:`, error);
        throw error;
      }
      
      // Wait before retry with exponential backoff
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
    }
  }
};

// Debounced search function
export const debouncedSearch = debounce(async (searchTerm, searchFunction) => {
  if (!searchTerm || searchTerm.length < 2) return [];
  
  try {
    return await searchFunction(searchTerm);
  } catch (error) {
    console.error('Search error:', error);
    return [];
  }
}, 300); // 300ms debounce

// Debounced form submission
export const debouncedSubmit = debounce(async (formData, submitFunction) => {
  try {
    return await submitFunction(formData);
  } catch (error) {
    console.error('Form submission error:', error);
    throw error;
  }
}, 500); // 500ms debounce

// Performance monitoring
export const trackAPIPerformance = (url, startTime) => {
  const duration = Date.now() - startTime;
  
  // Log slow API calls
  if (duration > 2000) { // 2 seconds
    console.warn(`Slow API call: ${url} took ${duration}ms`);
  }
  
  // Store performance data
  if (!window.apiPerformance) {
    window.apiPerformance = [];
  }
  
  window.apiPerformance.push({
    url,
    duration,
            timestamp: getHKNowISO()
  });
  
  // Keep only last 100 entries
  if (window.apiPerformance.length > 100) {
    window.apiPerformance = window.apiPerformance.slice(-100);
  }
};

// Enhanced API call with performance tracking
export const trackedAPICall = async (url, options = {}) => {
  const startTime = Date.now();
  
  try {
    const result = await apiCall(url, options);
    trackAPIPerformance(url, startTime);
    return result;
  } catch (error) {
    trackAPIPerformance(url, startTime);
    throw error;
  }
};

// Get performance statistics
export const getAPIPerformanceStats = () => {
  if (!window.apiPerformance || window.apiPerformance.length === 0) {
    return null;
  }
  
  const durations = window.apiPerformance.map(p => p.duration);
  const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
  const maxDuration = Math.max(...durations);
  const slowCalls = durations.filter(d => d > 2000).length;
  
  return {
    totalCalls: window.apiPerformance.length,
    averageDuration: Math.round(avgDuration),
    maxDuration,
    slowCalls,
    slowCallPercentage: Math.round((slowCalls / window.apiPerformance.length) * 100)
  };
};

// Clear performance data
export const clearAPIPerformance = () => {
  window.apiPerformance = [];
};

// Export rate limiter for testing
export { apiRateLimiter }; 