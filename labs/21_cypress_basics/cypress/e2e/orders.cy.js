// lab 21：对 SUT 复刻 Playwright 项目 16 的三条用例——同语义跨框架对比的素材
// Cypress 特色：命令链条 + 内置自动等待（should 自带重试，无需显式 wait）

describe('Ministore 订单管理', () => {
  const uniq = () => Math.random().toString(36).slice(2, 8)

  it('下单：填表提交后新订单出现在列表', () => {
    const user = `cypress用户-${uniq()}`
    cy.visit('/')
    cy.get('#customer').type(user)
    cy.get('#item').type('cypress 商品')
    cy.get('#price').type('12.5')
    cy.contains('button', '创建订单').click()
    cy.contains(user).should('be.visible')       // 自动等待渲染完成
  })

  it('查询：订单列表至少有一行且表头齐全', () => {
    cy.visit('/')
    cy.get('table thead th').should('have.length', 7)
    cy.get('#orders tr').its('length').should('be.gte', 1)
  })

  it('删除：创建一行再删掉，行从列表消失', () => {
    const user = `待删-${uniq()}`
    cy.visit('/')
    cy.get('#customer').type(user)
    cy.get('#item').type('即抛商品')
    cy.get('#price').type('1')
    cy.contains('button', '创建订单').click()
    cy.contains('tr', user).find('.delete-btn').click()
    cy.contains(user).should('not.exist')        // 自动等元素消失
  })
})
