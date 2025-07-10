const environment = process.env.NODE_ENV || 'development';

const config = {
  development: {
    API_BASE_URL: 'http://localhost:8000', // Flask server port
  },
  production: {
    API_BASE_URL: (process.env.REACT_APP_API_BASE_URL || 'https://iqstrade.onrender.com').trim(), // Backend for production
  },
};

if (config[environment].API_BASE_URL) {
  config[environment].API_BASE_URL = config[environment].API_BASE_URL.replace(/\/$/, '');
}

const currentConfig = config[environment];

export const API_BASE_URL = currentConfig.API_BASE_URL; // Use the configured value
export default currentConfig;
