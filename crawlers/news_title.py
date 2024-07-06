import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import concurrent.futures
import time
import random
import json

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

data = [
    # ["2330", "台積電", "31.7881%"],
    # ["2317", "鴻海", "3.3553%"],
    # ["2454", "聯發科", "2.462%"],
    # ["2382", "廣達", "1.5581%"],
    # ["2412", "中華電", "1.4924%"],
    # ["2881", "富邦金", "1.3953%"],
    # ["2308", "台達電", "1.2916%"],
    # ["2882", "國泰金", "1.1493%"],
    # ["6505", "台塑化", "1.0671%"],
    # ["2891", "中信金", "1.0382%"]
]

# 抓資料存到 json 檔
start_date = datetime(2023, 6, 1)
end_date = datetime(2024, 5, 30)

for idx, stock in enumerate(data):
    stock_name = stock[1]
    headlines = crawl_google_news_headlines(start_date, end_date, stock_name)
    json_content = json.dumps(headlines, ensure_ascii=False, indent=4)

    path = os.path.join("news_title", stock[0] + "news_title.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path , "w", encoding="UTF-8") as f:
        f.write(json_content)