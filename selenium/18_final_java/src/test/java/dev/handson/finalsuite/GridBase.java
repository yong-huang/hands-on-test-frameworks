package dev.handson.finalsuite;

import java.net.URI;
import java.time.Duration;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.remote.RemoteWebDriver;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;

/** Grid 基类：Remote driver 打向 standalone Grid（项目 13 的 compose）。 */
public class GridBase {

    protected WebDriver d;

    @BeforeMethod(alwaysRun = true)
    public void setUp() throws Exception {
        String grid = System.getenv().getOrDefault("GRID_URL", "http://127.0.0.1:4444/wd/hub");
        ChromeOptions opts = new ChromeOptions();
        opts.addArguments("--no-sandbox");
        d = new RemoteWebDriver(URI.create(grid).toURL(), opts);
        d.manage().window().setSize(new org.openqa.selenium.Dimension(1400, 1000));
        d.manage().timeouts().implicitlyWait(Duration.ZERO);
    }

    @AfterMethod(alwaysRun = true)
    public void tearDown() {
        if (d != null) {
            d.quit();
        }
    }
}
