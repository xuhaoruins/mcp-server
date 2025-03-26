# 分布式MCP Server

Model Context Protocol (MCP) 服务器，提供各种工具接口，包括法律信息查询、天气数据、Azure价格查询以及实用工具等功能。

## 功能概述

此MCP服务器提供一组API工具，可被Microsoft Copilot或其他支持MCP协议的AI助手使用，以访问和查询各种信息源：

### 法律信息工具

- **获取条款信息**：通过条款代码查询中国刑法条款
- **内容搜索**：通过关键词在刑法中搜索相关条款
- **条款名称查询**：通过条款名称或罪名查询法律信息
- **特定段落获取**：获取特定条款的特定段落
- **获取全部内容**：获取中国刑法的全部内容

### 天气与实用工具

- **获取天气预警**：获取美国各州的天气预警信息
- **获取天气预报**：通过经纬度获取特定位置的天气预报
- **Azure价格查询**：使用OData过滤表达式查询Azure服务价格
- **中文字数统计**：统计文本中的中文字符数量

## 技术架构

本服务器基于以下技术构建：

- FastMCP框架：用于MCP协议支持
- Uvicorn：ASGI服务器
- FastAPI/Starlette：Web框架
- SSE (Server-Sent Events)：用于服务端与客户端通信

## 前提条件

- Python 3.10 或更高版本
- Docker (可选，用于容器化部署)

## 安装指南

### 本地开发环境克隆代码库：

1. ```bash
   git clone <repository-url>
   cd mcp-server
   ```
2. 创建并激活虚拟环境：

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

### 部署Azure Function

项目包含一个用于中文字数统计的Azure Function。部署步骤：

1. 在VSCode中打开function目录：

   ```bash
   cd function
   ```
2. 使用Azure Functions扩展部署Function App

## 使用方法

### 启动服务器

使用以下命令启动MCP服务器：

```bash
python mcp-server.py --host 0.0.0.0 --port 8080
```

服务器将在 http://localhost:8080 上运行。

### 可用端点

- `/sse` - 用于MCP通信的Server-Sent Events端点
- `/messages/` - MCP消息处理端点

### 调用工具示例

以下是如何通过与MCP服务器集成的AI助手调用工具的示例：

```
# 查询刑法条款
请帮我查询刑法第133条的内容。

# 查询天气信息
纽约现在有什么天气预警吗？

# 计算中文字数
这段文字有多少个汉字：人工智能正在改变我们的生活方式。
```

## Docker构建与运行

### 构建Docker镜像

```bash
docker build -t mcp-server .
```

### 运行Docker容器

```bash
docker run -p 8080:8080 --env-file .env mcp-server
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
docker tag mcp-server myacrregistry.azurecr.io/mcp-server:latest

# 推送镜像到ACR
docker push myacrregistry.azurecr.io/mcp-server:latest
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
  --name mcp-server-app \
  --resource-group myResourceGroup \
  --environment my-environment \
  --image myacrregistry.azurecr.io/mcp-server:latest \
  --registry-server myacrregistry.azurecr.io \
  --target-port 8080 \
  --ingress external \
  --env-vars MONGODB_CONNECTION_STRING=secretref:mongodbconnection \
             AZURE_OPENAI_API_KEY=secretref:azureopenaikey
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
  --name my-mcp-server-app \
  --deployment-container-image-name myacrregistry.azurecr.io/mcp-server:latest

# 配置环境变量
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name my-mcp-server-app \
  --settings MONGODB_CONNECTION_STRING=your_mongodb_connection_string \
             AZURE_OPENAI_API_KEY=your_azure_openai_api_key

# 配置容器设置
az webapp config container set \
  --resource-group myResourceGroup \
  --name my-mcp-server-app \
  --docker-registry-server-url https://myacrregistry.azurecr.io \
  --docker-custom-image-name myacrregistry.azurecr.io/mcp-server:latest
```

## 持续集成/持续部署

本项目已配置GitHub Actions工作流，可自动构建Docker镜像并发布到Azure Container Registry。

查看 `.github/workflows/action-to-acr.yml` 文件了解详细配置。

## 架构推荐

对于生产环境，推荐以下部署架构：

1. MCP服务器部署到Azure Container Apps，提供自动扩展能力
2. Azure函数部署在单独的Function App中
3. 使用Azure Application Insights进行监控
4. 使用Azure Front Door作为前端，提供CDN和安全功能

## 添加新工具

要向服务器添加新工具：

1. 在 `mcp-server.py`中定义新的带有 `@mcp.tool()`装饰器的异步函数
2. 在函数内实现功能逻辑
3. 添加适当的错误处理
4. 重启服务器以使新工具可用

```python
@mcp.tool()
async def my_new_tool(param1: str, param2: int = None) -> str:
    """Tool description that will be shown to the user.
  
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
    """
    try:
        # 实现功能逻辑
        return "结果数据"
    except Exception as e:
        return f"Error: {str(e)}"
```

## 故障排除

### 数据库连接问题

- 确保MongoDB连接字符串格式正确
- 对于Azure Cosmos DB，确保集群支持向量搜索或使用回退选项

### Azure OpenAI API问题

- 验证API密钥和端点是否正确
- 检查模型部署名称是否与环境变量中指定的匹配

### 日志查看

```bash
# 查看Azure Container Apps的日志
az containerapp logs show --name mcp-server-app --resource-group myResourceGroup

# 查看Azure Web App的日志
az webapp log tail --name my-mcp-server-app --resource-group myResourceGroup

# 查看Azure Function的日志
az functionapp log tail --name haxufunctions --resource-group myResourceGroup
```

## 安全最佳实践

1. 使用Azure Key Vault存储所有敏感凭据
2. 为API端点配置适当的认证机制
3. 定期更新依赖包以修复安全漏洞
4. 启用Azure服务的诊断日志
5. 使用最小权限原则配置服务身份

## 参考资料

- [Model Context Protocol规范](https://github.com/microsoft/mcp)
- [FastMCP文档](https://github.com/microsoft/fastmcp)
- [Azure容器应用文档](https://docs.microsoft.com/azure/container-apps/)
- [Azure Functions文档](https://docs.microsoft.com/azure/azure-functions/)
- [Azure Cosmos DB文档](https://docs.microsoft.com/azure/cosmos-db/)
