// 自定义命令：把"业务动作"封装成 cy.* 语言
Cypress.Commands.add('createOrder', (customer, item = '标准商品', price = '9.9') => {
  cy.visit('/')
  cy.get('#customer').type(customer)
  cy.get('#item').type(item)
  cy.get('#price').type(price)
  cy.contains('button', '创建订单').click()
  cy.contains(customer).should('be.visible')
})

// 登录命令：配合 cy.session 缓存会话——同角色只真正登录一次
Cypress.Commands.add('login', (role) => {
  const accounts = { admin: ['admin', 'admin123'], user: ['user', 'user123'] }
  const [username, password] = accounts[role]
  cy.session(
    `session-${role}`,
    () => {
      cy.visit('/login.html')
      cy.get('#username').type(username)
      cy.get('#password').type(password)
      cy.contains('button', '登录').click()
      cy.contains('登录成功').should('be.visible')
    },
    {
      cacheAcrossSpecs: true,
      validate() {
        cy.window().its('localStorage.token').should('exist')
      },
    },
  )
})
