package POC;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.FindBy;

public class RegistrationPage extends BasePage {

    public RegistrationPage(WebDriver driver)
    {
        super(driver);
        System.out.println("in register page constructor");
    }

    @FindBy(xpath="//input[@id='input-firstname']")
	WebElement txtFirstname;
	
	@FindBy(xpath="//input[@id='input-lastname']")
	WebElement txtLastname;
	
	@FindBy(xpath="//input[@id='input-email']")
	WebElement txtEmail;
	
	@FindBy(xpath="//input[@id='input-telephone']")
	WebElement txtPhone;
	
	@FindBy(xpath="//input[@id='input-password']")
	WebElement txtPassword;
	
	@FindBy(xpath="//input[@id='input-confirm']")
	WebElement txtConfirmPassword;
	
	@FindBy(xpath="//input[@name='agree']")
	WebElement cbAgree;
	
	@FindBy(xpath="//input[@value='Continue']")
	WebElement btnContinue;
	
	@FindBy(xpath="//h1[normalize-space()='Your Account Has Been Created!']")
	WebElement msgSuccess;

    @FindBy(xpath="//a[normalize-space()='Continue']")
    WebElement btnSuccessContinue;

    static String email,pwd;

    public void setFirstname(String fname)
    {
        txtFirstname.sendKeys(fname);
    }

    public void setLastname(String lname)
    {
        txtLastname.sendKeys(lname);
    }

    public void setEmail(String email)
    {
        RegistrationPage.email=email;
        txtEmail.sendKeys(email);
    }
    public String getEmail()
    {
        return email;
        //return null;
    }

    public void setPhone(String phone)
    {
        txtPhone.sendKeys(phone);
    }

    public void setPassword(String pwd)
    {
        RegistrationPage.pwd=pwd;
        txtPassword.sendKeys(pwd);  
    }
    public String getPassword()
    {
        return pwd;
        //return null;
    }

    public void setConfirmPassword(String pwd)
    {
        txtConfirmPassword.sendKeys(pwd);  
    }
    public void clickAgree()
    {
        cbAgree.click();
    }
    public void clickContinue()
    {
        btnContinue.click();        
    }
    public String getSuccessMsg()
    {
        return msgSuccess.getText();
    }
    public void clickSuccessContinue()
    {
        btnSuccessContinue.click();        
    }

}
