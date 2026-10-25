package dev.handson.finalsuite;

import java.util.concurrent.atomic.AtomicInteger;

import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;

/** 最多重试 2 次（共 3 次执行）；用于演示「首试失败、重试通过」。 */
public class RetryAnalyzer implements IRetryAnalyzer {

    private final AtomicInteger attempt = new AtomicInteger(0);
    private static final int MAX_RETRY = 2;

    @Override
    public boolean retry(ITestResult result) {
        return attempt.incrementAndGet() <= MAX_RETRY;
    }
}
