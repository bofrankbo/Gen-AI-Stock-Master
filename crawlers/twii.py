from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
import time
import csv

# setting #######################################################
end_year = 2024                         # 資料抓到這一年
csv_file_path = 'twii_history.csv'    # 有過去資料的檔案
#################################################################

# 用with語句開啟檔案，確保在使用完後自動關閉
with open(csv_file_path, 'r') as file:
    # 使用csv.reader讀取檔案
    reader = csv.reader(file)

    # 將讀取的內容轉換為列表，並獲取最後一行
    last_row = list(reader)[-1]

# 印出最後一行
print(last_row)

########################################
# 直接設定開始日期
start_date = last_row[0]
########################################

y = str(start_date)[:4]
print(y)

m = int(str(start_date)[4:6])
print(m)

d = str(start_date)[6:]
print(d)

url = 'https://www.twse.com.tw/en/indices/taiex/mi-5min-hist.html'
driver = webdriver.Chrome()
driver.get(url)
driver.find_element(By.XPATH, '//*[@id="popupStatement"]/div/div/button').click()

for k in range(int(y), end_year+1):
    for j in range(m, 13):

        input_search_y = Select(driver.find_element(By.XPATH, '//*[@id="label0"]'))
        input_search_y.select_by_value(str(k))

        input_search_y = Select(driver.find_element(By.XPATH, '//*[@id="form"]/div/div[1]/span/select[2]'))
        input_search_y.select_by_value(str(j))

        search_btn = driver.find_element(By.XPATH, '//*[@id="form"]/div/button')
        search_btn.click()

        driver.implicitly_wait(1)
        sheet = driver.find_elements(By.XPATH, '//*[@id="reports"]/div[2]/div[2]/table/tbody/tr')
        print(len(sheet))

        for i in range(len(sheet)):
            # 設定時間避免重疊
            d = driver.find_element(By.XPATH, '//*[@id="reports"]/div[2]/div[2]/table/tbody/tr[' + str(i+1) + ']/td[1]').text
            original_date = datetime.strptime(d, '%Y/%m/%d')
            new_date_str = original_date.strftime('%Y%m%d')
            if int(start_date) >= int(new_date_str):
                continue

            data = [0, 0, 0, 0, 0]
            data[0] = new_date_str
            data[1] = driver.find_element(By.XPATH, '//*[@id="reports"]/div[2]/div[2]/table/tbody/tr[' + str(i+1) + ']/td[2]').text.replace(',', '')
            data[2] = driver.find_element(By.XPATH, '//*[@id="reports"]/div[2]/div[2]/table/tbody/tr[' + str(i+1) + ']/td[3]').text.replace(',', '')
            data[3] = driver.find_element(By.XPATH, '//*[@id="reports"]/div[2]/div[2]/table/tbody/tr[' + str(i+1) + ']/td[4]').text.replace(',', '')
            data[4] = driver.find_element(By.XPATH, '//*[@id="reports"]/div[2]/div[2]/table/tbody/tr[' + str(i+1) + ']/td[5]').text.replace(',', '')

            print(data)

            with open(csv_file_path, 'a', newline='') as csvfile:
                # 建立 CSV 檔寫入器
                writer = csv.writer(csvfile)

                # 寫入一列資料
                writer.writerow(data)

            # time.sleep(2)
        m = 1
