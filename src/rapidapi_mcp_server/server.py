"""Main MCP server implementation for RapidAPI marketplace discovery."""

import asyncio
import logging
import os
import random
import sys
from typing import Any

from mcp.server import Server

# Configure logging for MCP servers - all logs must go to stderr
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    stream=sys.stderr  # Critical: MCP servers must log to stderr, not stdout
)

from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    TextContent,
    Tool,
)

from .chrome_client import ChromeClient
from .enhanced_chrome_client import EnhancedChromeClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("rapidapi-mcp-server")

# Global Chrome client instance - use enhanced version
chrome_client: EnhancedChromeClient | None = None


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="rapidapi://info",
            name="RapidAPI Server Info",
            description="Information about the RapidAPI MCP server capabilities",
            mimeType="text/plain",
        )
    ]


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource read requests."""
    if uri == "rapidapi://info":
        return """RapidAPI MCP Server

This server provides tools for discovering and assessing APIs from the RapidAPI marketplace.

Available tools:
- search_apis: Search for APIs by keyword
- assess_api: Get comprehensive assessment of a specific API
- get_api_documentation: Extract documentation URLs and endpoints
- compare_apis: Compare multiple APIs side by side
- get_pricing_plans: Extract detailed pricing plans
- get_enhanced_api_documentation: Get enhanced documentation with GraphQL support

