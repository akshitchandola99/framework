package POC;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class MyAccountPage extends BasePage {

    //constructor
    public MyAccountPage(WebDriver driver)
    {
        super(driver);
        System.out.println("in myaccountpage constructor");
    }

    //WebElements
    @FindBy(xpath="//h2[normalize-space()='My Account']")
	WebElement msgHeading;
	
	@FindBy(xpath="(//a[normalize-space()='Logout'])[1]")
	WebElement btnLogout;
	
	@FindBy(xpath="//a[@title='My Account']")
	WebElement myAccount;

    //Action methods
    public String getHeadingMsg()
    {
        return msgHeading.getText();
    }

    public void clickLogout()
    {
        btnLogout.click();
    }

    public void clickMyAccount()
    {
        myAccount.click();
    }


}
