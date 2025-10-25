package TestCases;

import java.io.FileReader;
import java.io.IOException;
import java.time.Duration;
import java.util.Properties;
import java.util.Random;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.edge.EdgeDriver;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.openqa.selenium.firefox.FirefoxOptions;
import org.openqa.selenium.safari.SafariDriver;
import org.testng.annotations.AfterTest;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Parameters;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;



public class BaseTestClass {

    public static WebDriver driver;
    public static Properties p;
    public static Logger logger = LogManager.getLogger(BaseTestClass.class.getName());

    @Parameters({"browser"})
    @BeforeTest
    void setup(String br) throws IOException
    {
        

        System.out.println("executing setup method");
        
        logger.info("********** Starting Test Execution **********");

        p=new Properties();
        FileReader fr = new FileReader("./src/test/resources/config.properties");
        p.load(fr);

        ChromeOptions croptions = new ChromeOptions();
        croptions.addArguments("--headless=new");

        FirefoxOptions froptions = new FirefoxOptions();
        froptions.addArguments("--headless");

        //DesiredCapabilities capabilities = new DesiredCapabilities();

    switch (br.toLowerCase()) {
        case "chrome":
            driver = new ChromeDriver();
            break;
            
        case "firefox":
            driver = new FirefoxDriver(froptions);
            break;
        case "edge":
            driver = new EdgeDriver();
            break;
        case "safari":
            driver = new SafariDriver();
            break;
        default:
            throw new IllegalArgumentException("Browser not supported: " + br);
    }

        driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
        driver.get(p.getProperty("url"));
        driver.manage().window().maximize();   

    }
    
    @AfterTest(alwaysRun = true)
    void teardown()
    {
        System.out.println("executing teardown method");
        logger.info("********** Ending Test Execution **********");
        driver.quit();
    }

    String randomAlphaString(int length)
    {
        String randomString = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
        StringBuilder sb = new StringBuilder(10);

        Random random = new Random();

        for (int i = 0; i < length; i++) {
            int index = random.nextInt(randomString.length());
            sb.append(randomString.charAt(index));
        }

        return sb.toString();
    }

    String randomNumericString(int length)
    {
        String randomString = "0123456789";
        StringBuilder sb = new StringBuilder(10);   
        Random random = new Random();
        for (int i = 0; i < length; i++) {
            int index = random.nextInt(randomString.length());
            sb.append(randomString.charAt(index));
        }
        return randomString.toString(); 
    }
    public static String randomAlphaNumericString(int length) {
        String alphaNumeric = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        StringBuilder sb = new StringBuilder(length);
        Random random = new Random();

        for (int i = 0; i < length; i++) {
            int index = random.nextInt(alphaNumeric.length());
            sb.append(alphaNumeric.charAt(index));
        }
        return sb.toString();
    }
}