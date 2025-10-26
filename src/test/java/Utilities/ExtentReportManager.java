package Utilities;

import java.util.Arrays;

import org.testng.ITestContext;
import org.testng.ITestListener;
import org.testng.ITestResult;
import org.testng.annotations.Listeners;


@Listeners(Utilities.ExtentReportManager.class)
public class ExtentReportManager implements ITestListener {

    @Override
        public String toString() {
            return "ExtentReportManager []";
        }


    @Override
    public void onTestStart(ITestResult result){
        System.out.println("Test Started: " + result.getName());
        System.out.println("Included Groups: " + Arrays.toString(result.getMethod().getGroups()));

    }

    @Override
    public void onTestSuccess(ITestResult result){
        System.out.println("Test Passed: " + result.getName());
    }

    @Override
    public void onTestFailure(ITestResult result){
        System.out.println("Test Failed: " + result.getName());
    }

    @Override
    public void onTestSkipped(ITestResult result){
        System.out.println("Test Skipped: " + result.getName());
    }

    @Override
    public void onStart(ITestContext context){
        System.out.println("Test Suite Started: " + context.getName());
    }

    @Override
    public void onFinish(ITestContext context){
        System.out.println("Test Finished: " + context.getName());
    }

   
}
