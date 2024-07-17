// vue.config.js
module.exports = {
  devServer: {
      proxy: {
          '/api': {
              target: 'http://localhost:5000',  // Your backend server URL
              changeOrigin: true,  // Needed for CORS
          },
      },
  },
};