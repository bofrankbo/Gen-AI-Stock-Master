import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import concurrent.futures
import time
import random
import json
import csv


# https://www.google.com/search?q=%E5%8F%B0%E7%A9%8D%E9%9B%BB&sca_esv=9dac49f0ebffbd81&sca_upv=1&rlz=1C5CHFA_enTW1068TW1068&tbm=nws&prmd=nsvimbtz&sxsrf=ADLYWIKnXyLeW2HlH7pwOCd0V9H3I7sEgA:1717147723871&ei=S5hZZpXfNIDl2roP6Z-FqQM&start=0&sa=N&ved=2ahUKEwjVsO7gybeGAxWAslYBHelPITU4ChDy0wN6BAgEEAQ&biw=1140&bih=867&dpr=2
# https://www.google.com/search?q=%E5%8F%B0%E7%A9%8D%E9%9B%BB&sca_esv=9dac49f0ebffbd81&sca_upv=1&rlz=1C5CHFA_enTW1068TW1068&tbm=nws&prmd=nsvimbtz&sxsrf=ADLYWIKkw5MBQ97EKrduM1hySfr5u08RsQ:1717147783075&ei=h5hZZo6QBNWV2roPg6GzoAM&start=10&sa=N&ved=2ahUKEwjO74v9ybeGAxXVilYBHYPQDDQQ8tMDegQIAhAE&biw=1140&bih=867&dpr=2
# https://www.google.com/search?q=%E5%8F%B0%E7%A9%8D%E9%9B%BB&tbs=cdr:1&tbm=nws&start=1
def fetch_news_for_date(date, stock_name):
    date_formatted = date.strftime('%m/%d/%Y').lstrip("0").replace(" 0", " ")
    url = f"https://www.google.com/search?q={stock_name}&tbs=cdr:1,cd_min:{date_formatted},cd_max:{date_formatted}&tbm=nws&start=0"
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Safari/537.36"
    }

    for _ in range(3):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.find_all('div', class_='n0jPhd ynAwRc MBeuO nDgy9d')
            headlines = [element.text for element in elements]
            return date_formatted, headlines
        except requests.RequestException as e:
            print(f"錯誤獲取新聞 {date_formatted}: {e}")
            time.sleep(random.uniform(1, 3))
    return date_formatted, []

def crawl_google_news_headlines(start_date, end_date, stock_name):
    headlines_by_date = {}
    dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_news_for_date, date, stock_name) for date in dates]
        for future in concurrent.futures.as_completed(futures):
            date_formatted, headlines = future.result()
            date_formatted2 = datetime.strptime(date_formatted, '%m/%d/%Y').strftime('%Y%m%d')
            headlines_by_date[date_formatted2] = headlines

    return headlines_by_date

def read_last_date():
    file_path = 'last_date.csv'
    if os.path.exists(file_path):
        with open(file_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    yyyy, mm, dd = map(int, row)
                    return datetime(yyyy, mm, dd)
    return None

def write_last_date(date):
    file_path = 'last_date.csv'
    yyyy = date.year
    mm = date.month
    dd = date.day
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([yyyy, mm, dd])

