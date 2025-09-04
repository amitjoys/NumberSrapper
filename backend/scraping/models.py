from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class PersonData(BaseModel):
    name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""

class ScrapedData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    url: str
    phone_numbers: List[str] = []
    email_address: str = ""
    linkedin_url: str = ""
    facebook_url: str = ""
    instagram_url: str = ""
    github_url: str = ""
    persons: List[PersonData] = []
    company_address: str = ""
    scraped_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    scraping_method: str = ""  # "beautifulsoup" or "playwright"
    error: Optional[str] = None
    success: bool = True

class ScrapingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    urls: List[str]
    max_threads: int = 5
    status: str = "pending"  # pending, started, completed, failed
    progress: int = 0
    total_urls: int = 0
    completed_urls: int = 0
    failed_urls: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    completed_at: Optional[datetime] = None
    results: List[str] = []  # List of scraped data IDs

class BulkScrapingRequest(BaseModel):
    urls: List[str]
    max_threads: int = Field(default=5, ge=1, le=25)

class CachedScrapeData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    data: ScrapedData
    last_scraped: datetime = Field(default_factory=lambda: datetime.utcnow())
    expires_at: datetime