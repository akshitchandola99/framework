package Utilities;

import java.io.FileInputStream;
import java.io.IOException;

import org.apache.poi.xssf.usermodel.XSSFRow;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.testng.annotations.DataProvider;

public class DataProviders {

    @DataProvider(name="RegistrationData")
    Object[][] getData() throws IOException
    {
        FileInputStream fis = new FileInputStream("TestData/emails_passwords.xlsx");

        XSSFWorkbook workbook = new XSSFWorkbook(fis);
        XSSFSheet sheet = workbook.getSheet("Sheet1");

        int rows = sheet.getLastRowNum(); //reurns the index of last row even if some rows are empty
        //int rows = sheet.getPhysicalNumberOfRows(); //returns the count of rows which are not empty

        int cols = sheet.getRow(1).getLastCellNum(); //returns the count of cells in that row that can include empty cells also
        //int cols = sheet.getRow(0).getPhysicalNumberOfCells(); //returns the count of cells in that row which are not empty

        System.out.println("rows: "+rows+" cols: "+cols);

        Object[][] data = new Object[rows][cols];

        for(int r=1; r<=rows ; r++)
        {
            XSSFRow currentRow = sheet.getRow(r);

             if(currentRow == null) {
                // Optionally skip or break if you expect only populated rows
                continue;
            }
                
            for(int c=0; c<cols; c++)
            {
                String cellValue = currentRow.getCell(c).toString();
                data[r-1][c]=cellValue;
            }
        }

        /*Object[][] datas = new Object[][]{
            {"akshitchandola60@gmail.com","qwerty12345"},
            {"akshitchandola61@gmail.com","qwerty12345"}};*/

            return data;
            
            
    }
    
}
