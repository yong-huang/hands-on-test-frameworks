// cy.intercept：网络桩三连——提速 / 断网 / 500 注入（对应 Playwright lab 19）
describe('网络拦截', () => {
  it('慢接口桩成即时返回：banner 立刻出现 MOCKED', () => {
    cy.intercept('GET', '**/api/slow-config', {
      statusCode: 200,
      body: { theme: 'dark', banner: 'MOCKED', loaded_after_ms: 5 },
    }).as('fastConfig')
    cy.visit('/')
    cy.contains('MOCKED').should('be.visible')   // 不用等 1.5s——桩生效即出现
  })

  it('断网注入：banner 停留加载态、列表为空（优雅降级）', () => {
    cy.intercept('GET', '**/api/**', { forceNetworkError: true }).as('offline')
    cy.visit('/')
    cy.contains('正在加载配置…').should('be.visible')
    cy.get('#orders tr').should('have.length', 0)
  })

  it('500 注入：下单弹"下单失败"提示', () => {
    const alertStub = cy.stub()
    cy.on('window:alert', alertStub)
    cy.intercept('POST', '**/api/orders', { statusCode: 500, body: { detail: '内部错误（注入）' } }).as('brokenCreate')
    cy.visit('/')
    cy.get('#customer').type('注入用户')
    cy.get('#item').type('失败商品')
    cy.get('#price').type('1')
    cy.contains('button', '创建订单').click()
    cy.wait('@brokenCreate')
    cy.wrap().should(() => {
      expect(alertStub).to.have.been.calledWithMatch(/下单失败/)
    })
  })
})
