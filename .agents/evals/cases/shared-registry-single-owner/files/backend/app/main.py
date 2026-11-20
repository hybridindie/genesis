from fastapi import FastAPI

from app.reports.routes import router as reports_router

app = FastAPI(title="reports")
app.include_router(reports_router, prefix="/reports")
