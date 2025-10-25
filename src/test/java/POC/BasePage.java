package POC;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.PageFactory;

public class BasePage {
    
    WebDriver driver;

    BasePage(WebDriver driver)
    {
        System.out.println("in basepage constructor");
        this.driver=driver;
        PageFactory.initElements(driver, this);
    }

}
