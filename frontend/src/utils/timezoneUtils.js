/**
 * Frontend Timezone Utilities for Hong Kong Time
 * Ensures consistent timezone handling across the entire frontend application
 */

// Hong Kong timezone configuration
const HK_TIMEZONE = 'Asia/Hong_Kong';
const HK_LOCALE = 'en-HK';

/**
 * Get current time in Hong Kong timezone
 * @returns {Date} Current date/time in Hong Kong timezone
 */
export const getHKNow = () => {
  return new Date();
};

/**
 * Get current time in Hong Kong timezone as ISO string
 * @returns {string} Current time in Hong Kong timezone as ISO format
 */
export const getHKNowISO = () => {
  return new Date().toISOString();
};

/**
 * Format a date string to Hong Kong timezone
 * @param {string|Date} dateString - Date string or Date object
 * @param {Object} options - Formatting options
 * @returns {string} Formatted date string in Hong Kong timezone
 */
export const formatHKDate = (dateString, options = {}) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    
    // Default options for Hong Kong formatting
    const defaultOptions = {
      timeZone: HK_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      ...options
    };
    
    return date.toLocaleDateString(HK_LOCALE, defaultOptions);
  } catch (error) {
    console.warn('Error formatting date:', error);
    return dateString;
  }
};

/**
 * Format a date string to Hong Kong timezone with time
 * @param {string|Date} dateString - Date string or Date object
 * @param {Object} options - Formatting options
 * @returns {string} Formatted date and time string in Hong Kong timezone
 */
export const formatHKDateTime = (dateString, options = {}) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    
    // Default options for Hong Kong date/time formatting
    const defaultOptions = {
      timeZone: HK_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      ...options
    };
    
    return date.toLocaleString(HK_LOCALE, defaultOptions);
  } catch (error) {
    console.warn('Error formatting date/time:', error);
    return dateString;
  }
};

/**
 * Format a date string to Hong Kong timezone with time (short format)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted date and time string in Hong Kong timezone (short)
 */
export const formatHKDateTimeShort = (dateString) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    
    return date.toLocaleString(HK_LOCALE, {
      timeZone: HK_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.warn('Error formatting date/time (short):', error);
    return dateString;
  }
};

/**
 * Format a date string to Hong Kong timezone (date only)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted date string in Hong Kong timezone (date only)
 */
export const formatHKDateOnly = (dateString) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    
    return date.toLocaleDateString(HK_LOCALE, {
      timeZone: HK_TIMEZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (error) {
    console.warn('Error formatting date only:', error);
    return dateString;
  }
};

/**
 * Format a date string to Hong Kong timezone (time only)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted time string in Hong Kong timezone (time only)
 */
export const formatHKTimeOnly = (dateString) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    
    return date.toLocaleTimeString(HK_LOCALE, {
      timeZone: HK_TIMEZONE,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (error) {
    console.warn('Error formatting time only:', error);
    return dateString;
  }
};

/**
 * Get relative time in Hong Kong timezone (e.g., "2 hours ago")
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Relative time string
 */
export const getHKRelativeTime = (dateString) => {
  if (!dateString) return '-';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return formatHKDateOnly(dateString);
  } catch (error) {
    console.warn('Error getting relative time:', error);
    return dateString;
  }
};

/**
 * Check if a date is today in Hong Kong timezone
 * @param {string|Date} dateString - Date string or Date object
 * @returns {boolean} True if date is today
 */
export const isHKToday = (dateString) => {
  if (!dateString) return false;
  
  try {
    const date = new Date(dateString);
    const today = new Date();
    
    const dateHK = date.toLocaleDateString(HK_LOCALE, { timeZone: HK_TIMEZONE });
    const todayHK = today.toLocaleDateString(HK_LOCALE, { timeZone: HK_TIMEZONE });
    
    return dateHK === todayHK;
  } catch (error) {
    console.warn('Error checking if date is today:', error);
    return false;
  }
};

/**
 * Get Hong Kong timezone information
 * @returns {Object} Timezone information
 */
export const getHKTimezoneInfo = () => {
  const now = new Date();
  
  return {
    timezone: HK_TIMEZONE,
    locale: HK_LOCALE,
    currentTime: now.toLocaleString(HK_LOCALE, { timeZone: HK_TIMEZONE }),
    currentDate: now.toLocaleDateString(HK_LOCALE, { timeZone: HK_TIMEZONE }),
    utcOffset: now.toLocaleString('en-US', { 
      timeZone: HK_TIMEZONE, 
      timeZoneName: 'shortOffset' 
    }).split(' ').pop()
  };
};

/**
 * Convert a date to Hong Kong timezone for comparison
 * @param {string|Date} dateString - Date string or Date object
 * @returns {Date} Date object in Hong Kong timezone
 */
export const toHKDate = (dateString) => {
  if (!dateString) return null;
  
  try {
    const date = new Date(dateString);
    // Create a new date with HK timezone components
    const hkString = date.toLocaleString(HK_LOCALE, { timeZone: HK_TIMEZONE });
    return new Date(hkString);
  } catch (error) {
    console.warn('Error converting to HK date:', error);
    return new Date(dateString);
  }
};

// Convenience functions for common use cases
export const hkNow = getHKNow;
export const hkNowISO = getHKNowISO;
export const hkDate = formatHKDate;
export const hkDateTime = formatHKDateTime;
export const hkDateOnly = formatHKDateOnly;
export const hkTimeOnly = formatHKTimeOnly;
export const hkRelative = getHKRelativeTime;
export const hkToday = isHKToday; 