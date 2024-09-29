from flask import Flask, render_template, request, jsonify , Response, stream_with_context
import news_title
from run_mutate_TX import analy, mutate, eval
from tqdm import tqdm

import os
import time
import random
import json
import textwrap
import math
import csv

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import requests
from bs4 import BeautifulSoup
import concurrent.futures

import pandas as pd
import numpy as np

from IPython.display import display, Markdown

from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import google.generativeai as genai
from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from google.generativeai.types import HarmBlockThreshold
from google.ai.generativelanguage_v1 import HarmCategory

import os
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from IPython.display import display
from IPython.display import Markdown

current_file_path = os.path.abspath(__file__)

print(f"Current file path: {current_file_path}")

app = Flask(__name__)

@app.route("/model.html")
def model():
    return render_template("model.html")

@app.route("/predict.html")
def predict():
    return render_template("predict.html")

@app.route("/about.html")
def about():
    return render_template("about.html")

@app.route("/contact.html")
def contact():
    return render_template("contact.html")

@app.route("/index.html")
def index():
    return render_template("index.html")

@app.route("/crawl.html")
def crawl():
    return render_template("crawl.html")

@app.route("/")
def root():
    return render_template("index.html")

# SSE，用來發送進度
@app.route("/progress")
def progress():
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

    def crawl_google_news_headlines(start_date, end_date, stock_name, existing_data):
        headlines_by_date = existing_data.copy()
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        dates_to_fetch = [date for date in dates if date.strftime('%Y%m%d') not in headlines_by_date]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(fetch_news_for_date, date, stock_name): date for date in dates_to_fetch}
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc=f"爬取 {stock_name} 的新聞"):
                date_formatted, headlines = future.result()
                date_formatted2 = datetime.strptime(date_formatted, '%m/%d/%Y').strftime('%Y%m%d')
                headlines_by_date[date_formatted2] = headlines

        return headlines_by_date

    def generate():
        print("開始抓取新聞")
        data = [
            ["2330", "台積電", "31.7881%"],
            ["2317", "鴻海", "3.3553%"],
            ["2454", "聯發科", "2.462%"],
            ["2382", "廣達", "1.5581%"],
            ["2412", "中華電", "1.4924%"],
            ["2881", "富邦金", "1.3953%"],
            ["2308", "台達電", "1.2916%"],
            ["2882", "國泰金", "1.1493%"],
            ["6505", "台塑化", "1.0671%"],
            ["2891", "中信金", "1.0382%"]
        ]

        end_date = datetime.now() - timedelta(days=1)
        start_date = datetime(2023, 6, 1)  # 根據您的應用修改
        news_preview = "權值股的熱門新聞標題"
        path_preview = "static/predict_preview.json"

        for idx, stock in enumerate(data):
            stock_name = stock[1]
            # 模擬抓取新聞，實際上這裡調用您的抓取函數
            time.sleep(1)  # 假設每家公司需要 1 秒來爬取新聞
            path = os.path.join("history_data", "tw", "news_title", stock[0] + "news_title.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # 讀取現有的 JSON 檔案
            if os.path.exists(path):
                with open(path, "r", encoding="UTF-8") as f:
                    existing_data = json.load(f)
            else:
                existing_data = {}

            # 爬取缺少的資料
            headlines = crawl_google_news_headlines(start_date, end_date, stock_name, existing_data)

            # 將資料按照日期排序
            sorted_headlines = dict(sorted(headlines.items()))
            json_content = json.dumps(sorted_headlines, ensure_ascii=False, indent=4)

            # 取得最後一天的資料
            # 將字符串轉換為 JSON 物件
            json_data = json.loads(json_content)
            news_preview += f"{json_data[end_date.strftime('%Y%m%d')]} \n"

            with open(path , "w", encoding="UTF-8") as f:
                f.write(json_content)

            with open(path_preview, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            file_data["newsInput"] = news_preview
            with open(path_preview, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=4)

            yield f"data: 已更新 {stock_name} ({idx + 1}/{len(data)})\n\n"
        yield "data: 抓取完成!\n\n"

        

    return Response(stream_with_context(generate()), content_type='text/event-stream')

# 主路由，用來開始抓取新聞
@app.route("/news_title_submit", methods=["GET", "POST"])
def news_title_submit():
    return jsonify({'message': "開始抓取新聞!"})

    
@app.route("/run_model",methods=["GET", "POST"])
def run_model():
    try:
        # 從請求中獲取日期
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        target_value = float(request.args.get('target_value'))
        modelType = request.args.get('modelType')
        print("Now running:  " + modelType)
        
        # 解析日期
        start_day = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_day = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # 檢查目標值範圍
        if target_value < 0 or target_value > 1:
            return jsonify({'message': '訓練目標值必須在0到1之間'}), 400
        
        load_dotenv()

        if modelType == "gpt-4o":
            print("Using OpenAI model")
            llm = ChatOpenAI(
            openai_api_key = os.getenv('OPENAI_API_KEY'),
            model="gpt-4o",
            temperature=1,
            top_p=0.9,
            seed=0,
            )
        else:
            print("Using Google model")
            llm = ChatGoogleGenerativeAI(
                            #https://aistudio.google.com/app/u/1/apikey #api key查詢
                            google_api_key = os.getenv('GOOGLE_API_KEY'),
                            model='gemini-1.5-flash',
                            temperature=1,
                            top_p=0.9,
                            seed=0,
                            safety_settings={
                                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT : HarmBlockThreshold.BLOCK_NONE,
                            
                        })
        
        # 初始化
        run_count = 1
        #start_day = datetime(2024, 5, 15)
        #end_day = datetime(2024, 5, 30)
        stock_ids = ['2308', '2317', '2330', '2382', '2412', '2454', '2881', '2882', '2891', '6505']
        init_acc = 0
        acc = 0
        init_prompt = """
        讓我們一步一步來
        利多需要滿足以下條件：
        企業創新策略：這是所有句子的核心主題，無論是滿足客戶需求、吸引投資者，還是促進股價增長，都是基於企業的創新策略。
        滿足客戶需求：客戶需求是企業創新的首要驅動力，能否滿足客戶需求直接影響創新成敗。
        吸引投資者關注：投資者的關注和信心能為企業提供必要的資金和支持，也是創新成功的重要標誌。
        """
        prompt_stack = [(init_prompt, acc)]  # 初始prompt和準確率加入stack
        mutate_count = 0  # 記錄變異次數
        out_folder = "out_mutate_tx/test/"

        current_prompt, init_acc = prompt_stack[-1]

        # 主迴圈
        while prompt_stack:
            print(f"Run count: {run_count}")
            current_prompt, _ = prompt_stack[-1]  # 取得stack頂部的prompt和準確率
            mutate_prompt = init_prompt
            mutate_prompt = mutate(current_prompt, modelType, llm)  # 生成變異prompt
            outpath = analy(stock_ids, start_day, end_day, current_prompt, mutate_prompt, out_folder, llm)
            acc, ev = eval(outpath)
            mutate_count += 1

            # 將新的prompt和準確率加入stack，並按準確率排序
            prompt_stack.append((mutate_prompt, acc))
            prompt_stack.sort(key=lambda x: x[1])  # 按準確率由低至高排序

            # 有比stack更高的準確率則將 counter 重置
            if acc > _:
                init_acc = acc
                mutate_count = 0  # 重置變異次數計數器
                print(f"Update prompt with accuracy: {acc}")

            if len(prompt_stack) > 1 and mutate_count >= 5:
                prompt_stack.pop()  # 移除準確率最高的prompt 避免local minimum
                mutate_count = 0  # 重置變異次數計數器
                print("Remove top prompt due to no improvement after 5 mutations.")
            elif acc > 0.9:
                acc = 0.6
                prompt_stack.pop()  # 移除準確率最高的prompt 避免local minimum
                mutate_count = 0  # 重置變異次數計數器
                print("Remove top prompt due to accuracy over 0.9.")
            elif len(prompt_stack) == 1:
                # 如果stack只剩下一個prompt，移除變異次數限制
                mutate_count = 0
                print("Single prompt in stack, removing mutation limit.")
            
            path_prewiew = "static/predict_preview.json"
            with open(path_prewiew, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            # 放表現最好的prompt
            file_data["promptInput"] = prompt_stack[-1][0]
            with open(path_prewiew, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, ensure_ascii=False, indent=4)
            
            if acc >= target_value:
                #print("============ prompt ==========")
                with open(outpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    #print(data["mutate_prompt"])
                return {'message':"Prompt:"+data["mutate_prompt"]+"\nAccuracy:"+str(acc*100)+"%"}
                #print("==============================")
            # return {'message':"accuracy smaller than target value please training longer or give more data."}

    except Exception as e:
        error_msg = f"Failed to run model: {str(e)}"
        return {'message':error_msg}


       

@app.route("/twii_submit",methods=["GET", "POST"])
def twii_submit():
    try:
        # setting #######################################################
        end_year = 2024                         # 資料抓到這一年
        #csv_file_path = 'history_data\tw\twii_history.csv'    # 有過去資料的檔案
        #################################################################
        # 獲取當前工作目錄
        current_directory = os.getcwd()
        print(f"Current directory: {current_directory}")

        # 相對路徑
        relative_path = 'history_data/tw/twii_history.csv'

        # 拼接並打印絕對路徑
        csv_file_path = os.path.abspath(relative_path)
        print(f"Full path: {csv_file_path}")

        # 用with語句開啟檔案，確保在使用完後自動關閉
        with open(csv_file_path, 'r', encoding='utf-8') as file:
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
        return {'message': "success update twii"}
    except Exception as e:
        error_msg = f"Failed to update twii: {str(e)}"
        return {'message':error_msg}
    
    
@app.route("/predict_stock", methods=["GET", "POST"])
def predict_stock():
    try:
        model = 'gemini-1.5-flash'
        temperature = 1
        top_p = 0.9
        seed = 0
        load_dotenv()

        llm = ChatGoogleGenerativeAI(
                        #https://aistudio.google.com/app/u/1/apikey #api key查詢
                        google_api_key = os.getenv('GOOGLE_API_KEY'),
                        model=model,
                        temperature=temperature,
                        top_p=top_p,
                        seed=seed,
                        safety_settings={
                                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT : HarmBlockThreshold.BLOCK_NONE,
                        
                    })
        # 從請求中獲取prompt
        prompt_in = request.args.get('prompt')
        news_in = request.args.get('news')
        
        messages = [
            ("human",
            f"""
            以下是台灣股市權值股的新聞標題，
            {news_in}

            請依據以下判斷依據判斷權值股對大盤（實際操作使用台指期）隔日開盤時買進收盤時賣出的獲利可能性
            {prompt_in}
                
            請綜合以上資訊，判斷明日當沖台指期是否可能獲利，有可能請則只回答#yes，否則只回答#no，如果無關則回答#unknown，請盡量不要回答 #unknown
            """)
        ]
        response = llm.invoke(messages)
        response_content = response.content  # 回覆的內容
        print(response_content)

        return jsonify({'content': response_content, 'message': 'success predict'})
    except Exception as e:
        error_msg = f"Failed to predict: {str(e)}"
        return jsonify({'message': error_msg}), 500
    
    
if __name__ == '__main__':
    #定義app在8080埠運行
    app.run(host="0.0.0.0",port=8000,debug=True)
    


