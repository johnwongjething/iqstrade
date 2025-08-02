const webpack = require('webpack');

module.exports = {
  webpack: {
    configure: (webpackConfig, { env }) => {
      // Only apply in production builds
      if (env === 'production') {
        // Add webpack plugin to strip console.log statements
        webpackConfig.plugins.push(
          new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('production'),
            // This will cause console.log statements to be removed during build
            'console.log': 'undefined',
            'console.warn': 'undefined',
            'console.info': 'undefined',
            'console.debug': 'undefined'
          })
        );

        // Add terser plugin configuration to remove console statements
        if (webpackConfig.optimization && webpackConfig.optimization.minimizer) {
          webpackConfig.optimization.minimizer.forEach(minimizer => {
            if (minimizer.constructor.name === 'TerserPlugin') {
              minimizer.options.terserOptions = {
                ...minimizer.options.terserOptions,
                compress: {
                  ...minimizer.options.terserOptions?.compress,
                  drop_console: true, // Remove console.log, console.warn, etc.
                  drop_debugger: true, // Remove debugger statements
                  pure_funcs: ['console.log', 'console.warn', 'console.info', 'console.debug']
                }
              };
            }
          });
        }
      }
      
      return webpackConfig;
    }
  }
}; 