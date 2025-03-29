import uvicorn
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
from legal_documents_cn import criminal_law_cn as law
from dotenv import load_dotenv
from supabase import create_client
from langchain_openai import AzureOpenAIEmbeddings

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
            # Remove the integer 99 and use only the stream objects
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


###########################
#####vector search tools
###########################    
@mcp.tool()
def gdpr_semantic_search(query_text):
    """
    Perform semantic search against the GDPR. 

    GDPR is a comprehensive data protection and privacy regulation enacted by the European Union that came into effect on May 25, 2018. 
    It represents one of the most significant and stringent privacy laws in the world.
    
    Args:
        query_text (str): The text of search query
        
    Returns:
        list: Raw matching documents with similarity scores, containing up to 3 results
              with similarity above 0.5 threshold
    """
    # Initialize Supabase client
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    
    # Initialize Azure OpenAI embedding model
    embedding_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-ada-002",
        model="text-embedding-ada-002",
        api_version=os.environ["AZURE_OPENAI_API_VERSION"]
    )
    # Generate embedding for the query text using Azure OpenAI
    query_embedding = embedding_model.embed_query(query_text)
    
    # Perform vector similarity search using pgvector
    response = supabase.rpc(
        'match_documents',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.5,
            'match_count': 3
        }
    ).execute()
    
    return response.data


@mcp.tool()
def China_pipl_semantic_search(query_text):
    """
    Perform semantic search against China PIPL.

    China's Personal Information Protection Law (PIPL) is a comprehensive data protection law that regulates the processing of personal information in China.
    PIPL is China's first comprehensive national data privacy law that came into effect on November 1, 2021. 
    It establishes a framework for the protection of personal information in China.
    
    Args:
        query_text (str): The text of search query

        
    Returns:
        list: Raw matching documents with similarity scores, containing up to 3 results
              with similarity above 0.5 threshold
    """
    # Initialize Supabase client
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

    # Initialize Azure OpenAI embedding model
    embedding_model = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-ada-002",
        model="text-embedding-ada-002",
        api_version=os.environ["AZURE_OPENAI_API_VERSION"]
    )

    query_embedding = embedding_model.embed_query(query_text)
    
    # Search for similar content in Supabase
    response = supabase.rpc(
        "match_pipl_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": 3
        }
    ).execute()
    
    return response.data

###########################
#####vector search tools
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
