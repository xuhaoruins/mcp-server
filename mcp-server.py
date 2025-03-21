import uvicorn
import pymongo
import os
from typing import Any
import httpx
from urllib.parse import quote
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.routing import Mount, Route
from mcp.server import Server
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.vector_stores.azurecosmosmongo import (
    AzureCosmosDBMongoDBVectorSearch,
)
from llama_index.core import Settings

from legal_documents_cn import criminal_law_cn as law
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("haxu-mcp-server")

## init mcp sse server
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


###########################
#####llamaindex mcp tools
###########################
# MongoDB connection and client setup

connection_string = os.environ.get("MONGODB_CONNECTION_STRING", "")
# Make sure the connection string is not surrounded by quotes
if connection_string.startswith('"') and connection_string.endswith('"'):
    connection_string = connection_string[1:-1]

# Validate connection string format
if not connection_string.startswith(('mongodb://', 'mongodb+srv://')):
    print(f"Warning: Invalid MongoDB connection string format: {connection_string[:10]}...")
    # You might want to exit here if the connection is critical
    # import sys
    # sys.exit(1)

mongodb_client = pymongo.MongoClient(connection_string)

# Azure OpenAI configuration
openai_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
openai_api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
chat_model = os.environ.get("AZURE_OPENAI_CHAT_MODEL")  # 使用环境变量或默认值
embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL")
temperature = float(os.environ.get("AZURE_OPENAI_TEMPERATURE"))

def load_index(collection):
    """Load a vector index from Azure Cosmos DB MongoDB."""
    try:
        # Try using vector search first (for higher tier Cosmos DB)
        store = AzureCosmosDBMongoDBVectorSearch(
            mongodb_client=mongodb_client,
            db_name="vectordemo",
            collection_name=collection,
            index_name="default_vector_search_index",
            embedding_field="content_vector",
            # Using a more compatible configuration for lower-tier clusters
            cosmos_search_options={
                "kind": "vector-ivf",  # Changed from vector-hnsw to vector-ivf which might be supported in lower tiers
                "similarity": "COS",
                "dimensions": 1536
            }
        )
        storage_context = StorageContext.from_defaults(vector_store=store)
        index = VectorStoreIndex.from_vector_store(store, storage_context=storage_context)
        return index
    except Exception as e:
        print(f"Failed to create vector search index: {str(e)}")
        # Fallback to simple retrieval without vector search if vector search isn't available
        try:
            from llama_index.core import SimpleDirectoryReader
            from llama_index.core import Document
            
            # This is a simplified fallback - in a real application, you'd want to 
            # implement a more robust fallback strategy
            print("Using basic in-memory index as fallback...")
            documents = [Document(text=f"Unable to load vector index for {collection}. Please upgrade your Cosmos DB cluster to support vector search.")]
            index = VectorStoreIndex.from_documents(documents)
            return index
        except Exception as fallback_error:
            print(f"Fallback also failed: {str(fallback_error)}")
            raise

def setup_llm_and_embeddings(api_key=openai_api_key, api_base=openai_api_base, 
                           chat_model_name=chat_model, embed_model_name=embedding_model, 
                           temp=temperature):
    """Set up LLM and embedding models."""
    llm = AzureOpenAI(
        deployment_name=chat_model_name,
        api_key=api_key,
        azure_endpoint=api_base,
        api_version="2023-05-15",
        temperature=temp,
    )

    embedding = AzureOpenAIEmbedding(
        deployment_name=embed_model_name,
        azure_endpoint=api_base,
        api_key=api_key,
        api_version="2023-05-15",
    )

    Settings.llm = llm
    Settings.embed_model = embedding

