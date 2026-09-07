const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_SUT_URL || 'http://127.0.0.1:8922',
    supportFile: 'cypress/support/e2e.js',
    video: false,
    retries: { runMode: 1, openMode: 0 },   // flaky 治理的第一道闸：运行时自动重试一次
  },
})
