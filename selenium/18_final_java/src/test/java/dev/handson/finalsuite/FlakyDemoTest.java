package dev.handson.finalsuite;

import java.util.concurrent.atomic.AtomicBoolean;

import org.testng.Assert;
import org.testng.annotations.Test;

/** 重试演示：首试必失败、重试必通过——验证 RetryAnalyzer 链路（验收要求 ≥1 条重试成功）。 */
public class FlakyDemoTest extends GridBase {

    private static final AtomicBoolean FIRST = new AtomicBoolean(true);

    @Test(retryAnalyzer = RetryAnalyzer.class)
    public void failsOnceThenPasses() {
        if (FIRST.compareAndSet(true, false)) {
            System.out.println("[flaky-demo] 第 1 次执行：故意失败（RetryAnalyzer 将接管）");
            Assert.fail("演示用首试失败");
        }
        System.out.println("✅ 第二次执行通过（重试生效）");
    }
}
