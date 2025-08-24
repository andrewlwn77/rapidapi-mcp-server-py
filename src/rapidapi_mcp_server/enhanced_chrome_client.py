"""Enhanced Chrome client with network monitoring from undetected-chrome-mcp."""

import asyncio
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional
from .chrome_client import ChromeClient

logger = logging.getLogger(__name__)


class EnhancedChromeClient(ChromeClient):
    """Chrome client enhanced with network monitoring for capturing GraphQL responses."""
    
    def __init__(self):
        super().__init__()
        # Network monitoring state (copied from undetected-chrome-mcp)
        self.network_monitoring = False
        self.network_requests: List[Dict[str, Any]] = []
        self.network_responses: List[Dict[str, Any]] = []
        self.network_lock = threading.Lock()
        self.max_network_entries = 1000
        
        logger.info("Enhanced Chrome client initialized with network monitoring")
    
    def _network_request_handler(self, message):
        """Handle Network.requestWillBeSent events."""
        try:
            with self.network_lock:
                if len(self.network_requests) >= self.max_network_entries:
                    self.network_requests.pop(0)  # Remove oldest
                
                # Handle different message structures
                if isinstance(message, dict) and 'params' in message:
                    # Standard CDP format
                    params = message['params']
                    request_data = {
                        'requestId': params.get('requestId'),
                        'url': params.get('request', {}).get('url'),
                        'method': params.get('request', {}).get('method'),
                        'headers': params.get('request', {}).get('headers', {}),
                        'timestamp': params.get('timestamp'),
                        'type': params.get('type'),
                        'postData': params.get('request', {}).get('postData')
                    }
                else:
                    # Direct format (undetected-chromedriver specific)
                    request_data = {
                        'requestId': message.get('requestId'),
                        'url': message.get('request', {}).get('url') if message.get('request') else message.get('url'),
                        'method': message.get('request', {}).get('method') if message.get('request') else message.get('method'),
                        'headers': message.get('request', {}).get('headers', {}) if message.get('request') else message.get('headers', {}),
                        'timestamp': message.get('timestamp'),
                        'type': message.get('type'),
                        'postData': message.get('request', {}).get('postData') if message.get('request') else message.get('postData')
                    }
                
                self.network_requests.append(request_data)
                logger.debug(f"Network request captured: {request_data.get('method')} {request_data.get('url')}")
        except Exception as e:
            logger.warning(f"Error handling network request: {e}")
    
    def _network_response_handler(self, message):
        """Handle Network.responseReceived events."""
        try:
            with self.network_lock:
                if len(self.network_responses) >= self.max_network_entries:
                    self.network_responses.pop(0)  # Remove oldest
                
                # Handle different message structures
                if isinstance(message, dict) and 'params' in message:
                    # Standard CDP format
                    params = message['params']
                    response_data = {
                        'requestId': params.get('requestId'),
                        'url': params.get('response', {}).get('url'),
                        'status': params.get('response', {}).get('status'),
                        'statusText': params.get('response', {}).get('statusText'),
                        'headers': params.get('response', {}).get('headers', {}),
                        'mimeType': params.get('response', {}).get('mimeType'),
                        'timestamp': params.get('timestamp'),
                        'type': params.get('type')
                    }
                else:
                    # Direct format (undetected-chromedriver specific)
                    response_data = {
                        'requestId': message.get('requestId'),
                        'url': message.get('response', {}).get('url') if message.get('response') else message.get('url'),
                        'status': message.get('response', {}).get('status') if message.get('response') else message.get('status'),
                        'statusText': message.get('response', {}).get('statusText') if message.get('response') else message.get('statusText'),
                        'headers': message.get('response', {}).get('headers', {}) if message.get('response') else message.get('headers', {}),
                        'mimeType': message.get('response', {}).get('mimeType') if message.get('response') else message.get('mimeType'),
                        'timestamp': message.get('timestamp'),
                        'type': message.get('type')
                    }
                
                self.network_responses.append(response_data)
                logger.debug(f"Network response captured: {response_data.get('status')} {response_data.get('url')}")
        except Exception as e:
            logger.warning(f"Error handling network response: {e}")
    
    async def start_network_monitoring(self) -> bool:
        """Start monitoring network traffic using Chrome DevTools Protocol."""
        if self.network_monitoring:
            return True
        
        try:
            driver = self._get_chrome_driver()
            
            # Enable Network domain
            await asyncio.get_event_loop().run_in_executor(
                None, driver.execute_cdp_cmd, 'Network.enable', {}
            )
            
            # Add event listeners
            await asyncio.get_event_loop().run_in_executor(
                None, driver.add_cdp_listener, 'Network.requestWillBeSent', self._network_request_handler
            )
            await asyncio.get_event_loop().run_in_executor(
                None, driver.add_cdp_listener, 'Network.responseReceived', self._network_response_handler
            )
            
            self.network_monitoring = True
            logger.info("Network monitoring started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start network monitoring: {e}")
            return False
    
    async def stop_network_monitoring(self) -> bool:
        """Stop monitoring network traffic."""
        if not self.network_monitoring:
            return True
        
        try:
            if self.driver:
                # Disable Network domain
                await asyncio.get_event_loop().run_in_executor(
                    None, self.driver.execute_cdp_cmd, 'Network.disable', {}
                )
            
            self.network_monitoring = False
            logger.info("Network monitoring stopped")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop network monitoring: {e}")
            return False
    
    def get_network_responses(self, url_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get captured network responses, optionally filtered by URL pattern."""
        with self.network_lock:
            if url_filter:
                return [resp for resp in self.network_responses if url_filter.lower() in resp.get('url', '').lower()]
            return self.network_responses.copy()
    
    async def get_response_body(self, request_id: str) -> Optional[str]:
        """Get response body for a specific request ID."""
        if not self.network_monitoring:
            logger.warning("Network monitoring is not enabled")
            return None
        
        try:
            if self.driver:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.driver.execute_cdp_cmd, 'Network.getResponseBody', {'requestId': request_id}
                )
                return result.get('body')
        except Exception as e:
            logger.warning(f"Failed to get response body for request {request_id}: {e}")
            return None
    
    def clear_network_data(self):
        """Clear all captured network data."""
        with self.network_lock:
            self.network_requests.clear()
            self.network_responses.clear()
        logger.info("Network data cleared")
    
    async def assess_api_enhanced(self, api_url: str) -> Dict[str, Any]:
        """Enhanced API assessment using real network monitoring."""
        logger.info(f"🔥 ENHANCED ASSESSMENT CALLED for: {api_url}")
        print(f"🔥 ENHANCED ASSESSMENT CALLED for: {api_url}")
        
        try:
            # Clear previous network data
            self.clear_network_data()
            
            # Start network monitoring
            if not await self.start_network_monitoring():
                logger.warning("Could not start network monitoring, falling back to static")
                return await self.assess_api(api_url)
            
            # Navigate to API page with network monitoring active
            logger.info(f"Navigating to {api_url} with network monitoring")
            
            # Use existing navigation but with monitoring active
            driver = self._get_chrome_driver()
            driver.get(api_url)
            
            # Wait and trigger interactions to load GraphQL data
            await asyncio.sleep(3)
            
            # Execute JavaScript to trigger GraphQL calls
            interaction_script = """
            // Scroll and interact to trigger API calls for pricing, documentation, etc.
            window.scrollTo(0, 1000);
            
            setTimeout(() => {
                // Click on tabs that might trigger data loading
                const tabs = document.querySelectorAll('button[role="tab"], [data-tab], .tab, a[href*="pricing"], a[href*="doc"]');
                tabs.forEach((tab, index) => {
                    if (index < 5) { // Click first 5 relevant tabs/links
                        setTimeout(() => {
                            try {
                                tab.click();
                                console.log('Clicked:', tab.textContent || tab.href);
                            } catch (e) {
                                console.log('Could not click:', e);
                            }
                        }, index * 800);
                    }
                });
                
                // Scroll to bottom to trigger lazy loading
                setTimeout(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 3000);
            }, 1000);
            
            return true;
            """
            
            driver.execute_script(interaction_script)
            
            # Wait for GraphQL calls to complete
            await asyncio.sleep(5)
            
            # Get standard assessment
            result = await self.assess_api(api_url)
            
            # Get RapidAPI RSC responses (Next.js Server Components) and GraphQL responses
            api_responses = self.get_network_responses(url_filter="/api/")
            graphql_responses = self.get_network_responses(url_filter="graphql")
            
            enhanced_data = {}
            
            # Extract data from RSC payloads (primary source)
            if api_responses:
                logger.info(f"Found {len(api_responses)} API responses")
                rsc_data = await self._extract_rsc_data(api_responses)
                if rsc_data:
                    enhanced_data.update(rsc_data)
                    logger.info(f"Enhanced with RSC data: {list(rsc_data.keys())}")
            
            # Extract data from GraphQL responses (secondary source)
            if graphql_responses:
                logger.info(f"Found {len(graphql_responses)} GraphQL responses")
                graphql_data = await self._extract_graphql_data(graphql_responses)
                if graphql_data:
                    enhanced_data.update(graphql_data)
                    logger.info(f"Enhanced with GraphQL data: {list(graphql_data.keys())}")
            
            # Merge enhanced data
            if enhanced_data:
                for key, value in enhanced_data.items():
                    if value and value != result.get(key):
                        result[key] = value
                        
                logger.info(f"Total enhanced fields: {list(enhanced_data.keys())}")
            else:
                logger.info("No enhanced data captured")
            
            # Stop network monitoring
            await self.stop_network_monitoring()
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced assessment failed: {e}")
            # Ensure monitoring is stopped
            await self.stop_network_monitoring()
            # Fallback to standard assessment
            return await self.assess_api(api_url)
    
    async def _extract_rsc_data(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract API data from Next.js RSC (React Server Components) responses."""
        enhanced_data = {}
        import re
        
        try:
            for response in responses:
                request_id = response.get('requestId')
                url = response.get('url', '')
                
                if request_id and ('/api/' in url):
                    # Get actual response body
                    body = await self.get_response_body(request_id)
                    
                    if body:
                        try:
                            # Parse RSC payload for API metadata
                            # RSC responses contain data in format: "description","content":"We provide free API..."
                            
                            # Extract description from RSC meta content
                            desc_pattern = r'"description","content":"([^"]*)"'
                            desc_match = re.search(desc_pattern, body)
                            if desc_match:
                                enhanced_data['description'] = desc_match.group(1)
                                logger.debug(f"Extracted description from RSC: {desc_match.group(1)[:100]}...")
                            
                            # Extract provider from URL structure - rapidapi.com/PROVIDER/api/API-NAME
                            if 'rapidapi.com' in url:
                                provider_match = re.search(r'rapidapi\.com/([^/]+)/', url)
                                if provider_match:
                                    enhanced_data['provider'] = provider_match.group(1)
                            
                            # Look for pricing data in RSC payload
                            if 'pricing' in url.lower():
                                # Try to parse pricing information from RSC structure
                                pricing_pattern = r'"plans":\s*(\[.*?\])'
                                pricing_match = re.search(pricing_pattern, body, re.DOTALL)
                                if pricing_match:
                                    try:
                                        import json
                                        plans_data = json.loads(pricing_match.group(1))
                                        enhanced_data['pricing'] = {'tiers': plans_data}
                                    except json.JSONDecodeError:
                                        pass
                            
                            # Look for endpoint data in RSC payload
                            if 'endpoint' in url.lower() or 'playground' in url.lower():
                                # Extract endpoint information from RSC structure
                                endpoint_pattern = r'"endpoints":\s*(\[.*?\])'
                                endpoint_match = re.search(endpoint_pattern, body, re.DOTALL)
                                if endpoint_match:
                                    try:
                                        import json
                                        endpoints_data = json.loads(endpoint_match.group(1))
                                        enhanced_data['endpoints'] = endpoints_data
                                    except json.JSONDecodeError:
                                        pass
                                        
                        except Exception as e:
                            logger.warning(f"Could not parse RSC data from response {request_id}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error extracting RSC data: {e}")
        
        return enhanced_data

    async def _extract_graphql_data(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract API data from real GraphQL responses."""
        enhanced_data = {}
        
        try:
            for response in responses:
                request_id = response.get('requestId')
                if request_id:
                    # Get actual response body
                    body = await self.get_response_body(request_id)
                    
                    if body:
                        try:
                            # Parse actual JSON response
                            response_data = json.loads(body)
                            
                            # Extract real API information from GraphQL structure
                            if 'data' in response_data:
                                data = response_data['data']
                                
                                # Look for API information in various GraphQL response structures
                                api_info = None
                                if 'api' in data:
                                    api_info = data['api']
                                elif 'getApi' in data:
                                    api_info = data['getApi']
                                elif 'apiDetails' in data:
                                    api_info = data['apiDetails']
                                elif 'marketplace' in data and 'api' in data['marketplace']:
                                    api_info = data['marketplace']['api']
                                
                                if api_info:
                                    # Extract real fields from GraphQL response
                                    if api_info.get('name'):
                                        enhanced_data['name'] = api_info['name']
                                    if api_info.get('description'):
                                        enhanced_data['description'] = api_info['description']
                                    if api_info.get('provider') or api_info.get('providerName'):
                                        enhanced_data['provider'] = api_info.get('provider') or api_info.get('providerName')
                                    if api_info.get('rating') is not None:
                                        enhanced_data['rating'] = float(api_info['rating'])
                                    if api_info.get('reviewCount') is not None:
                                        enhanced_data['reviewCount'] = int(api_info['reviewCount'])
                                    if api_info.get('popularity'):
                                        enhanced_data['popularity'] = api_info['popularity']
                                    if api_info.get('serviceLevel'):
                                        enhanced_data['serviceLevel'] = api_info['serviceLevel']
                                    if api_info.get('documentationUrl'):
                                        enhanced_data['documentationUrl'] = api_info['documentationUrl']
                                    
                                    # Extract pricing information
                                    if 'pricing' in api_info and api_info['pricing']:
                                        enhanced_data['pricing'] = api_info['pricing']
                                    elif 'pricingTiers' in api_info:
                                        enhanced_data['pricing'] = {'tiers': api_info['pricingTiers']}
                                    elif 'plans' in api_info:
                                        enhanced_data['pricing'] = {'tiers': api_info['plans']}
                                    
                                    # Extract endpoints with parameters
                                    if 'endpoints' in api_info and api_info['endpoints']:
                                        enhanced_data['endpoints'] = api_info['endpoints']
                                    elif 'methods' in api_info:
                                        enhanced_data['endpoints'] = api_info['methods']
                                    elif 'operations' in api_info:
                                        enhanced_data['endpoints'] = api_info['operations']
                                    
                                    logger.info(f"Extracted real GraphQL data: {list(enhanced_data.keys())}")
                                    break
                                    
                        except json.JSONDecodeError as e:
                            logger.warning(f"Could not parse JSON from response {request_id}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error extracting GraphQL data: {e}")
        
        return enhanced_data
    
    async def close(self):
        """Close the Chrome driver and cleanup."""
        # Stop network monitoring if active
        if self.network_monitoring:
            await self.stop_network_monitoring()
            
        # Call parent close
        await super().close()