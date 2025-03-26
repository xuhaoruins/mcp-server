https://github.com/user-attachments/assets/f72e1f7d-3c84-4429-a465-23dff3d3bd63


# Getting Started

## Set Up Environment Variables:

```sh
touch .env
```

Add the following inside `.env` at the root:

```sh
LANGSMITH_API_KEY=lsv2_...
```

Next, create another `.env` file inside the `agent` folder:

```sh
cd agent
touch .env
```

Add the following inside `agent/.env`:

```sh
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
```

## Development

We recommend running the **frontend and agent separately** in different terminals to debug errors and logs:

```bash
# Terminal 1 - Frontend
pnpm run dev-frontend

# Terminal 2 - Agent
pnpm run dev-agent
```

Alternatively, you can run both services together with:

```bash
pnpm run dev
```

Then, open [http://localhost:3000](http://localhost:3000) in your browser.

## Architecture

The codebase is split into two main parts:

1. `/agent` **folder** – A LangGraph agent that connects to MCP servers and calls their tools.
2. `/app` **folder** – A frontend application using CopilotKit for UI and state synchronization.

# MCP Agent

Model Context Protocol (MCP) 智能代理服务，提供多种工具接口，包括法律信息查询、天气数据、Azure价格查询等功能。

## 功能概述

此代理服务通过LangGraph和Model Context Protocol (MCP)提供以下功能：

- **基础工具**：数学计算（加法、乘法）
- **连接到外部MCP服务**：通过配置可连接到提供更丰富功能的MCP服务器，包括：
  - **法律信息查询**：中国刑法条款查询
  - **天气预报**：美国各州天气警报和天气预报查询
  - **Azure价格查询**：通过OData表达式查询Azure服务价格
  - **实用工具**：中文字数统计等

## 前提条件

- Python 3.10 或更高版本
- Poetry 包管理器
- GitHub API Token (用于访问GitHub Copilot模型)
- Azure容器服务(可选，用于部署)

## 环境变量设置

在代理根目录下创建 `.env` 文件，包含以下环境变量:

```
# 必需的环境变量
GITHUB_TOKEN=your_github_token_here
GITHUB_MODEL_NAME=your_github_model_name_here

# 可选环境变量
LANGSMITH_API_KEY=your_langsmith_api_key  # 用于追踪和监控
```

## 本地开发

### 使用Poetry安装依赖

```bash
cd agent
poetry install
```

### 启动代理服务

```bash
poetry run langgraph dev
```

服务将在 http://localhost:8123 上运行。

### 自定义MCP配置

代理默认连接到math_server.py提供的基础数学工具。要连接到其他MCP服务器，可在AgentState初始化时提供mcp_config配置：

```python
# 连接到本地MCP服务器示例
mcp_config = {
    "math": {
        "transport": "stdio",
        "command": "python",
        "args": ["math_server.py"],
    },
    "legal": {
        "transport": "sse",
        "url": "http://localhost:8080/sse",
    }
}
```

## Docker构建与运行

### 构建Docker镜像

```bash
cd agent
docker build -t mcp-agent .
```

### 运行Docker容器

```bash
docker run -p 8123:8123 --env-file .env mcp-agent
```

## Azure部署选项

### 1. 部署到Azure Container Registry (ACR)

```bash
# 登录到Azure
az login

# 创建资源组(如果不存在)
az group create --name myResourceGroup --location eastasia

# 创建容器注册表
az acr create --resource-group myResourceGroup --name myacrregistry --sku Basic

# 登录到容器注册表
az acr login --name myacrregistry

# 标记镜像
docker tag mcp-agent myacrregistry.azurecr.io/mcp-agent:latest

# 推送镜像到ACR
docker push myacrregistry.azurecr.io/mcp-agent:latest
```

### 2. 部署到Azure Container Apps

```bash
# 创建环境
az containerapp env create \
  --name my-environment \
  --resource-group myResourceGroup \
  --location eastasia

# 从ACR创建容器应用
az containerapp create \
  --name mcp-agent-app \
  --resource-group myResourceGroup \
  --environment my-environment \
  --image myacrregistry.azurecr.io/mcp-agent:latest \
  --registry-server myacrregistry.azurecr.io \
  --target-port 8123 \
  --ingress external \
  --env-vars GITHUB_TOKEN=secretref:githubtoken \
             GITHUB_MODEL_NAME=secretref:githubmodelname
```

### 3. 部署到Azure Web App

```bash
# 创建App Service计划
az appservice plan create --name myAppServicePlan \
  --resource-group myResourceGroup \
  --sku B1 \
  --is-linux

# 创建Web App
az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name my-mcp-agent-app \
  --deployment-container-image-name myacrregistry.azurecr.io/mcp-agent:latest

# 配置环境变量
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name my-mcp-agent-app \
  --settings GITHUB_TOKEN=your_github_token \
             GITHUB_MODEL_NAME=your_github_model_name

# 配置容器设置
az webapp config container set \
  --resource-group myResourceGroup \
  --name my-mcp-agent-app \
  --docker-registry-server-url https://myacrregistry.azurecr.io \
  --docker-custom-image-name myacrregistry.azurecr.io/mcp-agent:latest
```

## 持续集成/持续部署

本项目包含GitHub Actions工作流程配置，可在代码推送到main分支时自动构建和部署Docker镜像到Azure Container Registry。

查看 `.github/workflows/action-to-acr.yml` 文件了解详细配置。

## 推荐部署架构

针对生产环境，推荐以下部署架构：

1. 将MCP Agent部署到Azure Container Apps
2. 将MCP Server部署到单独的Azure Container Apps实例
3. 使用Azure Key Vault存储敏感凭据
4. 使用Azure Application Insights进行监控
5. 使用Azure Log Analytics收集日志

## 故障排除

### 常见问题

- **连接超时**：检查MCP服务器URL是否正确且服务器是否在运行
- **认证失败**：确保GITHUB_TOKEN环境变量设置正确且有效
- **部署失败**：检查Azure服务的日志以获取详细错误信息

### 日志查看

```bash
# 查看Azure Container Apps的日志
az containerapp logs show --name mcp-agent-app --resource-group myResourceGroup

# 查看Azure Web App的日志
az webapp log tail --name my-mcp-agent-app --resource-group myResourceGroup
```

## 参考资料

- [LangGraph文档](https://github.com/langchain-ai/langgraph)
- [Model Context Protocol规范](https://github.com/Microsoft/MCP)
- [Azure Container Apps文档](https://docs.microsoft.com/azure/container-apps/)
- [Azure Container Registry文档](https://docs.microsoft.com/azure/container-registry/)
