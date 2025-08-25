# CLAUDE.md - RapidAPI Discovery MCP Server (Python)

## Project Overview
Python implementation of the RapidAPI Discovery MCP server with enhanced Chrome DevTools Protocol integration for comprehensive API marketplace intelligence.

## Development & Debug Setup

### Virtual Environment Setup
This project uses dual virtual environments for development and testing:

```bash
# Primary development environment
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Build/test environment  
python3 -m venv build-test-venv
source build-test-venv/bin/activate
pip install -e .
```

### Debug Logging - Build and Run with Enhanced Logging

**IMPORTANT**: You can see comprehensive debug logs when you build and run like this:

```bash
# Install in both environments for consistency
source venv/bin/activate && pip install -e . && source build-test-venv/bin/activate && pip install -e .
```

**Debug Testing Command**:
```bash
cd rapidapi-discovery-mcp/rapidapi-mcp-server-py && source venv/bin/activate && python3 -c "
from src.rapidapi_mcp_server.enhanced_chrome_client import EnhancedChromeClient
import asyncio

async def test():
    client = EnhancedChromeClient()
    result = await client.assess_api_enhanced('https://rapidapi.com/SafeDev/api/aso-report')
    print('API Name:', result.get('name'))
    print('API Description:', result.get('description'))
    print('Endpoints found:', len(result.get('endpoints', [])))
    for i, ep in enumerate(result.get('endpoints', [])[:5]):
        print(f'  {i+1}. {ep.get(\"method\")} {ep.get(\"name\")} - {ep.get(\"description\", \"No desc\")}')

asyncio.run(test())
"
```

### Debug Output Examples
When running the debug command, you'll see detailed logging output:

```
🔥 ENHANCED ASSESSMENT STARTED for: https://rapidapi.com/SafeDev/api/aso-report
🔥 DEBUG: Method assess_api_enhanced called successfully
🔄 Navigation successful: https://rapidapi.com/SafeDev/api/aso-report (loaded in 3565ms)
🔄 Scraped description: Unlock powerful insights with our API for Google Play...
🔄 Scraped pricing: {'tiers': [{'monthly_cost': 0, 'name': 'BASIC'...
🔄 Scraped ratings: {'rating': 5, 'reviewCount': 1}
🔥 DEBUG: _scrape_endpoint_sections called - WAIT FOR AUTO-EXPAND VERSION
🔄 Scraped 4 endpoint sections total
🔄 Extracted 4 detailed endpoints
DOM enhanced fields: ['description', 'pricing', 'rating', 'reviewCount', 'endpoints', 'provider']
```

### Key Features
- **Enhanced Chrome Client**: Real DOM extraction after JavaScript rendering
- **Comprehensive API Assessment**: Name, description, pricing, ratings, endpoints
- **Section Auto-Expansion**: Handles dynamic content expansion
- **Debug Logging**: Detailed step-by-step extraction logging
- **Dual Environment Support**: Development and build/test virtual environments

### Architecture
- `server.py`: Main MCP server implementation
- `enhanced_chrome_client.py`: Enhanced DOM extraction with CDP integration
- `chrome_client.py`: Base Chrome client for standard operations

### Recent Fixes
- ✅ **API Description Extraction**: Fixed missing description field
- ✅ **Enhanced Selectors**: Updated to handle current RapidAPI page structure
- ⚠️ **Endpoint Count**: Working on capturing all collapsed sections (currently 4/15+ endpoints)

### Testing
Use the debug command above to test API assessment functionality and see detailed logging output for troubleshooting.