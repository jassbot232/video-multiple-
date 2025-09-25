FROM python:3.9-slim

# FFmpeg install करें
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Working directory बनाएं
WORKDIR /app

# Requirements copy करें
COPY requirements.txt .

# Dependencies install करें
RUN pip install --no-cache-dir -r requirements.txt

# Source code copy करें
COPY . .

# Temp directory बनाएं
RUN mkdir -p temp_files

# Bot run करें
CMD ["python", "bot.py"]
