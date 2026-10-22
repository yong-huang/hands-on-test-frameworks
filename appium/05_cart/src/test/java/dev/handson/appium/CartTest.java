package dev.handson.appium;

import org.testng.annotations.BeforeClass;
import org.testng.annotations.Test;

import java.math.BigDecimal;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertTrue;

/**
 * 加购与购物车：角标、数量加减、总价同步、删除空态。
 * 该 App 的演示数据：第一个商品是 Sauce Labs Backpack - Black，$29.99。
 */
public class CartTest extends BaseTest {

    private CartPage cart;

    @BeforeClass(alwaysRun = true)
    public void initPage() {
        cart = new CartPage(this);
    }

    /** 加购 2 件：详情页数量调到 2 后加购一次，角标与总价同步。 */
    @Test
    public void addingTwoItemsShowsBadgeTwoAndSyncsTotal() {
        cart.openFirstProduct();
        BigDecimal unitPrice = cart.detailUnitPrice();

        cart.tapAddPlusOnDetail();
        assertEquals(cart.detailQuantity(), 2, "详情页数量应为 2");

        // 角标统计的是总件数：先加 1 件再加 2 件会得到 3，
        // 所以"加购 2 件"要把 Amount 调到 2 后只加购一次。
        cart.addToCartAndWaitBadge("2");
        assertEquals(cart.badgeText(), "2", "加购 2 件后角标应为 2");
        System.out.printf("✅ 加购 2 件：角标=2，单价 $%s%n", unitPrice);

        cart.openCart();
        BigDecimal total = cart.cartTotal();
        assertEquals(total, unitPrice.multiply(BigDecimal.valueOf(2)),
                "总价应等于单价 × 2");
        System.out.printf("✅ 购物车总价同步：$%s = $%s × 2（%s）%n",
                total, unitPrice, cart.itemCountLabel());
    }

    /** 购物车内 +1/-1：总价与件数随之同步。 */
    @Test
    public void quantityStepperInCartSyncsTotal() {
        cart.openFirstProduct();
        BigDecimal unitPrice = cart.detailUnitPrice();
        cart.addToCartAndWaitBadge("1");
        cart.openCart();

        cart.tapAddPlusInCart();
        assertEquals(cart.cartTotal(), unitPrice.multiply(BigDecimal.valueOf(2)),
                "数量 +1 后总价应等于单价 × 2");
        System.out.printf("✅ 购物车 +1：%s，总价 $%s%n",
                cart.itemCountLabel(), cart.cartTotal());

        cart.tapSubtractMinusInCart();
        assertEquals(cart.cartTotal(), unitPrice,
                "数量 -1 后总价应回到单价");
        System.out.printf("✅ 购物车 -1：%s，总价 $%s%n",
                cart.itemCountLabel(), cart.cartTotal());
    }

    /** 删除商品：回到 No Items 空态。 */
    @Test
    public void removeItemReturnsToEmptyState() {
        cart.openFirstProduct();
        cart.addToCartAndWaitBadge("1");
        cart.openCart();
        System.out.printf("✅ 删除前：%s，总价 $%s%n",
                cart.itemCountLabel(), cart.cartTotal());

        cart.removeItemAndWaitEmptyState();
        assertTrue(cart.emptyStateVisible(), "删除后应显示 No Items 空态");
        System.out.println("✅ 删除后回到 No Items 空态");
    }
}
