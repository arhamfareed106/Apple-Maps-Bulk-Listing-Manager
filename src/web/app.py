"""
Web interface for Apple Maps Bulk Listing Manager
"""
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import asyncio
import json
import uuid
from datetime import datetime
import os

from ..config.settings import Settings
from ..engine.bulk_uploader import BulkUploader
from ..storage.database import get_db_manager
from ..storage.models import Location, SyncJob, SyncJobStatus


app = FastAPI(title="Apple Maps Bulk Listing Manager - Web Interface")

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="src/web/templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home dashboard page"""
    # Get statistics from database
    db_manager = get_db_manager(Settings())
    
    with db_manager.get_sync_session() as session:
        total_locations = session.query(Location).count()
        synced_locations = session.query(Location).filter(Location.status == 'synced').count()
        verifying_locations = session.query(Location).filter(Location.verification_status == 'pending').count()
        failed_locations = session.query(Location).filter(Location.status == 'failed').count()
        
        # Get recent jobs
        recent_jobs = session.query(SyncJob).order_by(SyncJob.started_at.desc()).limit(5).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_locations": total_locations,
        "synced_locations": synced_locations,
        "verifying_locations": verifying_locations,
        "failed_locations": failed_locations,
        "recent_jobs": recent_jobs
    })


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """File upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    aggregator: str = Form(...)
):
    """Handle file upload and start processing"""
    # Save uploaded file temporarily
    upload_dir = "data/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Create a job ID
    job_id = str(uuid.uuid4())
    
    # Return redirect to progress page
    return JSONResponse({"job_id": job_id, "redirect_url": f"/progress/{job_id}"})


@app.get("/progress/{job_id}", response_class=HTMLResponse)
async def progress_page(request: Request, job_id: str):
    """Progress tracking page"""
    return templates.TemplateResponse("progress.html", {
        "request": request,
        "job_id": job_id
    })


@app.get("/progress/stream/{job_id}")
async def progress_stream(job_id: str):
    """Server-sent events for real-time progress updates"""
    async def event_generator():
        # Simulate progress updates
        for i in range(0, 101, 10):
            if i == 100:
                yield f"data: {json.dumps({'progress': i, 'status': 'completed', 'success': 45, 'failed': 2})}\n\n"
            else:
                yield f"data: {json.dumps({'progress': i, 'status': 'processing', 'success': i//10*4, 'failed': i//50})}\n\n"
            await asyncio.sleep(1)
    
    return EventSourceResponse(event_generator())


@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports and analytics page"""
    db_manager = get_db_manager(Settings())
    
    with db_manager.get_sync_session() as session:
        # Get all sync jobs
        jobs = session.query(SyncJob).order_by(SyncJob.started_at.desc()).all()
    
    return templates.TemplateResponse("reports.html", {
        "request": request,
        "jobs": jobs
    })


from fastapi.responses import StreamingResponse
import json


@app.get("/progress/stream/{job_id}")
async def progress_stream(job_id: str):
    """Server-sent events for real-time progress updates"""
    
    async def event_generator():
        # Simulate progress updates
        for i in range(0, 101, 10):
            if i == 100:
                data = json.dumps({
                    'progress': i, 
                    'status': 'completed', 
                    'success': 45, 
                    'failed': 2,
                    'total': 47
                })
            else:
                data = json.dumps({
                    'progress': i, 
                    'status': 'processing', 
                    'success': i//10*4, 
                    'failed': i//50,
                    'total': i//10*4 + i//50
                })
            
            yield f"data: {data}\n\n"
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# Initialize the web app
web_app = app