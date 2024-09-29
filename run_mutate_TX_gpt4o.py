import os
import textwrap
import math
import pandas as pd
import numpy as np

from datetime import datetime
from dateutil.relativedelta import relativedelta

from langchain.schema.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from IPython.display import display
from IPython.display import Markdown

# model = 'gpt-4o'
model = 'gpt-4o'
temperature = 1
top_p = 0.9
seed = 0

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

llm = ChatOpenAI(
            openai_api_key = os.getenv('OPENAI_API_KEY'),
            model=model,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            )

'''--------------------------------------------------------------------------------------------------------------'''
import pandas as pd
import json
import os

def eval(out_file):
    # 計算準確率和平均報酬率
    gain = []
    loss = []

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    token_input = 0
    token_output = 0

    path_price_his = (os.path.abspath(os.getcwd())) + "/history_data/tw/twii_history.csv"
    df_price_his = pd.read_csv(path_price_his, encoding='utf-8')
    df_price_his['日期'] = pd.to_datetime(df_price_his['日期'], format='%Y%m%d')

    with open(out_file, "r", encoding='utf-8') as f:
        data = json.load(f)
        output_data = data["output_data"]

        for date_str, result in output_data.items():
            token_input += result["token"]["input_tokens"]
            token_output += result["token"]["output_tokens"]
            sig_str = result["raw_data"]
            sig = 0

            if "unknown" in sig_str:
                sig = 0
            elif "yes" in sig_str:
                sig = 1
            elif "no" in sig_str:
                sig = -1
            else:
                sig = 0

            df_price = df_price_his[df_price_his['日期'] == pd.to_datetime(date_str, format='%Y%m%d')]

            if df_price.empty:
                continue

            rtn = (df_price.iloc[0]['收盤指數'] - df_price.iloc[0]['開盤指數']) / df_price.iloc[0]['開盤指數']

            if pd.isna(rtn):
                rtn = 0

            if sig > 0:
                if rtn > 0:
                    tp += 1
                    gain.append(rtn)
                else:
                    fp += 1
                    loss.append(rtn)
            elif sig == -1:
                if rtn < 0:
                    tn += 1
                    gain.append(-rtn)
                else:
                    fn += 1
                    loss.append(-rtn)


    
    ev = 0
    accuracy = 0
    if tp + fp + tn + fn == 0:
        accuracy = 0
        ev = 0
    elif len(gain) == 0 or len(loss) == 0:
        accuracy = (tp + tn) / (tp + fp + tn + fn)
        ev = 0
    else:
        accuracy = (tp + tn) / (tp + fp + tn + fn)
        ev = (sum(gain) / len(gain))*accuracy + (sum(loss) / len(loss))*(1-accuracy)
    print(f'tp {tp}, fp {fp}, tn {tn}, fn {fn}, total:[{tp + fp + tn + fn}/{len(output_data)}]')
    print(f'Accuracy {round(accuracy, 5)}, Expected value:{round(ev,5)}')
    # print("--------------------")
    # print(f'token: input {token_input}, output {token_output}')
    # print(f'預估費用 {(token_input/1000000)*0.35 + (token_output/1000000)*0.7} USD, {((token_input/1000000)*0.35 + (token_output/1000000)*0.7)*32.6} TWD')
    # print(f'詢問次數 {len(output_data)}')
    print()

    return accuracy, ev

'''--------------------------------------------------------------------------------------------------------------'''
# 透過前一天的新聞判斷今日的股市走勢
import time
import os
import json
import pandas as pd
from datetime import datetime, timedelta

def step1(stock_ids, st, et, init_prompt, mutate_prompt, out_folder):
    out_path = out_folder
    count = 1
    while True:
        if os.path.exists(out_path + str(count) + ".json"):
            count += 1
            continue
        else:
            out_file = out_path + str(count) + ".json"
            break

    path_price_his = (os.path.abspath(os.getcwd())) + "/history_data/tw/twii_history.csv"

    # 讀取CSV檔案
    df_price_his = pd.read_csv(path_price_his, encoding='utf-8')
    df_price_his['日期'] = pd.to_datetime(df_price_his['日期'], format='%Y%m%d')
    df_price_his = df_price_his[(st <= df_price_his['日期']) & (df_price_his['日期'] <= et)]

    idx = 1
    batch_size = 15
    output_data = {}  # 使用字典來存儲每一天的輸出數據

    while idx < len(df_price_his):
        batch = []
        for i in range(batch_size):
            if idx + i >= len(df_price_his):
                break

            # 取得前一日的日期
            news_date = df_price_his.iloc[idx + i]['日期'] 
            news_date -= timedelta(days=1)

            # 存儲所有股票的新聞資料
            text_news = ""
            for j, stock_id in enumerate(stock_ids):
                path_news_file = (os.path.abspath(os.getcwd())) + "/history_data/tw/news_title/" + stock_id + "news_title.json"
                with open(path_news_file, 'r', encoding='utf-8') as f:
                    news_data = json.load(f)
                    text_news = "權值股的熱門新聞標題"
                    text_news += f"{news_data[news_date.strftime('%Y%m%d')]} \n"

            # 設置初始消息列表，包括 SystemMessage 和第一個 HumanMessage
            messages = [
                ("system", "你是一個厲害的股市操盤手，專長是當日沖消"),
                ("human",
                f"""
                以下是台灣股市權值股的新聞標題，
                {text_news}

                請依據以下判斷依據判斷權值股對大盤（實際操作使用台指期）隔日開盤時買進收盤時賣出的獲利可能性
                {mutate_prompt}
                
                請綜合以上資訊，判斷明日當沖台指期是否可能獲利，有可能請則只回答#yes，否則只回答#no，如果無關則回答#unknown，請盡量不要回答 #unknown
                
                """)
            ]
            batch.append(messages)

        res = llm.batch(batch)

        for i in range(len(res)):
            # 被預測的日期
            date_str = df_price_his.iloc[idx + i]['日期'].strftime('%Y%m%d')
            output_data[date_str] = {
                "token": res[i].usage_metadata,
                "raw_data": res[i].content,
            }

        time.sleep(60)
        idx += batch_size

    # 將所有輸出數據寫入到同一個json檔案中
    data = {
        "model": model,
        "temperature": temperature,
        "top_p": top_p,
        "seed": seed,
        "init_prompt": init_prompt,
        "mutate_prompt": mutate_prompt,
        "output_data": output_data,
    }
    json_content = json.dumps(data, ensure_ascii=False, indent=4)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="UTF-8") as f:
        f.write(json_content)
    
    return out_file

def step2(text_in):
    messages = [
        ("human",
        f"""
        請用以下指令產生1個清晰和有條理的變體，同時保留語意：{text_in}
        """)
    ]
    response = llm.invoke(messages)
    # print(f'變異結果： {response.content}')
    time.sleep(60)
    return response.content

'''--------------------------------------------------------------------------------------------------------------'''

# 避免local minimum
from datetime import datetime
