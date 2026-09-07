// Cypress 版统一场景套件：同语义 5 条
describe('统一场景', () => {
  const uniq = () => Math.random().toString(36).slice(2, 8)

  it('1 首页加载', () => {
    cy.visit('/')
    cy.get('h1').contains('Ministore 订单管理').should('be.visible')
  })
  it('2 下单', () => {
    const u = `对比-${uniq()}`
    cy.visit('/')
    cy.get('#customer').type(u)
    cy.get('#item').type('对比商品')
    cy.get('#price').type('5.5')
    cy.contains('button', '创建订单').click()
    cy.contains(u).should('be.visible')
  })
  it('3 列表有行', () => {
    cy.visit('/')
    cy.get('#orders tr').its('length').should('be.gte', 1)
  })
  it('4 删除', () => {
    const u = `删除-${uniq()}`
    cy.visit('/')
    cy.get('#customer').type(u)
    cy.get('#item').type('x')
    cy.get('#price').type('1')
    cy.contains('button', '创建订单').click()
    cy.contains('tr', u).find('.delete-btn').click()
    cy.contains(u).should('not.exist')
  })
  it('5 慢 banner', () => {
    cy.intercept('GET', '**/api/slow-config', { body: { theme: 'd', banner: 'welcome' } })
    cy.visit('/')
    cy.contains('Banner: welcome').should('be.visible')
  })
})
