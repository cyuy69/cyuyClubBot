# 使用輕量級 Python 映像
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 設定環境變數：確保 Python 輸出直接顯示在 Docker 日誌中，不快取
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安裝系統依賴 (如果未來需要編譯某些套件)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製所有程式碼
COPY . .

# 建立數據目錄 (確保容器內有對應資料夾)
RUN mkdir -p data

# 啟動指令
CMD ["python", "main.py"]
