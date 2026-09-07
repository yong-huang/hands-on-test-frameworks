// cy.session 会话复用 + 自定义命令 createOrder
describe('登录态复用与自定义命令', () => {
  it('admin 会话：控制台看到总订单数', () => {
    cy.login('admin')
    cy.visit('/admin.html')
    cy.contains('总订单数').should('be.visible')
  })

  it('user 会话：同一控制台被拒绝——角色不串号', () => {
    cy.login('user')
    cy.visit('/admin.html')
    cy.contains('访问被拒').should('be.visible')
  })

  it('自定义命令 cy.createOrder 被多条用例复用', () => {
    cy.createOrder(`复用命令-${Math.random().toString(36).slice(2, 8)}`)
  })
})
