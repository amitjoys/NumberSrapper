import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import json
import time
from urllib.parse import urljoin, urlparse
import re

from .models import ScrapedData, PersonData, CachedScrapeData
from .utils import (
    RateLimiter, extract_phone_numbers, extract_emails, 
    extract_social_media_urls, extract_persons_data, 
    clean_url, is_url_recently_scraped
)

logger = logging.getLogger(__name__)

class ScrapingEngine:
    def __init__(self, db, connection_manager):
        self.db = db
        self.connection_manager = connection_manager
        self.rate_limiter = RateLimiter(max_requests_per_domain=2, time_window=60)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        ]
        self.session = None
        
    async def get_session(self):
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def check_cache(self, url: str) -> Optional[ScrapedData]:
        """Check if URL was scraped recently (within 3 months)"""
        try:
            cached = await self.db.scraped_cache.find_one({"url": url})
            if cached and is_url_recently_scraped(cached.get('last_scraped'), cache_days=90):
                logger.info(f"Using cached data for {url}")
                return ScrapedData(**cached['data'])
            return None
        except Exception as e:
            logger.error(f"Error checking cache for {url}: {e}")
            return None
    
    async def save_to_cache(self, url: str, data: ScrapedData):
        """Save scraped data to cache"""
        try:
            cache_entry = CachedScrapeData(
                url=url,
                data=data,
                last_scraped=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=90)
            )
            
            await self.db.scraped_cache.replace_one(
                {"url": url},
                cache_entry.dict(),
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving to cache for {url}: {e}")
    
    async def scrape_with_requests(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape using aiohttp + BeautifulSoup (faster method)"""
        try:
            await self.rate_limiter.wait_for_slot(url)
            
            session = await self.get_session()
            headers = {
                'User-Agent': self.user_agents[hash(url) % len(self.user_agents)],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text_content = soup.get_text()
                    
                    return {
                        'html': html,
                        'text': text_content,
                        'soup': soup,
                        'method': 'beautifulsoup'
                    }
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error scraping {url} with requests: {e}")
            return None
    
    async def scrape_with_playwright(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape using Playwright (for JavaScript-heavy sites)"""
        try:
            await self.rate_limiter.wait_for_slot(url)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=self.user_agents[hash(url) % len(self.user_agents)],
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = await context.new_page()
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    await page.wait_for_timeout(2000)  # Wait for dynamic content
                    
                    html = await page.content()
                    text_content = await page.inner_text('body')
                    
                    await browser.close()
                    
                    soup = BeautifulSoup(html, 'lxml')
                    
                    return {
                        'html': html,
                        'text': text_content,
                        'soup': soup,
                        'method': 'playwright'
                    }
                    
                except Exception as e:
                    await browser.close()
                    raise e
                    
        except Exception as e:
            logger.error(f"Error scraping {url} with Playwright: {e}")
            return None
    
    def extract_company_address(self, soup, text_content: str) -> str:
        """Extract company address from content"""
        address = ""
        
        # Look for address patterns
        address_patterns = [
            r'\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)[.,\s]+[A-Z][a-z]+[.,\s]+[A-Z]{2}\s+\d{5}',
            r'[A-Z][a-z]+[.,\s]+[A-Z]{2}\s+\d{5}',
        ]
        
        # Look in structured data
        address_selectors = [
            '[itemtype*="PostalAddress"]',
            '.address',
            '#address',
            '[class*="address"]',
            '[class*="location"]',
            '.contact-info'
        ]
        
        for selector in address_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if len(text) > 10 and any(word in text.lower() for word in ['street', 'avenue', 'road', 'drive']):
                    address = text
                    break
            if address:
                break
        
        if not address:
            for pattern in address_patterns:
                matches = re.findall(pattern, text_content)
                if matches:
                    address = matches[0]
                    break
        
        return address[:200]  # Limit length
    
    async def extract_data_from_content(self, content_data: Dict[str, Any], url: str) -> ScrapedData:
        """Extract all relevant data from scraped content"""
        html = content_data['html']
        text_content = content_data['text']
        soup = content_data['soup']
        method = content_data['method']
        
        # Extract phone numbers
        phone_numbers = extract_phone_numbers(text_content)
        
        # Extract emails
        emails = extract_emails(text_content)
        primary_email = emails[0] if emails else ""
        
        # Extract social media URLs
        social_urls = extract_social_media_urls(text_content, html)
        
        # Extract persons data
        persons_data = extract_persons_data(text_content, html)
        persons = [PersonData(**person) for person in persons_data]
        
        # Extract company address
        company_address = self.extract_company_address(soup, text_content)
        
        scraped_data = ScrapedData(
            job_id="",  # Will be set by caller
            url=url,
            phone_numbers=phone_numbers,
            email_address=primary_email,
            linkedin_url=social_urls['linkedin_url'],
            facebook_url=social_urls['facebook_url'],
            instagram_url=social_urls['instagram_url'],
            github_url=social_urls['github_url'],
            persons=persons,
            company_address=company_address,
            scraped_at=datetime.now(timezone.utc),
            scraping_method=method,
            success=True
        )
        
        return scraped_data
    
    async def scrape_single_url(self, url: str, job_id: str) -> ScrapedData:
        """Scrape a single URL with fallback strategy"""
        url = clean_url(url)
        
        # Check cache first
        cached_data = await self.check_cache(url)
        if cached_data:
            cached_data.job_id = job_id
            return cached_data
        
        scraped_data = None
        
        try:
            # Try BeautifulSoup first (faster)
            content_data = await self.scrape_with_requests(url)
            
            if content_data:
                scraped_data = await self.extract_data_from_content(content_data, url)
                logger.info(f"Successfully scraped {url} with BeautifulSoup")
            else:
                # Fallback to Playwright for JavaScript-heavy sites
                logger.info(f"Trying Playwright for {url}")
                content_data = await self.scrape_with_playwright(url)
                
                if content_data:
                    scraped_data = await self.extract_data_from_content(content_data, url)
                    logger.info(f"Successfully scraped {url} with Playwright")
                else:
                    # Create failed result
                    scraped_data = ScrapedData(
                        job_id=job_id,
                        url=url,
                        scraped_at=datetime.now(timezone.utc),
                        success=False,
                        error="Failed to scrape with both methods"
                    )
                    logger.error(f"Failed to scrape {url} with both methods")
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            scraped_data = ScrapedData(
                job_id=job_id,
                url=url,
                scraped_at=datetime.now(timezone.utc),
                success=False,
                error=str(e)
            )
        
        if scraped_data:
            scraped_data.job_id = job_id
            
            # Save to cache if successful
            if scraped_data.success:
                await self.save_to_cache(url, scraped_data)
        
        return scraped_data
    
    async def update_job_progress(self, job_id: str, completed: int, total: int, failed: int):
        """Update job progress in database and send WebSocket update"""
        try:
            progress = int((completed / total) * 100) if total > 0 else 0
            
            await self.db.scraping_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "progress": progress,
                        "completed_urls": completed,
                        "failed_urls": failed,
                        "status": "completed" if completed + failed >= total else "in_progress"
                    }
                }
            )
            
            # Send WebSocket update (ensure all data is JSON serializable)
            message = {
                "type": "progress_update",
                "job_id": str(job_id),
                "progress": int(progress),
                "completed": int(completed),
                "total": int(total),
                "failed": int(failed),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.connection_manager.broadcast(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Error updating job progress: {e}")
    
    async def scrape_urls(self, urls: List[str], job_id: str, max_threads: int = 5):
        """Scrape multiple URLs with threading and progress tracking"""
        try:
            total_urls = len(urls)
            completed = 0
            failed = 0
            
            # Update job to started
            await self.db.scraping_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": "in_progress", "total_urls": total_urls}}
            )
            
            # Create semaphore for controlling concurrency
            semaphore = asyncio.Semaphore(max_threads)
            
            async def scrape_with_semaphore(url: str, index: int):
                nonlocal completed, failed
                
                async with semaphore:
                    try:
                        # Send start message
                        start_message = {
                            "type": "url_start",
                            "job_id": str(job_id),
                            "url": str(url),
                            "index": int(index),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await self.connection_manager.broadcast(json.dumps(start_message))
                        
                        result = await self.scrape_single_url(url, job_id)
                        
                        # Save to database
                        await self.db.scraped_data.insert_one(result.dict())
                        
                        if result.success:
                            completed += 1
                        else:
                            failed += 1
                        
                        # Send completion message (serialize datetime objects)
                        result_data = None
                        if result.success and result:
                            result_data = result.dict()
                            # Convert datetime to ISO string for JSON serialization
                            if "scraped_at" in result_data and result_data["scraped_at"]:
                                result_data["scraped_at"] = result_data["scraped_at"].isoformat()
                        
                        complete_message = {
                            "type": "url_complete",
                            "job_id": str(job_id),
                            "url": str(url),
                            "index": int(index),
                            "success": bool(result.success),
                            "data": result_data,
                            "error": str(result.error) if result.error else None,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await self.connection_manager.broadcast(json.dumps(complete_message))
                        
                        # Update progress
                        await self.update_job_progress(job_id, completed, total_urls, failed)
                        
                    except Exception as e:
                        failed += 1
                        logger.error(f"Error in scrape_with_semaphore for {url}: {e}")
                        
                        error_message = {
                            "type": "url_error",
                            "job_id": job_id,
                            "url": url,
                            "index": index,
                            "error": str(e)
                        }
                        await self.connection_manager.broadcast(json.dumps(error_message))
                        
                        await self.update_job_progress(job_id, completed, total_urls, failed)
            
            # Create tasks for all URLs with their indices to maintain order
            tasks = []
            for index, url in enumerate(urls):
                task = asyncio.create_task(scrape_with_semaphore(url, index))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Mark job as completed
            await self.db.scraping_jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # Send final completion message
            final_message = {
                "type": "job_complete",
                "job_id": job_id,
                "total": total_urls,
                "completed": completed,
                "failed": failed
            }
            await self.connection_manager.broadcast(json.dumps(final_message))
            
            logger.info(f"Job {job_id} completed: {completed} successful, {failed} failed out of {total_urls}")
            
        except Exception as e:
            logger.error(f"Error in scrape_urls for job {job_id}: {e}")
            
            # Mark job as failed
            await self.db.scraping_jobs.update_one(
                {"id": job_id},
                {"$set": {"status": "failed", "error": str(e)}}
            )
            
            error_message = {
                "type": "job_error",
                "job_id": job_id,
                "error": str(e)
            }
            await self.connection_manager.broadcast(json.dumps(error_message))
        
        finally:
            await self.close_session()