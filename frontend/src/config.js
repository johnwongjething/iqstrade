const environment = process.env.NODE_ENV || 'development';

const config = {
  development: {
    API_BASE_URL: window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin,
    ENABLE_DEBUG: true,
  },
  production: {
    API_BASE_URL: (process.env.REACT_APP_API_BASE_URL || '/').trim(), // Backend for production
    ENABLE_DEBUG: false,
  },
  local: {
    API_BASE_URL: window.location.hostname === 'localhost' ? 'http://localhost:5000' : window.location.origin,
    ENABLE_DEBUG: true,
  }
};

// Clean up API_BASE_URL
if (config[environment].API_BASE_URL) {
  config[environment].API_BASE_URL = config[environment].API_BASE_URL.replace(/\/$/, '');
}

const currentConfig = config[environment];

// Configuration loaded

export const API_BASE_URL = currentConfig.API_BASE_URL; // Use the configured value
export const ENABLE_DEBUG = currentConfig.ENABLE_DEBUG;
export default currentConfig;
