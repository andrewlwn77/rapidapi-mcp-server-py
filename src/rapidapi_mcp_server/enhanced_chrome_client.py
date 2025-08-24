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
            # Debug: Log to stderr only for MCP compatibility
            logger.error(f"CDP Network Request Event: {message}")
            
            with self.network_lock:
                if len(self.network_requests) >= self.max_network_entries:
                    self.network_requests.pop(0)  # Remove oldest
                
                # Handle different message structures (exact copy from working undetected-chrome-mcp)
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
                logger.error(f"✅ Network request captured: {request_data.get('method')} {request_data.get('url')}")
        except Exception as e:
            logger.error(f"Error handling network request: {e}")
    
    def _network_response_handler(self, message):
        """Handle Network.responseReceived events."""
        try:
            # Debug: Log to stderr only for MCP compatibility
            logger.error(f"CDP Network Response Event: {message}")
            
            with self.network_lock:
                if len(self.network_responses) >= self.max_network_entries:
                    self.network_responses.pop(0)  # Remove oldest
                
                # Handle different message structures (exact copy from working undetected-chrome-mcp)
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
                        'mimeType': params.get('response', {}).get('mimeType') if message.get('response') else message.get('mimeType'),
                        'timestamp': message.get('timestamp'),
                        'type': message.get('type')
                    }
                
                self.network_responses.append(response_data)
                logger.error(f"✅ Network response captured: {response_data.get('status')} {response_data.get('url')}")
        except Exception as e:
            logger.error(f"Error handling network response: {e}")
    
    async def start_network_monitoring(self) -> bool:
        """Start monitoring network traffic using Chrome DevTools Protocol."""
        if self.network_monitoring:
            return True
        
        try:
            driver = self._get_chrome_driver()
            
            # Enable Network domain (direct synchronous call)
            driver.execute_cdp_cmd('Network.enable', {})
            
            # Add event listeners (direct synchronous calls)
            driver.add_cdp_listener('Network.requestWillBeSent', self._network_request_handler)
            driver.add_cdp_listener('Network.responseReceived', self._network_response_handler)
            
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
                # Disable Network domain (direct synchronous call)
                self.driver.execute_cdp_cmd('Network.disable', {})
            
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
    
    def get_network_requests(self, url_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get captured network requests, optionally filtered by URL pattern."""
        with self.network_lock:
            if url_filter:
                return [req for req in self.network_requests if url_filter.lower() in req.get('url', '').lower()]
            return self.network_requests.copy()
    
    async def get_response_body(self, request_id: str) -> Optional[str]:
        """Get response body for a specific request ID."""
        if not self.network_monitoring:
            logger.warning("Network monitoring is not enabled")
            return None
        
        try:
            if self.driver:
                result = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
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
        """Enhanced API assessment with DOM extraction after JavaScript rendering."""
        logger.error(f"🔥 ENHANCED ASSESSMENT STARTED for: {api_url}")
        logger.error(f"🔥 DEBUG: Method assess_api_enhanced called successfully")
        logger.error(f"🔥 DEBUG: Driver state: {self.driver is not None}")
        
        try:
            # Navigate to API page for DOM extraction (no network monitoring needed)
            logger.error(f"Navigating to {api_url} for DOM extraction")
            
            # Use working undetected-chrome-mcp for navigation and DOM extraction
            logger.error("🔄 Using undetected-chrome-mcp for DOM extraction...")
            
            # Get standard assessment first
            result = await self.assess_api(api_url)
            
            # Step-by-step DOM extraction using working undetected-chrome approach
            await self._navigate_to_page(api_url)
            enhanced_data = {}
            
            # Extract each data type step by step
            description = await self._scrape_description()
            if description:
                enhanced_data['description'] = description
                
            pricing = await self._scrape_pricing()
            if pricing:
                enhanced_data['pricing'] = pricing
                
            rating_data = await self._scrape_ratings()
            if rating_data:
                enhanced_data.update(rating_data)
            
            # Extract detailed endpoint sections with expansion
            endpoints = await self._scrape_endpoint_sections()
            if endpoints:
                enhanced_data['endpoints'] = endpoints
                logger.error(f"🔄 Extracted {len(endpoints)} detailed endpoints")
            
            # Extract provider from URL structure (real extraction) as fallback
            if 'provider' not in enhanced_data and 'rapidapi.com/' in api_url and '/api/' in api_url:
                import re
                provider_match = re.search(r'rapidapi\.com/([^/]+)/api/', api_url)
                if provider_match:
                    enhanced_data['provider'] = provider_match.group(1)
            
            # Merge enhanced data with base result
            if enhanced_data:
                for key, value in enhanced_data.items():
                    if value and value != result.get(key):
                        result[key] = value
                logger.error(f"DOM enhanced fields: {list(enhanced_data.keys())}")
            else:
                logger.error("No DOM enhanced data captured")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ DOM ENHANCED ASSESSMENT FAILED: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Stack trace: {traceback.format_exc()}")
            # Fallback to standard assessment
            logger.error("🔄 Falling back to basic assess_api...")
            return await self.assess_api(api_url)
    
    async def _extract_dom_data(self) -> Dict[str, Any]:
        """Extract API data directly from DOM after JavaScript rendering."""
        enhanced_data = {}
        import re
        
        try:
            if not self.driver:
                logger.warning("No Chrome driver available for DOM extraction")
                return enhanced_data
            
            # Wait for JavaScript rendering (match undetected-chrome timing)
            await asyncio.sleep(3)
            
            # Validate key elements are present before extraction
            key_elements_script = """
            // Check for presence of key elements
            const hasOverview = document.querySelector('h1, h2, h3') !== null;
            const hasContent = document.querySelector('[class*="markdown"], .description, p') !== null;
            const hasProvider = document.querySelector('a[href*="/user/"], [class*="provider"]') !== null;
            
            return {
                hasOverview: hasOverview,
                hasContent: hasContent,
                hasProvider: hasProvider,
                totalElements: document.querySelectorAll('*').length
            };
            """
            
            validation_result = self.driver.execute_script(key_elements_script)
            logger.error(f"DOM validation: {validation_result}")
            
            if validation_result['totalElements'] < 100:
                logger.error("Page appears to be not fully loaded")
                await asyncio.sleep(2)  # Additional wait
            
            # Extract API description from 'API Overview' section
            description_script = """
            // Primary selector: API Overview section
            let description = '';
            
            // Look for "API Overview" heading and extract following content
            const overviewHeadings = document.querySelectorAll('h1, h2, h3, h4');
            for (let heading of overviewHeadings) {
                if (heading.textContent.toLowerCase().includes('api overview')) {
                    // Find following content div
                    let nextElement = heading.nextElementSibling;
                    while (nextElement) {
                        if (nextElement.classList.contains('markdown') || nextElement.querySelector('[class*="markdown"]')) {
                            const paragraphs = nextElement.querySelectorAll('p');
                            if (paragraphs.length > 0) {
                                description = Array.from(paragraphs).map(p => p.textContent.trim()).join(' ');
                                break;
                            }
                        }
                        nextElement = nextElement.nextElementSibling;
                    }
                    if (description) break;
                }
            }
            
            // Fallback selectors if API Overview not found
            if (!description) {
                const fallbackSelectors = [
                    '[class*="markdown"] p',
                    '.description p',
                    '[class*="desc"] p',
                    '.content p'
                ];
                
                for (let selector of fallbackSelectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        description = Array.from(elements).map(el => el.textContent.trim()).join(' ');
                        if (description.length > 50) break; // Ensure substantial content
                    }
                }
            }
            
            return description.trim();
            """
            
            description = self.driver.execute_script(description_script)
            if description and len(description) >= 50:  # Validation per spec
                enhanced_data['description'] = description
            
            # Extract rating and review data
            rating_script = """
            // Extract rating from star component
            let rating = null;
            let reviewCount = null;
            
            // Look for aria-label with rating info
            const ratingElements = document.querySelectorAll('[role="img"][aria-label*="Rated"], [aria-label*="Rated"]');
            for (let element of ratingElements) {
                const ariaLabel = element.getAttribute('aria-label');
                if (ariaLabel) {
                    // Parse "Rated X on 5" pattern
                    const ratingMatch = ariaLabel.match(/Rated\\s+(\\d+(?:\\.\\d+)?)\\s+on\\s+5/i);
                    if (ratingMatch) {
                        rating = parseFloat(ratingMatch[1]);
                        break;
                    }
                }
            }
            
            // Extract review count
            const reviewElements = document.querySelectorAll('.text-xs.font-medium.leading-0');
            for (let element of reviewElements) {
                const text = element.textContent;
                if (text && text.includes('(') && text.includes(')')) {
                    const countMatch = text.match(/\\((\\d+)\\)/);
                    if (countMatch) {
                        reviewCount = parseInt(countMatch[1]);
                        break;
                    }
                }
            }
            
            // Alternative: count star elements
            if (rating === null) {
                const starElements = document.querySelectorAll('.rr--box.rr--on');
                if (starElements.length > 0 && starElements.length <= 5) {
                    rating = starElements.length;
                }
            }
            
            return { rating, reviewCount };
            """
            
            rating_data = self.driver.execute_script(rating_script)
            if rating_data['rating'] is not None and 0.0 <= rating_data['rating'] <= 5.0:
                enhanced_data['rating'] = rating_data['rating']
            if rating_data['reviewCount'] is not None:
                enhanced_data['reviewCount'] = rating_data['reviewCount']
            
            # Extract performance metrics
            metrics_script = """
            // Extract popularity, service level, and latency
            let popularity = null;
            let serviceLevel = null;
            let latency = null;
            
            // Look for metrics in badge elements
            const badgeElements = document.querySelectorAll('[class*="gap-1.5"]');
            for (let element of badgeElements) {
                const text = element.textContent.toLowerCase();
                
                if (text.includes('popularity')) {
                    const popMatch = text.match(/([\\d.]+)\\s*popularity/i);
                    if (popMatch) popularity = parseFloat(popMatch[1]);
                }
                
                if (text.includes('service level')) {
                    const serviceMatch = text.match(/([\\d.]+)%\\s*service level/i);
                    if (serviceMatch) serviceLevel = parseFloat(serviceMatch[1]);
                }
                
                if (text.includes('latency')) {
                    const latencyMatch = text.match(/([\\d.]+\\s*ms)\\s*latency/i);
                    if (latencyMatch) latency = latencyMatch[1];
                }
            }
            
            return { popularity, serviceLevel, latency };
            """
            
            metrics_data = self.driver.execute_script(metrics_script)
            if metrics_data['popularity'] is not None:
                enhanced_data['popularity'] = metrics_data['popularity']
            if metrics_data['serviceLevel'] is not None:
                enhanced_data['serviceLevel'] = metrics_data['serviceLevel']
            if metrics_data['latency']:
                enhanced_data['latency'] = metrics_data['latency']
            
            # Extract pricing tiers
            pricing_script = """
            // Extract pricing from cards carousel
            let pricing = { tiers: [] };
            
            const pricingLinks = document.querySelectorAll('a[href*="pricing"] .rounded-lg');
            for (let card of pricingLinks) {
                const nameElement = card.querySelector('span.truncate');
                const priceElement = card.querySelector('.text-muted-foreground');
                
                if (nameElement && priceElement) {
                    const name = nameElement.textContent.trim().toUpperCase();
                    const priceText = priceElement.textContent.trim();
                    
                    // Parse monthly cost from price text  
                    let monthlyCost = null;
                    const costMatch = priceText.match(/\\$?([.\\d,]+)/);
                    if (costMatch) {
                        monthlyCost = parseFloat(costMatch[1].replace(',', ''));
                    }
                    
                    pricing.tiers.push({
                        name: name,
                        price: priceText,
                        monthly_cost: monthlyCost
                    });
                }
            }
            
            return pricing.tiers.length > 0 ? pricing : null;
            """
            
            pricing_data = self.driver.execute_script(pricing_script)
            if pricing_data and pricing_data['tiers']:
                enhanced_data['pricing'] = pricing_data
            
            # Extract provider information
            provider_script = """
            // Extract provider info from sidebar
            let provider = null;
            let subscribers = null;
            let category = null;
            
            // Provider name from user link
            const providerLink = document.querySelector('a[href*="/user/"] span.text-card-primary');
            if (providerLink) {
                provider = providerLink.textContent.trim();
            }
            
            // Subscriber count
            const subscriberElements = document.querySelectorAll('p.font-light.text-muted-foreground + p.font-normal');
            for (let element of subscriberElements) {
                const text = element.textContent;
                if (text && text.includes('subs')) {
                    const subMatch = text.match(/([\\d,]+)\\s*subs/i);
                    if (subMatch) {
                        subscribers = parseInt(subMatch[1].replace(',', ''));
                        break;
                    }
                }
            }
            
            // Category from badge
            const categoryElements = document.querySelectorAll('.bg-teal-500 span, [class*="category"] span');
            if (categoryElements.length > 0) {
                category = categoryElements[0].textContent.trim();
            }
            
            return { provider, subscribers, category };
            """
            
            provider_data = self.driver.execute_script(provider_script)
            if provider_data['provider']:
                enhanced_data['provider'] = provider_data['provider']
            if provider_data['subscribers']:
                enhanced_data['subscribers'] = provider_data['subscribers']
            if provider_data['category']:
                enhanced_data['category'] = provider_data['category']
            
            # Extract endpoint sections (basic visible endpoints only)
            endpoints_script = """
            // Extract visible endpoint information
            let endpoints = [];
            
            // Look for endpoint section buttons and titles
            const sectionButtons = document.querySelectorAll('button[aria-controls*="radix"]:has(.whitespace-nowrap)');
            
            for (let button of sectionButtons) {
                const titleElement = button.querySelector('.whitespace-nowrap.text-xs.font-normal');
                if (titleElement) {
                    const sectionName = titleElement.textContent.trim();
                    
                    // Check if section is expanded and has visible endpoints
                    const controlsId = button.getAttribute('aria-controls');
                    if (controlsId) {
                        const contentElement = document.getElementById(controlsId);
                        if (contentElement && contentElement.getAttribute('data-state') === 'open') {
                            const endpointLinks = contentElement.querySelectorAll('a[href*="playground"]');
                            
                            for (let link of endpointLinks) {
                                const endpointName = link.querySelector('.whitespace-nowrap')?.textContent.trim();
                                const methodElement = link.querySelector('.text-blue-500 span');
                                const method = methodElement?.textContent.trim();
                                
                                if (endpointName) {
                                    endpoints.push({
                                        section: sectionName,
                                        name: endpointName,
                                        method: method || 'GET',
                                        link: link.getAttribute('href')
                                    });
                                }
                            }
                        } else {
                            // Just record the section name even if not expanded
                            endpoints.push({
                                section: sectionName,
                                name: 'Section available (not expanded)',
                                method: 'UNKNOWN',
                                link: null
                            });
                        }
                    }
                }
            }
            
            return endpoints.length > 0 ? endpoints : null;
            """
            
            endpoints_data = self.driver.execute_script(endpoints_script)
            if endpoints_data:
                enhanced_data['endpoints'] = endpoints_data
            
        except Exception as e:
            logger.error(f"Error during DOM extraction: {e}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
        
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

    async def _navigate_to_page(self, api_url: str):
        """Navigate to the API page using exact undetected-chrome MCP code."""
        import time
        import random
        from selenium.common.exceptions import TimeoutException, WebDriverException
        
        logger.error(f"🔄 Navigating to {api_url}")
        start_time = time.time()
        
        try:
            if not self.driver:
                self.driver = self._get_chrome_driver()
            
            # Set page load timeout (copied from undetected-chrome MCP)
            timeout = 30  # seconds
            self.driver.set_page_load_timeout(timeout)
            
            # Navigate to URL (exact same as undetected-chrome MCP)
            self.driver.get(api_url)
            
            # Add human-like delay (copied from undetected-chrome MCP)
            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
            
            # Get final URL and title (same as undetected-chrome MCP)
            final_url = self.driver.current_url
            title = self.driver.title
            
            load_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            logger.error(f"🔄 Navigation successful: {final_url} (loaded in {load_time}ms)")
            return True
            
        except TimeoutException:
            error_msg = f"Navigation timeout after {timeout}s for URL: {api_url}"
            logger.error(error_msg)
            return False
            
        except WebDriverException as e:
            error_msg = f"WebDriver error during navigation: {str(e)}"
            logger.error(error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error during navigation: {str(e)}"
            logger.error(error_msg)
            return False
        
    async def _scrape_description(self) -> str:
        """Scrape API description using the exact working JavaScript from undetected-chrome test."""
        script = '''
        // Test the API Overview description extraction (exact copy from working test)
        let description = '';
        
        // Look for "API Overview" heading and extract following content
        const overviewHeadings = document.querySelectorAll('h1, h2, h3, h4');
        for (let heading of overviewHeadings) {
            if (heading.textContent.toLowerCase().includes('api overview')) {
                // Find following content div
                let nextElement = heading.nextElementSibling;
                while (nextElement) {
                    if (nextElement.classList.contains('markdown') || nextElement.querySelector('[class*="markdown"]')) {
                        const paragraphs = nextElement.querySelectorAll('p');
                        if (paragraphs.length > 0) {
                            description = Array.from(paragraphs).map(p => p.textContent.trim()).join(' ');
                            break;
                        }
                    }
                    nextElement = nextElement.nextElementSibling;
                }
                if (description) break;
            }
        }
        
        // Fallback selectors if API Overview not found
        if (!description) {
            const fallbackSelectors = [
                '[class*="markdown"] p',
                '.description p',
                '[class*="desc"] p',
                '.content p'
            ];
            
            for (let selector of fallbackSelectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    description = Array.from(elements).map(el => el.textContent.trim()).join(' ');
                    if (description.length > 50) break; // Ensure substantial content
                }
            }
        }
        
        return description.trim();
        '''
        
        # Execute JavaScript using exact undetected-chrome MCP pattern
        try:
            from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
            
            if not self.driver:
                logger.error("🔄 No Chrome driver available for description scraping")
                return ""
            
            # Set script timeout (copied from undetected-chrome MCP)
            timeout = 30  # seconds
            self.driver.set_script_timeout(timeout)
            
            # Execute the script (exact same as undetected-chrome MCP)
            result = self.driver.execute_script(script)
            
            # Process the result (copied from undetected-chrome MCP result processing)
            if result is None:
                description = ""
            elif isinstance(result, str):
                description = result
            else:
                description = str(result)
            
            logger.error(f"🔄 Scraped description: {description[:100]}...")
            return description if description and len(description) >= 50 else ""
            
        except JavascriptException as e:
            error_msg = f"JavaScript execution error during description scraping: {str(e)}"
            logger.error(error_msg)
            return ""
            
        except TimeoutException:
            error_msg = f"JavaScript execution timeout during description scraping"
            logger.error(error_msg)
            return ""
            
        except WebDriverException as e:
            error_msg = f"WebDriver error during description scraping: {str(e)}"
            logger.error(error_msg)
            return ""
            
        except Exception as e:
            error_msg = f"Unexpected error during description scraping: {str(e)}"
            logger.error(error_msg)
            return ""
        
    async def _scrape_pricing(self) -> dict:
        """Scrape pricing data using the exact working JavaScript from undetected-chrome test."""
        script = '''
        // Test pricing extraction from cards carousel (exact copy from working test)
        let pricing = { tiers: [] };
        
        const pricingLinks = document.querySelectorAll('a[href*="pricing"] .rounded-lg');
        for (let card of pricingLinks) {
            const nameElement = card.querySelector('span.truncate');
            const priceElement = card.querySelector('.text-muted-foreground');
            
            if (nameElement && priceElement) {
                const name = nameElement.textContent.trim().toUpperCase();
                const priceText = priceElement.textContent.trim();
                
                // Parse monthly cost from price text
                let monthlyCost = null;
                const costMatch = priceText.match(/\\$?([.\\d,]+)/);
                if (costMatch) {
                    monthlyCost = parseFloat(costMatch[1].replace(',', ''));
                }
                
                pricing.tiers.push({
                    name: name,
                    price: priceText,
                    monthly_cost: monthlyCost
                });
            }
        }
        
        return pricing.tiers.length > 0 ? pricing : null;
        '''
        
        # Execute JavaScript using exact undetected-chrome MCP pattern
        try:
            from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
            
            if not self.driver:
                logger.error("🔄 No Chrome driver available for pricing scraping")
                return {}
            
            # Set script timeout (copied from undetected-chrome MCP)
            timeout = 30  # seconds
            self.driver.set_script_timeout(timeout)
            
            # Execute the script (exact same as undetected-chrome MCP)
            result = self.driver.execute_script(script)
            
            # Process the result (copied from undetected-chrome MCP result processing)
            if result is None:
                pricing_data = {}
            elif isinstance(result, dict):
                pricing_data = result
            else:
                pricing_data = {}
            
            logger.error(f"🔄 Scraped pricing: {pricing_data}")
            return pricing_data if pricing_data else {}
            
        except JavascriptException as e:
            error_msg = f"JavaScript execution error during pricing scraping: {str(e)}"
            logger.error(error_msg)
            return {}
            
        except TimeoutException:
            error_msg = f"JavaScript execution timeout during pricing scraping"
            logger.error(error_msg)
            return {}
            
        except WebDriverException as e:
            error_msg = f"WebDriver error during pricing scraping: {str(e)}"
            logger.error(error_msg)
            return {}
            
        except Exception as e:
            error_msg = f"Unexpected error during pricing scraping: {str(e)}"
            logger.error(error_msg)
            return {}
        
    async def _scrape_ratings(self) -> dict:
        """Scrape rating and review data using the exact working JavaScript from undetected-chrome test."""
        script = '''
        // Test rating extraction (exact copy from working test)
        let rating = null;
        let reviewCount = null;
        
        // Look for aria-label with rating info
        const ratingElements = document.querySelectorAll('[role="img"][aria-label*="Rated"], [aria-label*="Rated"]');
        for (let element of ratingElements) {
            const ariaLabel = element.getAttribute('aria-label');
            if (ariaLabel) {
                // Parse "Rated X on 5" pattern
                const ratingMatch = ariaLabel.match(/Rated\\s+(\\d+(?:\\.\\d+)?)\\s+on\\s+5/i);
                if (ratingMatch) {
                    rating = parseFloat(ratingMatch[1]);
                    break;
                }
            }
        }
        
        // Extract review count
        const reviewElements = document.querySelectorAll('.text-xs.font-medium.leading-0');
        for (let element of reviewElements) {
            const text = element.textContent;
            if (text && text.includes('(') && text.includes(')')) {
                const countMatch = text.match(/\\((\\d+)\\)/);
                if (countMatch) {
                    reviewCount = parseInt(countMatch[1]);
                    break;
                }
            }
        }
        
        // Alternative: count star elements
        if (rating === null) {
            const starElements = document.querySelectorAll('.rr--box.rr--on');
            if (starElements.length > 0 && starElements.length <= 5) {
                rating = starElements.length;
            }
        }
        
        return { rating, reviewCount };
        '''
        
        # Execute JavaScript using exact undetected-chrome MCP pattern
        try:
            from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
            
            if not self.driver:
                logger.error("🔄 No Chrome driver available for rating scraping")
                return {}
            
            # Set script timeout (copied from undetected-chrome MCP)
            timeout = 30  # seconds
            self.driver.set_script_timeout(timeout)
            
            # Execute the script (exact same as undetected-chrome MCP)
            result = self.driver.execute_script(script)
            
            # Process the result (copied from undetected-chrome MCP result processing)
            if result is None:
                rating_data = {}
            elif isinstance(result, dict):
                rating_data = result
            else:
                rating_data = {}
            
            logger.error(f"🔄 Scraped ratings: {rating_data}")
            return rating_data if rating_data else {}
            
        except JavascriptException as e:
            error_msg = f"JavaScript execution error during rating scraping: {str(e)}"
            logger.error(error_msg)
            return {}
            
        except TimeoutException:
            error_msg = f"JavaScript execution timeout during rating scraping"
            logger.error(error_msg)
            return {}
            
        except WebDriverException as e:
            error_msg = f"WebDriver error during rating scraping: {str(e)}"
            logger.error(error_msg)
            return {}
            
        except Exception as e:
            error_msg = f"Unexpected error during rating scraping: {str(e)}"
            logger.error(error_msg)
            return {}
    
    async def _scrape_endpoint_sections(self) -> list:
        """Extract detailed endpoint sections by expanding collapsible sections."""
        script = '''
        // Extract endpoint sections with expansion (following documentation spec)
        let endpoints = [];
        
        // Find all collapsible endpoint section buttons
        const sectionButtons = document.querySelectorAll('button[aria-controls*="radix"]:has(.whitespace-nowrap)');
        
        for (let button of sectionButtons) {
            try {
                // Get section title
                const titleElement = button.querySelector('.whitespace-nowrap.text-xs.font-normal');
                const sectionName = titleElement ? titleElement.textContent.trim() : '';
                
                // Check if section is already expanded
                const isExpanded = button.getAttribute('aria-expanded') === 'true';
                
                if (!isExpanded) {
                    // Click to expand the section
                    button.click();
                    // Wait for expansion animation
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
                
                // Extract endpoints from expanded section
                const controlsId = button.getAttribute('aria-controls');
                const expandedContent = document.getElementById(controlsId);
                
                if (expandedContent) {
                    const endpointLinks = expandedContent.querySelectorAll('a[href*="playground"]');
                    
                    for (let link of endpointLinks) {
                        const endpointName = link.querySelector('.whitespace-nowrap')?.textContent?.trim() || '';
                        const methodElement = link.querySelector('.text-blue-500 span');
                        const method = methodElement?.textContent?.trim() || 'GET';
                        const playgroundUrl = link.href;
                        
                        if (endpointName) {
                            endpoints.push({
                                name: endpointName,
                                method: method,
                                section: sectionName,
                                playgroundUrl: playgroundUrl,
                                description: `${method} ${endpointName}`
                            });
                        }
                    }
                }
            } catch (error) {
                console.warn('Error processing section:', error);
            }
        }
        
        return endpoints;
        '''
        
        # Execute JavaScript using exact undetected-chrome MCP pattern
        try:
            from selenium.common.exceptions import JavascriptException, TimeoutException, WebDriverException
            
            if not self.driver:
                logger.error("🔄 No Chrome driver available for endpoint section scraping")
                return []
            
            # Set script timeout
            timeout = 45  # longer timeout for section expansion
            self.driver.set_script_timeout(timeout)
            
            # Execute the async script with proper callback handling
            async_script = f"""
            var callback = arguments[arguments.length - 1];
            (async function() {{
                {script}
            }})().then(callback).catch(err => callback([]));
            """
            
            result = self.driver.execute_async_script(async_script)
            
            # Process the result
            if result is None or not isinstance(result, list):
                endpoints = []
            else:
                endpoints = result
            
            logger.error(f"🔄 Scraped {len(endpoints)} endpoint sections")
            return endpoints
            
        except JavascriptException as e:
            error_msg = f"JavaScript execution error during endpoint section scraping: {str(e)}"
            logger.error(error_msg)
            return []
            
        except TimeoutException:
            error_msg = f"JavaScript execution timeout during endpoint section scraping"
            logger.error(error_msg)
            return []
            
        except WebDriverException as e:
            error_msg = f"WebDriver error during endpoint section scraping: {str(e)}"
            logger.error(error_msg)
            return []
            
        except Exception as e:
            error_msg = f"Unexpected error during endpoint section scraping: {str(e)}"
            logger.error(error_msg)
            return []

    async def _extract_endpoint_parameters(self, playground_url: str) -> dict:
        """Navigate to playground URL and extract detailed parameter information."""
        try:
            # Navigate to the playground page
            current_url = self.driver.current_url
            self.driver.get(playground_url)
            
            # Wait for playground page to load
            import time
            time.sleep(3)
            
            param_script = '''
            // Extract parameter information from playground page
            let parameters = {
                pathParams: [],
                queryParams: [],
                headers: [],
                requestBody: null,
                responseSchema: null
            };
            
            // Extract path parameters
            const pathElements = document.querySelectorAll('[data-testid*="path-param"], input[placeholder*="path"]');
            pathElements.forEach(el => {
                const name = el.getAttribute('name') || el.getAttribute('placeholder') || el.id;
                const required = el.hasAttribute('required') || el.getAttribute('aria-required') === 'true';
                if (name) {
                    parameters.pathParams.push({
                        name: name.replace(/[{}]/g, ''),
                        type: el.type || 'string',
                        required: required,
                        description: el.getAttribute('title') || ''
                    });
                }
            });
            
            // Extract query parameters
            const queryElements = document.querySelectorAll('[data-testid*="query-param"], input[placeholder*="query"]');
            queryElements.forEach(el => {
                const name = el.getAttribute('name') || el.getAttribute('placeholder') || el.id;
                const required = el.hasAttribute('required') || el.getAttribute('aria-required') === 'true';
                if (name) {
                    parameters.queryParams.push({
                        name: name,
                        type: el.type || 'string',
                        required: required,
                        description: el.getAttribute('title') || ''
                    });
                }
            });
            
            // Extract request body schema if present
            const requestBodyElement = document.querySelector('[data-testid*="request-body"], textarea[placeholder*="request"], .request-body');
            if (requestBodyElement) {
                parameters.requestBody = {
                    contentType: 'application/json',
                    schema: requestBodyElement.value || requestBodyElement.textContent || null
                };
            }
            
            // Extract response schema/example
            const responseElement = document.querySelector('[data-testid*="response"], .response-body, pre code');
            if (responseElement) {
                parameters.responseSchema = responseElement.textContent || null;
            }
            
            return parameters;
            '''
            
            # Execute parameter extraction script
            result = self.driver.execute_script(param_script)
            
            # Navigate back to original page
            self.driver.get(current_url)
            time.sleep(2)  # Wait for page to reload
            
            return result if result else {}
            
        except Exception as e:
            logger.error(f"Error extracting endpoint parameters from {playground_url}: {e}")
            # Make sure to navigate back on error
            try:
                self.driver.get(current_url)
            except:
                pass
            return {}
    
    async def close(self):
        """Close the Chrome driver and cleanup."""
        # Stop network monitoring if active
        if self.network_monitoring:
            await self.stop_network_monitoring()
            
        # Call parent close
        await super().close()