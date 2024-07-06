## todo list
UI/UX  
企劃書  
系統需求書  
Demo 影片  

# Gen-AI Stock Master

LLM-Predict-Stock 是一個強大的股票預測工具，它使用先進的機器學習技術來預測股票價格。

## 目錄
- [Crawler](crawlers)
- [History Data](history_data)
- [變異程式](run_mutate_TX.ipynb)

## Crawler 🕷️
爬取過去的股票資訊，跟新聞標題

## History Data 📈
- twii_history：期交所公布的台指期貨的每日價格
- news_title：從google 新聞爬股市新聞標題

## 變異程式 🧑🏻‍💻
設定初始的prompt 判斷漲跌並計算其準確率和期望值  
再拿最高的年化報酬率的prompt變異
建立stack 將prompt 依序由表現好排到表現差
然後將比較好的拿來變異
最好的promt變異五次如果準確率沒有提升，便將其刪除，改用第二好的prompt
