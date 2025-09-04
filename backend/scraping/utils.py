import re
import phonenumbers
from phonenumbers import NumberParseException
from typing import List, Set
import asyncio
from collections import defaultdict
import time
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests_per_domain: int = 3, time_window: int = 60):
        self.max_requests = max_requests_per_domain
        self.time_window = time_window
        self.domain_requests = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def can_make_request(self, url: str) -> bool:
        domain = urlparse(url).netloc
        async with self.lock:
            now = time.time()
            # Clean old requests
            self.domain_requests[domain] = [
                req_time for req_time in self.domain_requests[domain]
                if now - req_time < self.time_window
            ]
            
            if len(self.domain_requests[domain]) < self.max_requests:
                self.domain_requests[domain].append(now)
                return True
            return False
    
    async def wait_for_slot(self, url: str):
        while not await self.can_make_request(url):
            await asyncio.sleep(1)

def extract_phone_numbers(text: str) -> List[str]:
    """Extract and validate phone numbers in E164 format"""
    if not text:
        return []
    
    # Common phone number patterns
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+?\d{10,15}',
        r'\(\d{3}\)\s?\d{3}[-.\s]?\d{4}',
        r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+\d{1,3}\s?\d{1,14}',
    ]
    
    phone_numbers = set()
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean the number
            cleaned = re.sub(r'[^\d+]', '', match)
            if len(cleaned) >= 10:
                try:
                    # Try to parse as US number first, then international
                    parsed = None
                    if not cleaned.startswith('+'):
                        try:
                            parsed = phonenumbers.parse(cleaned, 'US')
                        except NumberParseException:
                            try:
                                parsed = phonenumbers.parse('+' + cleaned, None)
                            except NumberParseException:
                                continue
                    else:
                        parsed = phonenumbers.parse(cleaned, None)
                    
                    if parsed and phonenumbers.is_valid_number(parsed):
                        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                        phone_numbers.add(e164)
                except NumberParseException:
                    continue
    
    return list(phone_numbers)

def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    if not text:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Filter out common false positives
    filtered_emails = []
    skip_domains = {'example.com', 'test.com', 'domain.com', 'email.com'}
    
    for email in emails:
        domain = email.split('@')[1].lower()
        if domain not in skip_domains and not domain.endswith('.png') and not domain.endswith('.jpg'):
            filtered_emails.append(email.lower())
    
    return list(set(filtered_emails))

def extract_social_media_urls(text: str, html_content: str = "") -> dict:
    """Extract social media URLs"""
    social_urls = {
        'linkedin_url': '',
        'facebook_url': '',
        'instagram_url': '',
        'github_url': ''
    }
    
    content = f"{text} {html_content}"
    
    patterns = {
        'linkedin_url': [
            r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+',
            r'linkedin\.com/(?:company|in)/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+'
        ],
        'facebook_url': [
            r'https?://(?:www\.)?facebook\.com/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+',
            r'facebook\.com/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+'
        ],
        'instagram_url': [
            r'https?://(?:www\.)?instagram\.com/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+',
            r'instagram\.com/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+'
        ],
        'github_url': [
            r'https?://(?:www\.)?github\.com/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+',
            r'github\.com/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]+'
        ]
    }
    
    for social_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                url = matches[0]
                if not url.startswith('http'):
                    url = 'https://' + url
                social_urls[social_type] = url
                break
    
    return social_urls

def extract_persons_data(text: str, html_content: str = "") -> List[dict]:
    """Extract person information from text"""
    persons = []
    content = f"{text} {html_content}"
    
    # Look for common patterns that indicate person information
    # This is a simplified version - in production, you might use NLP libraries
    
    # Pattern for "Name - Title" or "Name, Title"
    name_title_patterns = [
        r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[-,]\s*([A-Z][^.!?]*?)(?=[.!?]|\n|$)',
        r'<h[1-6][^>]*>([^<]+)</h[1-6]>',  # Names in headers
    ]
    
    emails = extract_emails(content)
    phones = extract_phone_numbers(content)
    
    # Simple extraction - this could be enhanced with NLP
    for pattern in name_title_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if isinstance(match, tuple) and len(match) == 2:
                name, title = match
                if len(name.split()) >= 2 and len(name) > 3:  # Basic validation
                    person = {
                        'name': name.strip(),
                        'title': title.strip(),
                        'email': emails[len(persons)] if len(persons) < len(emails) else '',
                        'phone': phones[len(persons)] if len(persons) < len(phones) else ''
                    }
                    persons.append(person)
                    if len(persons) >= 5:  # Limit to 5 persons
                        break
    
    return persons

def clean_url(url: str) -> str:
    """Clean and validate URL"""
    if not url:
        return ""
    
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

def is_url_recently_scraped(last_scraped, cache_days: int = 90) -> bool:
    """Check if URL was scraped within the cache period"""
    if not last_scraped:
        return False
    
    from datetime import datetime, timezone, timedelta
    
    # Ensure last_scraped is timezone-aware
    if isinstance(last_scraped, datetime):
        if last_scraped.tzinfo is None:
            # If naive, assume UTC
            last_scraped = last_scraped.replace(tzinfo=timezone.utc)
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=cache_days)
    return last_scraped > cutoff_date