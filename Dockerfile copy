# 使用官方 Python 镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 创建虚拟环境
RUN python3 -m venv venv

# 设置使用虚拟环境
ENV PATH="/app/venv/bin:$PATH"

# 复制 requirements.txt 文件
COPY requirements.txt .

# 在虚拟环境中安装依赖
RUN . /app/venv/bin/activate && pip install -r requirements.txt

# 复制应用程序文件
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令（使用虚拟环境中的Python）
CMD ["/app/venv/bin/python", "mcp-server.py"]
