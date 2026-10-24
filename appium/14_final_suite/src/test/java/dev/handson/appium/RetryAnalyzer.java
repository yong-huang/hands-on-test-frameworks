package dev.handson.appium;

import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

/** 失败自动重试，最多 1 次；成功后计入 flaky 统计。 */
public class RetryAnalyzer implements IRetryAnalyzer {

    public static final int MAX_RETRY = 1;
    private static int retriedAndPassed;

    private int count;

    @Override
    public boolean retry(ITestResult result) {
        if (count < MAX_RETRY) {
            count++;
            System.out.println("⚠️ flaky：" + result.getMethod().getMethodName()
                    + " 首次失败，自动重试 " + count + "/" + MAX_RETRY);
            return true;
        }
        if (result.getStatus() == org.testng.ITestResult.SUCCESS && count > 0) {
            retriedAndPassed++;
            System.out.println("⚠️ flaky：" + result.getMethod().getMethodName()
                    + " 重试后通过");
        }
        return false;
    }

    public static int flakyCount() {
        return retriedAndPassed;
    }
}
