import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.middleware import setup_cors, setup_exception_handlers, setup_security_headers, setup_rate_limiter, setup_audit_logging
from app.routers.api import api_router

logger = logging.getLogger(__name__)

_startup_time = None

def _run_scheduled_automations(trigger: str):
    """Background job: run scheduled automation rules for all users."""
    try:
        from app.database.session import SessionLocal
        from app.services.automation_service import AutomationRunner
        from app.models.automation import AutomationRule
        from sqlalchemy import select
        db = SessionLocal()
        try:
            user_ids = db.execute(
                select(AutomationRule.user_id)
                .where(AutomationRule.is_enabled == True, AutomationRule.trigger == trigger)
                .distinct()
            ).scalars().all()
            for uid in user_ids:
                try:
                    AutomationRunner.run_scheduled(db, uid, trigger)
                except Exception as e:
                    logger.warning("Scheduled automation failed for user %s: %s", uid, e)
        finally:
            db.close()
    except Exception as e:
        logger.error("Automation scheduler job error (%s): %s", trigger, e)


_scheduler = BackgroundScheduler(daemon=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _startup_time
    # Startup configurations
    setup_logging(
        env=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
        db_echo=settings.DB_ECHO
    )
    _startup_time = time.time()
    logger.info("Starting ExpenseFlow AI Backend service...")
    logger.info(f"App configuration: {settings.PROJECT_NAME} in v1 mode")

    # Validate SMTP Email Infrastructure
    from app.services.email_service import email_service
    email_service.validate_smtp_configuration()

    # Start automation scheduler
    _scheduler.add_job(_run_scheduled_automations, "cron", hour=1, minute=0, args=["daily"], id="auto_daily", replace_existing=True)
    _scheduler.add_job(_run_scheduled_automations, "cron", day_of_week="mon", hour=2, minute=0, args=["weekly"], id="auto_weekly", replace_existing=True)
    _scheduler.add_job(_run_scheduled_automations, "cron", day=1, hour=3, minute=0, args=["monthly"], id="auto_monthly", replace_existing=True)
    _scheduler.start()
    logger.info("==================================================")
    logger.info("ExpenseFlowAI Backend Configuration Loaded:")
    logger.info("AI_PROVIDER     : %s", settings.AI_PROVIDER)
    logger.info("GEMINI_MODEL    : %s", settings.GEMINI_MODEL)
    logger.info("==================================================")
    logger.info("Automation scheduler started (daily@01:00, weekly@Mon02:00, monthly@1st03:00)")

    # Pre-warm AI Provider
    try:
        from app.ai.factory import get_llm_provider
        provider = get_llm_provider()
        if hasattr(provider, "warmup"):
            provider.warmup()
    except Exception as _w_err:
        logger.warning("[AI Startup Warmup] Deferred warmup: %s", str(_w_err))

    yield

    # Shutdown cleaning processes
    _scheduler.shutdown(wait=False)
    logger.info("Shutting down ExpenseFlow AI Backend service...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ExpenseFlow AI — Track smarter. Save better. A production-ready personal finance management SaaS API.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Apply middleware stack (order matters: outermost first)
setup_security_headers(app)
setup_audit_logging(app)
setup_cors(app)
setup_rate_limiter(app)
setup_exception_handlers(app)

# Register central routers
from app.routers.personalization import router as personalization_router
from app.routers.dashboard_overview import router as dashboard_overview_router
from app.routers.digests import router as digests_router
from app.routers.explanations import router as explanations_router
from app.routers.chat_stream import router as chat_stream_router

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(personalization_router, prefix="/api/personalization", tags=["personalization-root-alias"])
app.include_router(dashboard_overview_router, prefix="/api/dashboard", tags=["command-center-root-alias"])
app.include_router(digests_router, prefix="/api", tags=["digests-root-alias"])
app.include_router(explanations_router, prefix="/api", tags=["explanations-root-alias"])
app.include_router(chat_stream_router, prefix="/api", tags=["chat-stream-root-alias"])


@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Access documentation at /docs",
        "version": "1.0.0"
    }


def get_uptime():
    """Get server uptime in seconds."""
    if _startup_time:
        return time.time() - _startup_time
    return 0
