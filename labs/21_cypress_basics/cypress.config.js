// Cypress 配置：baseUrl 指向 lab 脚本起的 SUT；教学套件关掉视频减少噪音
const { defineConfig } = require('cypress')

module.exports = defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_SUT_URL || 'http://127.0.0.1:8921',
    supportFile: false,
    video: true,
    screenshotOnRunFailure: true,
  },
})
