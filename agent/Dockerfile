# 使用官方的 Python 3.12 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-distutils \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# 将 Poetry 添加到 PATH
ENV PATH="/root/.local/bin:$PATH"

# 复制项目文件到容器中
COPY pyproject.toml poetry.lock /app/

# 确保 lock 文件是最新的
RUN poetry lock --no-interaction

# 安装项目依赖
RUN poetry install --no-root

# 复制其余项目文件
COPY . /app

# 暴露端口（与启动命令一致）
EXPOSE 8123

# 定义容器启动时的默认命令
CMD ["poetry", "run", "langgraph", "dev", "--host", "0.0.0.0", "--port", "8123", "--no-browser"]