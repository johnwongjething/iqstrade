#!/usr/bin/env node
/**
 * Local Development Frontend Starter
 * This script starts the React development server with local configuration
 */

const { spawn } = require('child_process');
const path = require('path');

// Starting IQS Trade Frontend (Local Development)

// Set environment variables for local development
process.env.NODE_ENV = 'development';
process.env.REACT_APP_API_BASE_URL = 'http://localhost:8000';

// Environment configured for local development

// Start the React development server
const reactScriptsPath = path.join(__dirname, 'node_modules', '.bin', 'react-scripts');
const startProcess = spawn(reactScriptsPath, ['start'], {
  stdio: 'inherit',
  env: process.env,
  cwd: __dirname
});

startProcess.on('close', (code) => {
      // React development server stopped
  process.exit(code);
});

startProcess.on('error', (error) => {
  console.error('❌ Error starting React development server:', error);
  process.exit(1);
});

// Handle process termination
process.on('SIGINT', () => {
  // Stopping React development server
  startProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  // Stopping React development server
  startProcess.kill('SIGTERM');
}); 