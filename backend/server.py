from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
from io import StringIO, BytesIO

# Import scraping modules
from scraping.scraper import ScrapingEngine
from scraping.models import ScrapedData, ScrapingJob, BulkScrapingRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Connection closed, remove it
                self.active_connections.remove(connection)

manager = ConnectionManager()
scraping_engine = ScrapingEngine(db, manager)

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class SingleUrlRequest(BaseModel):
    url: str
    max_threads: int = Field(default=5, ge=1, le=25)

class ScrapingResponse(BaseModel):
    job_id: str
    status: str
    message: str

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Realtime Webscraper API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Single URL scraping endpoint
@api_router.post("/scrape/single", response_model=ScrapingResponse)
async def scrape_single_url(request: SingleUrlRequest):
    try:
        job_id = str(uuid.uuid4())
        
        # Create scraping job
        job = ScrapingJob(
            id=job_id,
            urls=[request.url],
            max_threads=request.max_threads,
            status="started",
            created_at=datetime.now(timezone.utc)
        )
        
        await db.scraping_jobs.insert_one(job.dict())
        
        # Start scraping in background
        asyncio.create_task(scraping_engine.scrape_urls([request.url], job_id, request.max_threads))
        
        return ScrapingResponse(
            job_id=job_id,
            status="started",
            message="Scraping job started. Check WebSocket for real-time updates."
        )
    except Exception as e:
        logging.error(f"Error starting single URL scraping: {e}")
        return ScrapingResponse(
            job_id="",
            status="error",
            message=f"Failed to start scraping: {str(e)}"
        )

# Bulk CSV scraping endpoint
@api_router.post("/scrape/bulk", response_model=ScrapingResponse)
async def scrape_bulk_urls(file: UploadFile = File(...), max_threads: int = Form(5)):
    try:
        if not file.filename.endswith('.csv'):
            return ScrapingResponse(
                job_id="",
                status="error",
                message="Please upload a CSV file"
            )
        
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode('utf-8')))
        
        if 'url' not in df.columns:
            return ScrapingResponse(
                job_id="",
                status="error",
                message="CSV must contain a 'url' column"
            )
        
        urls = df['url'].dropna().tolist()
        if not urls:
            return ScrapingResponse(
                job_id="",
                status="error",
                message="No valid URLs found in CSV"
            )
        
        job_id = str(uuid.uuid4())
        
        # Create scraping job
        job = ScrapingJob(
            id=job_id,
            urls=urls,
            max_threads=min(max_threads, 25),
            status="started",
            created_at=datetime.now(timezone.utc)
        )
        
        await db.scraping_jobs.insert_one(job.dict())
        
        # Start scraping in background
        asyncio.create_task(scraping_engine.scrape_urls(urls, job_id, min(max_threads, 25)))
        
        return ScrapingResponse(
            job_id=job_id,
            status="started",
            message=f"Bulk scraping job started for {len(urls)} URLs. Check WebSocket for real-time updates."
        )
    except Exception as e:
        logging.error(f"Error starting bulk scraping: {e}")
        return ScrapingResponse(
            job_id="",
            status="error",
            message=f"Failed to start bulk scraping: {str(e)}"
        )

# Get scraping job status
@api_router.get("/scrape/job/{job_id}")
async def get_job_status(job_id: str):
    try:
        job = await db.scraping_jobs.find_one({"id": job_id})
        if not job:
            return {"error": "Job not found"}
        return job
    except Exception as e:
        logging.error(f"Error getting job status: {e}")
        return {"error": str(e)}

# Get scraped results for a job
@api_router.get("/scrape/results/{job_id}")
async def get_job_results(job_id: str):
    try:
        results = await db.scraped_data.find({"job_id": job_id}).to_list(1000)
        return {"results": results, "count": len(results)}
    except Exception as e:
        logging.error(f"Error getting job results: {e}")
        return {"error": str(e)}

# Download results as CSV
@api_router.get("/scrape/download/{job_id}")
async def download_results(job_id: str):
    try:
        results = await db.scraped_data.find({"job_id": job_id}).sort("_id", 1).to_list(1000)
        
        if not results:
            return {"error": "No results found for this job"}
        
        # Convert to DataFrame
        df_data = []
        for result in results:
            row = {
                'input_url': result.get('url', ''),
                'phone_numbers': ', '.join(result.get('phone_numbers', [])),
                'email_address': result.get('email_address', ''),
                'linkedin_url': result.get('linkedin_url', ''),
                'facebook_url': result.get('facebook_url', ''),
                'instagram_url': result.get('instagram_url', ''),
                'github_url': result.get('github_url', ''),
            }
            
            # Add person details
            persons = result.get('persons', [])
            for i, person in enumerate(persons[:5], 1):  # Limit to 5 persons
                row[f'person_name_{i}'] = person.get('name', '')
                row[f'person_title_{i}'] = person.get('title', '')
                row[f'person_email_{i}'] = person.get('email', '')
                row[f'person_phone_{i}'] = person.get('phone', '')
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # Create CSV response
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=scraping_results_{job_id}.csv"}
        )
    except Exception as e:
        logging.error(f"Error downloading results: {e}")
        return {"error": str(e)}

# Sample CSV template download
@api_router.get("/scrape/template")
async def download_template():
    try:
        template_data = {
            'url': [
                'https://example.com',
                'https://company.com',
                'https://startup.io'
            ]
        }
        df = pd.DataFrame(template_data)
        
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=bulk_scraping_template.csv"}
        )
    except Exception as e:
        logging.error(f"Error creating template: {e}")
        return {"error": str(e)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()