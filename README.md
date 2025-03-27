# Distributed MCP Server

A Model Context Protocol (MCP) server providing tool interfaces for legal information queries, weather data, Azure pricing, and utility functions.

## Overview

This server offers API tools that can be used by Microsoft Copilot or other AI assistants supporting the MCP protocol:

### Legal Information Tools
- **Get Article Information**: Query Chinese criminal law articles by code
- **Content Search**: Find relevant criminal law articles by keywords
- **Article Name Query**: Look up legal information by article or offense name
- **Specific Paragraph Retrieval**: Get specific paragraphs from articles
- **Get Full Content**: Get the complete content of Chinese criminal law

### Weather and Utility Tools
- **Weather Alerts**: Get US state weather alerts
- **Weather Forecast**: Get weather forecasts using latitude and longitude
- **Azure Price Query**: Query Azure service prices with OData filters
- **Chinese Character Count**: Count Chinese characters in text

## Technical Stack

- FastMCP framework for MCP protocol support
- Uvicorn ASGI server
- FastAPI/Starlette web framework
- SSE (Server-Sent Events) for communication

## Requirements
- Python 3.10 or higher
- Docker (optional, for containerized deployment)

## Installation

### Local Development:
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Deploy Azure Function
For the Chinese character counting function:
1. Open the function directory in VSCode:
   ```bash
   cd function
   ```
2. Deploy using the Azure Functions extension

## Usage

### Starting the Server
```bash
python mcp-server.py --host 0.0.0.0 --port 8080
```
The server will run at http://localhost:8080.

### Available Endpoints
- `/sse` - Server-Sent Events endpoint
- `/messages/` - MCP message processing endpoint

### Tool Usage Examples
```
# Query criminal law
Please look up Article 133 of the Criminal Law.

# Check weather
Are there any weather alerts in New York?

# Count Chinese characters
How many Chinese characters are in: 人工智能正在改变我们的生活方式。
```

## Docker Setup

### Build Image
```bash
docker build -t mcp-server .
```

### Run Container
```bash
docker run -p 8080:8080 --env-file .env mcp-server
```

## Azure Deployment Options

### 1. Azure Container Registry (ACR)
```bash
az login
az group create --name myResourceGroup --location eastasia
az acr create --resource-group myResourceGroup --name myacrregistry --sku Basic
az acr login --name myacrregistry
docker tag mcp-server myacrregistry.azurecr.io/mcp-server:latest
docker push myacrregistry.azurecr.io/mcp-server:latest
```

### 2. Azure Container Apps
```bash
az containerapp env create \
  --name my-environment \
  --resource-group myResourceGroup \
  --location eastasia

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

### 3. Azure Web App
```bash
az appservice plan create --name myAppServicePlan \
  --resource-group myResourceGroup \
  --sku B1 \
  --is-linux

az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name my-mcp-server-app \
  --deployment-container-image-name myacrregistry.azurecr.io/mcp-server:latest

az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name my-mcp-server-app \
  --settings MONGODB_CONNECTION_STRING=your_mongodb_connection_string \
             AZURE_OPENAI_API_KEY=your_azure_openai_api_key

az webapp config container set \
  --resource-group myResourceGroup \
  --name my-mcp-server-app \
  --docker-registry-server-url https://myacrregistry.azurecr.io \
  --docker-custom-image-name myacrregistry.azurecr.io/mcp-server:latest
```

## CI/CD
This project uses GitHub Actions to build Docker images and publish them to Azure Container Registry.
See `.github/workflows/action-to-acr.yml` for details.

## Recommended Architecture
For production:
1. Deploy to Azure Container Apps for auto-scaling
2. Deploy Azure Functions separately
3. Use Application Insights for monitoring
4. Use Azure Front Door for CDN and security

## Adding New Tools
```python
@mcp.tool()
async def my_new_tool(param1: str, param2: int = None) -> str:
    """Tool description.
  
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
    """
    try:
        # Your code here
        return "Result"
    except Exception as e:
        return f"Error: {str(e)}"
```

## Troubleshooting

### Database Issues
- Verify MongoDB connection string format
- For Cosmos DB, ensure vector search support

### Azure OpenAI Issues
- Check API key and endpoint
- Verify model deployment name

### Viewing Logs
```bash
# Container Apps logs
az containerapp logs show --name mcp-server-app --resource-group myResourceGroup
# Web App logs
az webapp log tail --name my-mcp-server-app --resource-group myResourceGroup
# Function logs
az functionapp log tail --name haxufunctions --resource-group myResourceGroup
```

## Security Best Practices
1. Store credentials in Azure Key Vault
2. Configure proper API authentication
3. Keep dependencies updated
4. Enable diagnostic logs
5. Use least privilege principle for service identities

## References
- [Model Context Protocol](https://github.com/microsoft/mcp)
- [FastMCP](https://github.com/microsoft/fastmcp)
- [Azure Container Apps](https://docs.microsoft.com/azure/container-apps/)
- [Azure Functions](https://docs.microsoft.com/azure/azure-functions/)
- [Azure Cosmos DB](https://docs.microsoft.com/azure/cosmos-db/)
