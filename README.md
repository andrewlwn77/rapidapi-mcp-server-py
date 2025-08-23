# RapidAPI Discovery MCP Server

A Model Context Protocol (MCP) server that provides comprehensive RapidAPI marketplace discovery and analysis capabilities using undetected-chromedriver for reliable web scraping that bypasses anti-bot detection.

## 🌟 Features

- **API Search**: Search for APIs by keyword and category across RapidAPI marketplace
- **API Assessment**: Detailed analysis of specific APIs including ratings, pricing, and endpoints
- **API Documentation**: Extract comprehensive documentation and endpoint details
- **API Comparison**: Side-by-side comparison of multiple APIs with key metrics
- **Pricing Analysis**: Detailed pricing plans and tier limits extraction
- **Enhanced Documentation**: GraphQL-enhanced endpoint details and comprehensive API docs
- **Anti-Detection**: Uses undetected-chromedriver to reliably bypass bot detection systems

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/rapidapi-mcp-server-py.git
cd rapidapi-mcp-server-py

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

Add to your Claude Desktop `.mcp.json`:

```json
{
  "mcpServers": {
    "rapidapi-discovery": {
      "command": "/path/to/rapidapi-mcp-server-py/venv/bin/python",
      "args": ["-m", "rapidapi_mcp_server.server"],
      "cwd": "/path/to/rapidapi-mcp-server-py",
      "env": {
        "CHROME_EXECUTABLE_PATH": "/opt/google/chrome/google-chrome"
      }
    }
  }
}
```

## 🛠️ Available Tools

### 1. Search APIs (`search_apis`)
Search for APIs in the RapidAPI marketplace by keyword and optional category.

**Parameters:**
- `query` (required): Search query for APIs (e.g., 'weather', 'crypto', 'news')
- `maxResults` (optional): Maximum number of results to return (1-50, default: 20)
- `category` (optional): Category filter

**Example:**
```python
mcp__rapidapi-discovery__search_apis(query="weather", maxResults=10)
```

### 2. Assess API (`assess_api`)
Get comprehensive assessment of a specific API including ratings, pricing, endpoints, and documentation.

**Parameters:**
- `apiUrl` (required): The RapidAPI URL for the specific API

**Example:**
```python
mcp__rapidapi-discovery__assess_api(apiUrl="https://rapidapi.com/weatherapi/api/weatherapi-com")
```

### 3. Get API Documentation (`get_api_documentation`)
Extract documentation URLs and endpoint information for a specific API.

**Parameters:**
- `apiUrl` (required): The RapidAPI URL for the specific API

### 4. Compare APIs (`compare_apis`)
Compare multiple APIs side by side with key metrics.

**Parameters:**
- `apiUrls` (required): Array of RapidAPI URLs to compare (2-5 APIs)

### 5. Get Pricing Plans (`get_pricing_plans`)
Extract detailed pricing plans and tier limits for a specific API.

**Parameters:**
- `apiUrl` (required): The RapidAPI URL for the specific API

### 6. Get Enhanced API Documentation (`get_enhanced_api_documentation`)
Extract comprehensive API documentation with GraphQL-enhanced endpoint details.

**Parameters:**
- `apiUrl` (required): The RapidAPI URL for the specific API

## 🏗️ Architecture

### Core Components

- **server.py**: Main MCP server implementation with JSON-RPC over stdio
- **chrome_client.py**: Chrome automation using undetected-chromedriver
- **pyproject.toml**: Project configuration and dependencies

### Key Features

- **Undetected Chrome**: Uses undetected-chromedriver for reliable bot detection bypass
- **Session Management**: Efficient Chrome session handling with automatic cleanup
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Async Support**: Full async/await support for concurrent operations
- **MCP Protocol**: Compatible with MCP v1.0.0+ protocol

## 🧪 Testing

Run the server in development mode:

```bash
# Activate virtual environment
source venv/bin/activate

# Run server directly
python -m rapidapi_mcp_server.server

# Test with simple MCP client
python -c "
import asyncio
import json
from rapidapi_mcp_server.server import serve

async def test():
    # Server will run on stdio
    pass

asyncio.run(test())
"
```

## 📊 Sample Output

### Search Results
```json
{
  "query": "weather",
  "resultsCount": 5,
  "apis": [
    {
      "name": "WeatherAPI",
      "description": "Real-time weather data and forecasts",
      "provider": "WeatherAPI.com",
      "url": "https://rapidapi.com/weatherapi/api/weatherapi-com",
      "rating": 4.8,
      "popularity": "High"
    }
  ]
}
```

### API Assessment
```json
{
  "name": "WeatherAPI.com",
  "rating": 4.8,
  "reviewCount": 15420,
  "popularity": "Very High",
  "pricing": {
    "free": {
      "requests": 1000000,
      "rateLimit": "1 req/sec"
    }
  },
  "endpoints": [
    {
      "name": "Current Weather",
      "method": "GET",
      "description": "Get real-time weather data"
    }
  ]
}
```

## 🔧 Environment Variables

- `CHROME_EXECUTABLE_PATH`: Path to Chrome executable (default: auto-detect)
- `CHROME_HEADLESS`: Run Chrome in headless mode (default: true)
- `CHROME_TIMEOUT`: Chrome operation timeout in seconds (default: 30)

## 🚨 Troubleshooting

### Common Issues

1. **Chrome not found**
   ```bash
   export CHROME_EXECUTABLE_PATH="/path/to/chrome"
   ```

2. **Session errors**
   - Ensure Chrome is properly installed
   - Check if Chrome process is already running
   - Restart the MCP server

3. **Import errors**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -e .
   ```

## 📁 Project Structure

```
rapidapi-mcp-server-py/
├── src/
│   └── rapidapi_mcp_server/
│       ├── __init__.py
│       ├── server.py          # Main MCP server
│       └── chrome_client.py   # Chrome automation
├── pyproject.toml            # Project configuration
├── README.md                 # This file
└── .gitignore               # Git ignore rules
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **undetected-chromedriver**: For reliable anti-detection capabilities
- **MCP Protocol**: For standardized AI tool integration
- **Selenium WebDriver**: For browser automation foundations
- **RapidAPI**: For providing the comprehensive API marketplace

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/your-username/rapidapi-mcp-server-py/issues)
- **Documentation**: This README and inline code documentation
- **Examples**: See the tool examples above for usage patterns

---

**Note**: This server requires a valid internet connection and Chrome browser installation. The server uses web scraping techniques that comply with RapidAPI's terms of service for automated access.