@mcp.tool()
async def query_visual_studio_license(prompt: str, language: str = "English") -> str:
    """Query information from Visual Studio 2022 License Whitepaper.
    
    Args:
        prompt: The question to ask about Visual Studio licensing
        language: Response language (English or Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("visualstudio2022licensewhitepaper")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying Visual Studio license information: {str(e)}"

@mcp.tool()
async def query_sql_server_license(prompt: str, language: str = "English") -> str:
    """Query information from SQL Server 2022 License Guide.
    
    Args:
        prompt: The question to ask about SQL Server licensing
        language: Response language (English or Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("sqlserver2022licenseguide")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying SQL Server license information: {str(e)}"

@mcp.tool()
async def query_windows_server_license(prompt: str, language: str = "English") -> str:
    """Query information from Windows Server 2022 License Guide.
    
    Args:
        prompt: The question to ask about Windows Server licensing
        language: Response language (English or Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("windowsserver2022licenseguide")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying Windows Server license information: {str(e)}"

@mcp.tool()
async def query_m365_license(prompt: str, language: str = "English") -> str:
    """Query information from Microsoft 365 Enterprise License Guide.
    
    Args:
        prompt: The question to ask about Microsoft 365 licensing
        language: Response language (English or Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("microsoft365licenseguide")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying Microsoft 365 license information: {str(e)}"

@mcp.tool()
async def query_dynamics365_license(prompt: str, language: str = "English") -> str:
    """Query information from Dynamics 365 License Guide.
    
    Args:
        prompt: The question to ask about Dynamics 365 licensing
        language: Response language (English or Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("dynamics365Licenswhitepaper")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying Dynamics 365 license information: {str(e)}"

@mcp.tool()
async def query_gdpr(prompt: str, language: str = "English") -> str:
    """Query information from General Data Protection Regulation (GDPR).
    
    Args:
        prompt: The question to ask about GDPR
        language: Response language (English or Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("generaldataprotectionregulation")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying GDPR information: {str(e)}"

@mcp.tool()
async def query_china_pipl(prompt: str, language: str = "Chinese") -> str:
    """Query information from China Personal Information Protection Law.
    
    Args:
        prompt: The question to ask about China's PIPL
        language: Response language (English or Chinese, default Chinese)
    """
    try:
        setup_llm_and_embeddings()
        index = load_index("chinapersonalinformationprotectionlaw")
        query_engine = index.as_query_engine()
        response = query_engine.query(
            f"You must answer the question in {language} follow by the provided context. ### question: {prompt}"
        )
        return response.response
    except Exception as e:
        return f"Error querying China PIPL information: {str(e)}"
###########################
#####llamaindex mcp tools
###########################

###########################
#####legal mcp tools
###########################
@mcp.tool()
async def get_article_by_code(article_code: int, sub_article_code: int = None) -> str:
    """Get information by article code from Chinese Criminal Law.

    Args:
        article_code: The main article code (e.g., 219)
        sub_article_code: The sub-article code (e.g., 1)
    """
    try:
        if sub_article_code:
            result = law.getInfoByArticleCode(article_code, sub_article_code)
        else:
            result = law.getInfoByArticleCode(article_code)
        return result if result else "No article found with the specified code."
    except Exception as e:
        return f"Error retrieving article information: {str(e)}"

@mcp.tool()
async def search_by_content(content: str, vague: bool = True) -> str:
    """Search for legal articles by content in Chinese Criminal Law.
    
    Args:
        content: The content to search for (e.g., '交通肇事')
        vague: Whether to use fuzzy search (default: True)
    """
    try:
        results = law.getInfoByContent(content, vague)
        if not results or len(results) == 0:
            return "No articles found matching the content."
        
        if isinstance(results, list):
            return "\n\n---\n\n".join(results)
        return results
    except Exception as e:
        return f"Error searching for content: {str(e)}"

@mcp.tool()
async def get_by_article_name(article_name: str) -> str:
    """Get legal information by article name/cause of action.
    
    Args:
        article_name: The name of the article or cause of action (e.g., '交通肇事罪')
    """
    try:
        result = law.getInfoByArticleName(article_name)
        return result if result else "No information found for the specified article name."
    except Exception as e:
        return f"Error retrieving information by article name: {str(e)}"

@mcp.tool()
async def get_specific_article(article_code: int, paragraph_code: int) -> str:
    """Get a specific paragraph from an article in Chinese Criminal Law.
    
    Args:
        article_code: The article code (e.g., 73)
        paragraph_code: The paragraph code (e.g., 3)
    """
    try:
        result = law.getInfoByArticleCode(article_code, paragraph_code)
        return result if result else "No specific paragraph found for the given article and paragraph code."
    except Exception as e:
        return f"Error retrieving specific article paragraph: {str(e)}"

@mcp.tool()
async def get_all_law_contents() -> str:
    """Get all contents of the Chinese Criminal Law.
    
    Returns a list of all legal provisions.
    """
    try:
        results = law.getContentsAll()
        if not results or len(results) == 0:
            return "Failed to retrieve Criminal Law contents."
        
        # Return first few and last few with a message about total count
        count = len(results)
        preview = results[:3] + ["..."] + results[-3:] if count > 6 else results
        preview_text = "\n\n---\n\n".join(preview)
        return f"Retrieved {count} legal provisions. Here's a preview:\n\n{preview_text}"
    except Exception as e:
        return f"Error retrieving all law contents: {str(e)}"
###########################
#####legal mcp tools
###########################

###########################
#####http mcp tools
###########################

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
AZURE_PRICE_API_BASE = "https://prices.azure.com/api/retail/prices"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

# fetch Azure Price API by using odata query
@mcp.tool()
async def get_azure_price(filter_expression: str) -> str:
    """Get Azure price for a service using OData filter expressions.

    Args:
        filter_expression: OData filter expression. Example: contains(armSkuName, 'Standard_D2_v3') and contains(armRegionName, 'eastus')
    """
    # URL encode the filter expression
    encoded_filter = quote(filter_expression)
    api_version = "2023-01-01-preview"
    price_url = f"{AZURE_PRICE_API_BASE}?api-version={api_version}&$filter={encoded_filter}"
    
    all_items = []
    next_page_url = price_url
    page_count = 0
    max_pages = 3  # Limit to 3 pages to avoid timeouts
    
    while next_page_url and page_count < max_pages:
        page_count += 1
        data = await make_azure_price_request(next_page_url)
        
        if not data:
            break
        
        # Add items from this page
        if "Items" in data:
            all_items.extend(data["Items"])
        
        # Get next page URL if available
        next_page_url = data.get("NextPageLink", "")
    
    if not all_items:
        return "Unable to fetch Azure price data for this filter expression or no results found."
    
    # Format the price data into a readable string
    prices = []
    for item in all_items:
        price_info = []
        # Extract key information
        if "productName" in item:
            price_info.append(f"Product: {item['productName']}")
        if "skuName" in item:
            price_info.append(f"SKU: {item['skuName']}")
        if "retailPrice" in item:
            price_info.append(f"Price: {item['retailPrice']} USD")
        if "unitOfMeasure" in item:
            price_info.append(f"Per: {item['unitOfMeasure']}")
        if "armRegionName" in item:
            price_info.append(f"Region: {item['armRegionName']}")
            
        prices.append("\n".join(price_info))

    summary = f"Found {len(all_items)} pricing items (showing all)"
    if page_count >= max_pages and next_page_url:
        summary = f"Found {len(all_items)} pricing items (limited to {max_pages} pages)"
        
    return f"{summary}\n\n" + "\n\n---\n\n".join(prices)

async def make_azure_price_request(url: str) -> dict[str, Any] | None:
    """Make a request to the Azure Price API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }   
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            print(f"Timeout while fetching Azure price data from {url}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code} while fetching Azure price data: {e.response.text}")
            return None
        except Exception as e:
            print(f"Error fetching Azure price data: {str(e)}")
            return None

@mcp.tool()
async def count_chinese_characters(text: str) -> str:
    """Count the number of Chinese characters in a string. Use when the user asks about the word count.
    
    Args:
        text: The input text string containing Chinese characters
    """
    url = "https://haxufunctions.azurewebsites.net/api/http_trigger"
    params = {'text': text}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            return f"Chinese character count: {response.text}"
        except Exception as e:
            return f"Error counting Chinese characters: {str(e)}"
###########################
#####http mcp tools
###########################      

## run the server
if __name__ == "__main__":
    mcp_server = mcp._mcp_server  # noqa: WPS437

    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)
