package dev.handson.finalsuite;

import org.testng.IAnnotationTransformer;
import org.testng.annotations.ITestAnnotation;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;

/** 全局挂 RetryAnalyzer（TestNG 的 transformer 惯用法）。 */
public class RetryListener implements IAnnotationTransformer {

    @Override
    public void transform(ITestAnnotation annotation, Class testClass, Constructor constructor, Method method) {
        annotation.setRetryAnalyzer(RetryAnalyzer.class);
    }
}
