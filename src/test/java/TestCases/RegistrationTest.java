package TestCases;

import org.testng.annotations.Test;
import org.testng.asserts.SoftAssert;

import POC.HomePage;
import POC.MyAccountPage;
import POC.RegistrationPage;

//@Test(enabled = false)
//@Ignore
public class RegistrationTest extends BaseTestClass {


    //@Test(dataProvider="RegistrationData", dataProviderClass=Utilities.DataProviders.class)
    //void registrationTest(String fname, String lname, String email, String phone, String pass, String confPassword) throws InterruptedException
    //@Ignore
    @Test(groups = "registeration")
    void registrationTest() throws InterruptedException
    {
        System.out.println("in registration test method");

        logger.info("********** Starting Registration Test **********");
        HomePage hp=new HomePage(driver);
        hp.clickMyAccount();
        hp.clickRegister();
        RegistrationPage rp=new RegistrationPage(driver);

        /* 
        rp.setFirstname(fname);
        rp.setLastname(lname);
        rp.setEmail(email);
        rp.setPhone(phone);
        rp.setPassword(pass);
        rp.setConfirmPassword(confPassword);*/

        rp.setFirstname(randomAlphaString(5));
        rp.setLastname(randomAlphaString(5));
        rp.setEmail(randomAlphaNumericString(7)+"@gmail.com");
        rp.setPhone(randomNumericString(10));
        rp.setPassword(randomAlphaNumericString(8));
        rp.setConfirmPassword(rp.getPassword());

        rp.clickAgree();
        rp.clickContinue();

        SoftAssert sa=new SoftAssert();
        if(rp.getSuccessMsg().equals("Your Account Has Been Created!"))
        {
            System.out.println("registration successful");
            sa.assertTrue(true);
        }
        else
        {
            System.out.println("registration failed");
            sa.assertTrue(false);
        }

        rp.clickSuccessContinue();
        
        MyAccountPage mp=new MyAccountPage(driver);
        mp.clickMyAccount();
        mp.clickLogout();
        rp.clickSuccessContinue();

        Thread.sleep(3000);
        sa.assertAll();

    }

}
