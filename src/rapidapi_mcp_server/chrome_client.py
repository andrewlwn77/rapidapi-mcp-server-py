"""Chrome client using undetected-chromedriver for web scraping RapidAPI marketplace with network monitoring."""

import asyncio
import json
import logging
import os
import time
import random
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException


logger = logging.getLogger(__name__)


class ChromeClient:
    """Client for interacting with undetected Chrome to scrape RapidAPI marketplace with network monitoring."""

    def __init__(self):
        self.driver: Optional[uc.Chrome] = None

    def _get_chrome_driver(self) -> uc.Chrome:
        """Create and configure undetected Chrome driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

        # Chrome options (copied from working undetected-chrome-mcp)
        options = uc.ChromeOptions()
        
        # Basic stealth arguments (from working chrome_manager.py)
        stealth_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage", 
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-default-apps",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-background-networking",
            "--disable-sync",
            "--no-default-browser-check",
            "--no-first-run"
        ]
        
        for arg in stealth_args:
            options.add_argument(arg)
        
        # Random user agent (from working chrome_manager.py)
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ]
        import random
        user_agent = random.choice(user_agents)
        options.add_argument(f"--user-agent={user_agent}")
        
        # Random window size for fingerprint variation (from working chrome_manager.py)
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f"--window-size={width},{height}")
        
        # Set headless mode
        options.add_argument("--headless=new")
        
        # Get custom Chrome executable path if set
        chrome_executable = os.getenv('CHROME_EXECUTABLE_PATH', '/opt/google/chrome/google-chrome')
        
        try:
            if os.path.exists(chrome_executable):
                options.binary_location = chrome_executable
                logger.info(f"Using Chrome executable: {chrome_executable}")
            
            # Create undetected Chrome driver with CDP events enabled (CRITICAL FOR NETWORK MONITORING)
            self.driver = uc.Chrome(
                options=options,
                version_main=None,  # Auto-detect Chrome version
                use_subprocess=True,
                headless=True if "--headless" in str(options.arguments) else False,  # Conditional headless like working chrome_manager.py
                enable_cdp_events=True  # Enable CDP for network monitoring (from working chrome_manager.py)
            )
            
            # Set implicit wait and page load timeout
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)  # Match working chrome_manager.py
            
            # Apply additional anti-detection measures (from working chrome_manager.py)
            self._apply_stealth_scripts(self.driver)
            
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to create Chrome driver: {e}")
            raise

    def _apply_stealth_scripts(self, driver: uc.Chrome):
        """Apply additional JavaScript-based stealth measures (from working chrome_manager.py)."""
        stealth_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {
                return {
                    connectionInfo: 'http/1.1',
                    finishDocumentLoadTime: Date.now(),
                    finishLoadTime: Date.now(),
                    firstPaintAfterLoadTime: 0,
                    firstPaintTime: Date.now(),
                    navigationType: 'Other',
                    npnNegotiatedProtocol: 'unknown',
                    requestTime: Date.now() - 1000,
                    startLoadTime: Date.now() - 1000,
                    wasAlternateProtocolAvailable: false,
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false
                };
            },
            csi: function() {
                return {
                    onloadT: Date.now(),
                    pageT: Date.now() - 1000,
                    startE: Date.now() - 1000,
                    tran: 15
                };
            }
        };
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        """
        
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': stealth_script
            })
        except Exception as e:
            logger.warning(f"Could not apply stealth scripts: {e}")

    def _human_like_delay(self, min_delay: float = 0.1, max_delay: float = 0.5) -> None:
        """Add human-like delays between actions (from working chrome_manager.py)."""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    async def search_apis(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """Search for APIs in RapidAPI marketplace.

        Args:
            query: Search query for APIs
            max_results: Maximum number of results to return

        Returns:
            Dictionary containing search results
        """
        logger.info(f"Searching RapidAPI for: {query}")

        driver = None
        try:
            def _search_sync():
                nonlocal driver
                driver = self._get_chrome_driver()
                
                # Navigate to RapidAPI hub
                logger.info("Navigating to RapidAPI hub")
                driver.get('https://rapidapi.com/hub')
                
                # Add human-like delay
                self._human_like_delay(1.0, 3.0)
                
                # Use natural search workflow (Ctrl+K method from original code)
                logger.info('Activating search with Ctrl+K shortcut')
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.CONTROL, "k")
                
                # Wait for search modal and type query
                try:
                    search_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Search..."]'))
                    )
                    search_input.send_keys(query)
                    search_input.send_keys(Keys.ENTER)
                except TimeoutException:
                    logger.warning("Search modal not found, trying alternative method")
                    # Fallback to direct search URL
                    driver.get(f'https://rapidapi.com/search?term={query}')
                
                # Wait for search results
                self._human_like_delay(2.0, 4.0)
                
                # Get page source and parse with BeautifulSoup
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract API results
                apis = []
                
                # Look for API cards using various selectors
                card_selectors = [
                    'div[class*="group/card"]',
                    'div[class*="card"]',
                    'div[class*="api"]'
                ]
                
                api_cards = []
                for selector in card_selectors:
                    api_cards = soup.select(selector)
                    if api_cards:
                        break
                
                for i, card in enumerate(api_cards[:max_results]):
                    try:
                        api_data = {
                            'name': '',
                            'description': '',
                            'provider': '',
                            'url': '',
                            'rating': None,
                            'popularity': None
                        }
                        
                        # Extract API name
                        name_el = card.select_one('h3, h4, [class*="title"], [class*="name"], a[href*="/api/"]')
                        if name_el:
                            api_data['name'] = name_el.get_text(strip=True)
                        
                        # Extract description
                        desc_el = card.select_one('p, [class*="description"], [class*="summary"]')
                        if desc_el:
                            api_data['description'] = desc_el.get_text(strip=True)
                        
                        # Extract provider
                        provider_el = card.select_one('[class*="provider"], [class*="author"], [class*="by"]')
                        if provider_el:
                            provider_text = provider_el.get_text(strip=True)
                            api_data['provider'] = provider_text.replace('by ', '', 1)
                        
                        # Extract URL
                        link_el = card.select_one('a[href*="/api/"], a[href*="rapidapi.com"]')
                        if link_el:
                            href = link_el.get('href', '')
                            if href.startswith('/'):
                                api_data['url'] = f"https://rapidapi.com{href}"
                            else:
                                api_data['url'] = href
                        
                        # Extract rating if available
                        rating_el = card.select_one('[class*="rating"], [class*="score"], [title*="star"]')
                        if rating_el:
                            rating_text = rating_el.get_text(strip=True)
                            import re
                            rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                            if rating_match:
                                try:
                                    api_data['rating'] = float(rating_match.group(1))
                                except ValueError:
                                    pass
                        
                        # Only add if we have essential information
                        if api_data['name'] and api_data['url']:
                            apis.append(api_data)
                            
                    except Exception as e:
                        logger.warning(f"Error extracting API data from card {i}: {e}")
                        continue
                
                logger.info(f"Found {len(apis)} API results")
                return {
                    'query': query,
                    'resultsCount': len(apis),
                    'apis': apis
                }
            
            # Run the synchronous operation in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _search_sync)
            return result
            
        except Exception as e:
            logger.error(f"Error searching APIs: {e}")
            raise
        finally:
            # Clean up driver
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                self.driver = None

    async def assess_api(self, api_url: str) -> Dict[str, Any]:
        """Get comprehensive assessment of a specific API.

        Args:
            api_url: RapidAPI URL for the specific API

        Returns:
            Dictionary containing API assessment data
        """
        logger.error(f"⚠️ BASIC ASSESS_API CALLED (no network monitoring) for: {api_url}")

        driver = None
        try:
            def _assess_sync():
                nonlocal driver
                driver = self._get_chrome_driver()
                
                # Navigate to API detail page
                logger.info(f"Navigating to {api_url}")
                driver.get(api_url)
                
                # Add human-like delay
                self._human_like_delay(2.0, 4.0)
                
                # Wait for page content to load
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'h1, [class*="title"]'))
                    )
                except TimeoutException:
                    logger.warning("Timeout waiting for page content")
                
                # Get page source and parse
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract API details
                assessment = {
                    'name': '',
                    'description': '',
                    'provider': '',
                    'url': api_url,
                    'rating': None,
                    'reviewCount': None,
                    'popularity': None,
                    'serviceLevel': None,
                    'latency': None,
                    'pricing': {},
                    'endpoints': [],
                    'documentationUrl': None
                }
                
                # Extract API name
                name_el = soup.select_one('h1, [class*="api-title"], [class*="title"]')
                if name_el:
                    assessment['name'] = name_el.get_text(strip=True)
                
                # Extract description
                desc_selectors = [
                    '[class*="description"]',
                    '[class*="overview"]',
                    'p:not([class*="metric"]):not([class*="stat"])'
                ]
                for selector in desc_selectors:
                    desc_el = soup.select_one(selector)
                    if desc_el and len(desc_el.get_text(strip=True)) > 50:
                        assessment['description'] = desc_el.get_text(strip=True)
                        break
                
                # Extract provider
                provider_el = soup.select_one('[class*="provider"], [class*="author"], [href*="provider"]')
                if provider_el:
                    provider_text = provider_el.get_text(strip=True)
                    assessment['provider'] = provider_text.replace('by ', '', 1)
                
                # Extract rating
                rating_el = soup.select_one('[class*="rating"], [title*="star"]')
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    import re
                    rating_match = re.search(r'(\d+(?:\.\d+)?)', rating_text)
                    if rating_match:
                        try:
                            assessment['rating'] = float(rating_match.group(1))
                        except ValueError:
                            pass
                
                # Extract endpoints from sidebar or documentation
                endpoint_selectors = [
                    '[class*="endpoint"]',
                    '[class*="method"]',
                    'nav a[href*="endpoint"]',
                    'aside a',
                    '[class*="sidebar"] a'
                ]
                
                endpoints = []
                for selector in endpoint_selectors:
                    endpoint_elements = soup.select(selector)
                    for element in endpoint_elements:
                        text = element.get_text(strip=True)
                        if text and 'api' in text.lower() and 'overview' not in text.lower():
                            # Extract HTTP method if present
                            import re
                            method_match = re.match(r'^(GET|POST|PUT|DELETE|PATCH)\s*(.+)', text, re.IGNORECASE)
                            
                            endpoint_data = {
                                'name': method_match.group(2) if method_match else text,
                                'method': method_match.group(1).upper() if method_match else 'GET',
                                'description': text
                            }
                            
                            # Avoid duplicates
                            if not any(ep['name'] == endpoint_data['name'] and ep['method'] == endpoint_data['method'] 
                                     for ep in endpoints):
                                endpoints.append(endpoint_data)
                
                assessment['endpoints'] = endpoints[:10]  # Limit to avoid too much data
                
                # Static scraping complete
                
                return assessment
            
            # Run the synchronous operation in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _assess_sync)
            return result
            
        except Exception as e:
            logger.error(f"Error assessing API: {e}")
            raise
        finally:
            # Clean up driver
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
                self.driver = None

    async def close(self):
        """Close the Chrome driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None