The server uses undetected-chromedriver for reliable web scraping with anti-detection capabilities.
"""
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_apis",
            description="Search for APIs in the RapidAPI marketplace by keyword and optional category",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for APIs (e.g., 'weather', 'crypto', 'news')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter"
                    },
                    "maxResults": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 20,
                        "description": "Maximum number of results to return (1-50, default: 20)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="assess_api",
            description="Get comprehensive assessment of a specific API including ratings, pricing, endpoints, and documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "apiUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "The RapidAPI URL for the specific API (e.g., https://rapidapi.com/weatherapi/api/weatherapi-com)"
                    }
                },
                "required": ["apiUrl"]
            }
        ),
        Tool(
            name="get_api_documentation",
            description="Extract documentation URLs and endpoint information for a specific API",
            inputSchema={
                "type": "object",
                "properties": {
                    "apiUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "The RapidAPI URL for the specific API"
                    }
                },
                "required": ["apiUrl"]
            }
        ),
        Tool(
            name="compare_apis",
            description="Compare multiple APIs side by side with key metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "apiUrls": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "format": "uri"
                        },
                        "minItems": 2,
                        "maxItems": 5,
                        "description": "Array of RapidAPI URLs to compare (2-5 APIs)"
                    }
                },
                "required": ["apiUrls"]
            }
        ),
        Tool(
            name="get_pricing_plans",
            description="Extract detailed pricing plans and tier limits for a specific API",
            inputSchema={
                "type": "object",
                "properties": {
                    "apiUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "The RapidAPI URL for the specific API"
                    }
                },
                "required": ["apiUrl"]
            }
        ),
        Tool(
            name="get_enhanced_api_documentation",
            description="Extract comprehensive API documentation with GraphQL-enhanced endpoint details",
            inputSchema={
                "type": "object",
                "properties": {
                    "apiUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "The RapidAPI URL for the specific API"
                    }
                },
                "required": ["apiUrl"]
            }
        ),
        Tool(
            name="start_network_monitoring",
            description="Start monitoring network traffic using Chrome DevTools Protocol",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="stop_network_monitoring", 
            description="Stop monitoring network traffic",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_network_requests",
            description="Get captured network requests, optionally filtered by URL pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "url_filter": {"type": "string", "description": "URL pattern to filter requests"}
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_network_responses",
            description="Get captured network responses, optionally filtered by URL pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "url_filter": {"type": "string", "description": "URL pattern to filter responses"}
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_response_body",
            description="Get response body for a specific request ID",
            inputSchema={
                "type": "object", 
                "properties": {
                    "request_id": {"type": "string", "description": "Request ID to get response body for"}
                },
                "required": ["request_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_network_summary",
            description="Get summary of captured network activity",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="clear_network_data",
            description="Clear all captured network data",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="extract_endpoint_parameters",
            description="Extract detailed endpoint parameters by navigating to playground URL and parsing parameter schemas",
            inputSchema={
                "type": "object",
                "properties": {
                    "playgroundUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "The RapidAPI playground URL for the specific endpoint (e.g., https://rapidapi.com/weatherapi/api/weatherapi-com/endpoint/123/playground)"
                    }
                },
                "required": ["playgroundUrl"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool execution requests."""
    global chrome_client
    
    try:
        # Initialize enhanced Chrome client if needed
        if not chrome_client:
            chrome_client = EnhancedChromeClient()
        
        if name == "search_apis":
            query = arguments["query"]
            category = arguments.get("category")
            max_results = arguments.get("maxResults", 20)
            
            result = await chrome_client.search_apis(query, max_results)
            
            return [
                TextContent(
                    type="text",
                    text=str(result)
                )
            ]
        
        elif name == "assess_api":
            api_url = arguments["apiUrl"]
            
            # Use enhanced assessment - client is now EnhancedChromeClient
            result = await chrome_client.assess_api_enhanced(api_url)
            
            return [
                TextContent(
                    type="text",
                    text=str(result)
                )
            ]
        
        elif name == "get_api_documentation":
            api_url = arguments["apiUrl"]
            
            # Get enhanced assessment which includes comprehensive endpoints
            if hasattr(chrome_client, 'assess_api_enhanced'):
                result = await chrome_client.assess_api_enhanced(api_url)
            else:
                result = await chrome_client.assess_api(api_url)
                
            doc_info = {
                'documentationUrl': result.get('documentationUrl'),
                'endpoints': result.get('endpoints', [])
            }
            
            return [
                TextContent(
                    type="text",
                    text=str(doc_info)
                )
            ]
        
        elif name == "compare_apis":
            api_urls = arguments["apiUrls"]
            
            comparisons = []
            for i, url in enumerate(api_urls):
                try:
                    logger.info(f"Assessing API {i + 1}/{len(api_urls)}: {url}")
                    assessment = await chrome_client.assess_api(url)
                    
                    comparisons.append({
                        'url': url,
                        'name': assessment.get('name', ''),
                        'provider': assessment.get('provider', ''),
                        'rating': assessment.get('rating'),
                        'pricing': assessment.get('pricing', {}),
                        'endpointCount': len(assessment.get('endpoints', [])),
                        'popularity': assessment.get('popularity'),
                        'serviceLevel': assessment.get('serviceLevel')
                    })
                    
                    # Add ethical delay between requests
                    if i < len(api_urls) - 1:
                        await asyncio.sleep(2.0 + (random.uniform(0, 1)))
                        
                except Exception as error:
                    logger.error(f"Failed to assess {url}: {error}")
                    comparisons.append({
                        'url': url,
                        'error': str(error)
                    })
            
            result = {
                'comparison': comparisons,
                'comparedAt': asyncio.get_event_loop().time()
            }
            
            return [
                TextContent(
                    type="text",
                    text=str(result)
                )
            ]
        
        elif name == "get_pricing_plans":
            api_url = arguments["apiUrl"]
            
            # Get assessment which includes pricing
            result = await chrome_client.assess_api(api_url)
            pricing_data = result.get('pricing', {})
            
            return [
                TextContent(
                    type="text",
                    text=str(pricing_data)
                )
            ]
        
        elif name == "get_enhanced_api_documentation":
            api_url = arguments["apiUrl"]
            
            # Use enhanced assessment for comprehensive documentation
            if hasattr(chrome_client, 'assess_api_enhanced'):
                result = await chrome_client.assess_api_enhanced(api_url)
            else:
                result = await chrome_client.assess_api(api_url)
            
            return [
                TextContent(
                    type="text",
                    text=str(result)
                )
            ]
        
        elif name == "start_network_monitoring":
            success = await chrome_client.start_network_monitoring()
            return [
                TextContent(
                    type="text",
                    text=str({"success": success, "monitoring_active": chrome_client.network_monitoring})
                )
            ]
        
        elif name == "stop_network_monitoring":
            success = await chrome_client.stop_network_monitoring()
            return [
                TextContent(
                    type="text",
                    text=str({"success": success, "monitoring_active": chrome_client.network_monitoring})
                )
            ]
        
        elif name == "get_network_requests":
            url_filter = arguments.get("url_filter")
            requests = chrome_client.get_network_requests(url_filter)
            return [
                TextContent(
                    type="text",
                    text=str({"total": len(requests), "url_filter": url_filter, "requests": requests})
                )
            ]
        
        elif name == "get_network_responses":
            url_filter = arguments.get("url_filter")
            responses = chrome_client.get_network_responses(url_filter)
            return [
                TextContent(
                    type="text",
                    text=str({"total": len(responses), "url_filter": url_filter, "responses": responses})
                )
            ]
        
        elif name == "get_response_body":
            request_id = arguments["request_id"]
            body = await chrome_client.get_response_body(request_id)
            return [
                TextContent(
                    type="text",
                    text=str({"request_id": request_id, "body": body})
                )
            ]
        
        elif name == "get_network_summary":
            requests = chrome_client.get_network_requests()
            responses = chrome_client.get_network_responses()
            
            # Group by domain
            domains = {}
            for req in requests:
                url = req.get('url', '')
                if url:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    domains[domain] = domains.get(domain, 0) + 1
            
            summary = {
                "total_requests": len(requests),
                "total_responses": len(responses),
                "monitoring_active": chrome_client.network_monitoring,
                "domains": domains
            }
            
            return [
                TextContent(
                    type="text",
                    text=str(summary)
                )
            ]
        
        elif name == "clear_network_data":
            chrome_client.clear_network_data()
            return [
                TextContent(
                    type="text",
                    text=str({"success": True, "message": "Network data cleared"})
                )
            ]
        
        elif name == "extract_endpoint_parameters":
            playground_url = arguments.get("playgroundUrl", "")
            if not playground_url:
                return [
                    TextContent(
                        type="text",
                        text=str({"error": "playgroundUrl is required"})
                    )
                ]
            
            # Use the enhanced Chrome client for parameter extraction
            result = await chrome_client._extract_endpoint_parameters(playground_url)
            return [
                TextContent(
                    type="text",
                    text=str(result)
                )
            ]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as error:
        logger.error(f"Error in tool {name}: {error}")
        return [
            TextContent(
                type="text",
                text=f"Error {name.replace('_', ' ')}: {str(error)}"
            )
        ]


async def main():
    """Run the MCP server."""
    logger.info("Starting RapidAPI MCP server...")
    
    # Clean up Chrome client on shutdown
    async def cleanup():
        global chrome_client
        if chrome_client:
            await chrome_client.close()
    
    try:
        async with stdio_server() as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        await cleanup()
        logger.info("Server shutdown complete")


def cli_main():
    """CLI entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()