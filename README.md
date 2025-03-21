# MCP Server

A Microsoft Copilot Plugin (MCP) server that provides various tools for querying information, including legal documents, Microsoft product licensing, weather data, and Azure pricing.

## Overview

This server provides a set of API tools that can be used by Microsoft Copilot to access and query various information sources:

- **Legal Information**: Query the Chinese Criminal Law articles and provisions
- **Microsoft Product Licensing**: Get information about licensing for various Microsoft products (Visual Studio, SQL Server, Windows Server, Microsoft 365, Dynamics 365)
- **Privacy Regulations**: Query information about GDPR and China's Personal Information Protection Law
- **Weather Data**: Get weather alerts and forecasts for locations in the United States
- **Azure Pricing**: Query Azure pricing information using OData filter expressions
- **Utility Tools**: Count Chinese characters in a text string

The server uses LlamaIndex for vector search and retrieval, Azure OpenAI for embeddings and language model capabilities, and MongoDB/Azure Cosmos DB for vector storage.

## Prerequisites

- Python 3.12 or higher
- MongoDB or Azure Cosmos DB with MongoDB API
- Azure OpenAI API access
- Docker (optional, for containerized deployment)

## Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-server
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```
   MONGODB_CONNECTION_STRING="your_mongodb_connection_string"
   AZURE_OPENAI_API_KEY="your_azure_openai_api_key"
   AZURE_OPENAI_ENDPOINT="your_azure_openai_endpoint"
   AZURE_OPENAI_CHAT_MODEL="gpt-4"
   AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-ada-002"
   AZURE_OPENAI_TEMPERATURE="0.1"
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t mcp-server .
   ```

2. Run the container:
   ```bash
   docker run -p 8080:8080 --env-file .env mcp-server
   ```

## Usage

### Starting the Server

Start the server with:

```bash
python mcp-server.py --host 0.0.0.0 --port 8080
```

The server will be available at `http://localhost:8080`.

### Available Endpoints

- `/sse` - Server-Sent Events endpoint for MCP communication
- `/messages/` - MCP message handling endpoint

### Available Tools

The server provides the following tools:

#### Licensing Information Tools
- `query_visual_studio_license` - Get information about Visual Studio 2022 licensing
- `query_sql_server_license` - Get information about SQL Server 2022 licensing
- `query_windows_server_license` - Get information about Windows Server 2022 licensing
- `query_m365_license` - Get information about Microsoft 365 Enterprise licensing
- `query_dynamics365_license` - Get information about Dynamics 365 licensing

#### Privacy Regulation Tools
- `query_gdpr` - Get information about GDPR regulations
- `query_china_pipl` - Get information about China's Personal Information Protection Law

#### Legal Information Tools
- `get_article_by_code` - Get information by article code from Chinese Criminal Law
- `search_by_content` - Search for legal articles by content
- `get_by_article_name` - Get legal information by article name/cause of action
- `get_specific_article` - Get a specific paragraph from an article
- `get_all_law_contents` - Get all contents of the Chinese Criminal Law

#### Weather and Utility Tools
- `get_alerts` - Get weather alerts for a US state
- `get_forecast` - Get weather forecast for a location
- `get_azure_price` - Get Azure price for a service using OData filter expressions
- `count_chinese_characters` - Count the number of Chinese characters in a string

## Development

### Adding New Tools

To add a new tool to the server:

1. Define a new async function with the `@mcp.tool()` decorator in `mcp-server.py`
2. Implement the functionality within the function
3. Add appropriate error handling
4. Restart the server to make the new tool available

## Troubleshooting

### MongoDB Connection Issues

- Ensure the MongoDB connection string is correctly formatted
- For Azure Cosmos DB, make sure the cluster supports vector search or use the fallback option

### Azure OpenAI API Issues

- Verify that your API key and endpoint are correct
- Check if the model deployment names match those specified in your environment variables

## License

[Your License Information]

## Contact

[Your Contact Information]