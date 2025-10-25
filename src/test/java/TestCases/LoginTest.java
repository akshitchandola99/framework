package TestCases;
import org.testng.SkipException;
import org.testng.annotations.Test;
import org.testng.asserts.SoftAssert;
import POC.HomePage;
import POC.LoginPage;
import POC.MyAccountPage;
import POC.RegistrationPage;

public class LoginTest extends BaseTestClass {

    //int i=0;
    int x=10;
    int j = 0;
    int z =10;
    
    @Test(dependsOnGroups = "registeration")
    void loginTest() throws InterruptedException
    {
        System.out.println("in login test method");
        
        HomePage hp=new HomePage(driver);
        hp.clickMyAccount();
        hp.clickLogin();

        LoginPage lp=new LoginPage(driver);
        RegistrationPage rp=new RegistrationPage(driver);

        //System.out.println(rp.getEmail());
        //System.out.println(rp.getPassword());

        //lp.setEmail(p.getProperty("email"));
        //lp.setPassword(p.getProperty("password"));

        //testing with data from registration test
        //if(rp.getEmail()==null || rp.getPassword()==null)
        //{
            /*if(i==0)
            {
                throw new SkipException("skipping as email and password not available");
            }*/
        //}

        lp.setEmail(rp.getEmail());
        lp.setPassword(rp.getPassword());
        lp.clickLogin();


        SoftAssert sa=new SoftAssert();

        MyAccountPage mp=new MyAccountPage(driver);
        if(mp.getHeadingMsg().equals("My Account"))
        {
            System.out.println("login successful");
            sa.assertTrue(true);
        }
        else
        {
            System.out.println("login failed");
            sa.assertTrue(false);
        }
        mp.clickMyAccount();
        mp.clickLogout();
        rp.clickSuccessContinue();

        Thread.sleep(2000);
        
        //sa.assertAll();
        sa.assertAll();

    }
}
