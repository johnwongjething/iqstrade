// config.js for frontend (auto-copied from backup)

const environment = process.env.NODE_ENV || 'development';

const config = {
  development: {
    API_BASE_URL: '/',
  },
  production: {
    API_BASE_URL: '/',
  },
};

if (config[environment].API_BASE_URL) {
  config[environment].API_BASE_URL = config[environment].API_BASE_URL.replace(/\/$/, '');
}

const currentConfig = config[environment];

export const API_BASE_URL = currentConfig.API_BASE_URL;
export default currentConfig;
