"""
SOGS - Snowflake Optimizer & Governance Suite
Main FastAPI Application
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import uvicorn

from config import settings
from snowflake_manager import snowflake_manager
from modules.cost_intelligence import CostIntelligenceEngine
from modules.performance_advisor import PerformanceAdvisor
from modules.governance_security import GovernanceSecurityHub
from modules.migration_toolkit import MigrationToolkit
from modules.ai_ml_monitor import AIMLMonitor
from modules.query_explorer import QueryExplorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Comprehensive Snowflake optimization, governance, and migration platform"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize modules
cost_engine = CostIntelligenceEngine(snowflake_manager)
performance_advisor = PerformanceAdvisor(snowflake_manager)
governance_hub = GovernanceSecurityHub(snowflake_manager)
migration_toolkit = MigrationToolkit(snowflake_manager)
ai_ml_monitor = AIMLMonitor(snowflake_manager)
query_explorer = QueryExplorer(snowflake_manager)


# Pydantic models
class SnowflakeCredentials(BaseModel):
    account: str
    user: str
    password: str
    warehouse: Optional[str] = None
    database: Optional[str] = None
    schema: Optional[str] = None
    role: Optional[str] = None


class QueryAnalysisRequest(BaseModel):
    query_text: str


class SQLConversionRequest(BaseModel):
    sql_text: str
    source_dialect: str = "oracle"


class SchemaAnalysisRequest(BaseModel):
    database: str
    schema: str


# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request, "app_name": settings.APP_NAME})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Credentials endpoints
@app.post("/api/credentials/configure")
async def configure_credentials(credentials: SnowflakeCredentials):
    """Configure Snowflake credentials"""
    try:
        snowflake_manager.set_credentials(
            account=credentials.account,
            user=credentials.user,
            password=credentials.password,
            warehouse=credentials.warehouse,
            database=credentials.database,
            schema=credentials.schema,
            role=credentials.role,
        )

        # Test the connection
        result = snowflake_manager.test_connection()

        if result["success"]:
            logger.info(f"Credentials configured successfully for user: {credentials.user}")
            return {
                "success": True,
                "message": "Credentials configured and tested successfully",
                "snowflake_version": result.get("version"),
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error"))

    except Exception as e:
        logger.error(f"Failed to configure credentials: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/credentials/test")
async def test_credentials():
    """Test current credentials"""
    result = snowflake_manager.test_connection()
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error"))


# Cost Intelligence endpoints
@app.get("/api/cost/summary")
async def get_cost_summary(days: int = 30):
    """Get cost summary"""
    try:
        summary = cost_engine.get_cost_summary(days=days)
        return summary
    except Exception as e:
        logger.error(f"Failed to get cost summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/by-warehouse")
async def get_cost_by_warehouse(days: int = 7):
    """Get cost breakdown by warehouse"""
    try:
        costs = cost_engine.get_cost_by_warehouse(days=days)
        return {"warehouses": costs}
    except Exception as e:
        logger.error(f"Failed to get cost by warehouse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/idle-warehouses")
async def get_idle_warehouses(threshold_minutes: int = 60):
    """Get idle warehouses"""
    try:
        idle = cost_engine.detect_idle_warehouses(idle_threshold_minutes=threshold_minutes)
        return {"idle_warehouses": idle}
    except Exception as e:
        logger.error(f"Failed to detect idle warehouses: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/anomalies")
async def get_cost_anomalies(threshold_percentage: float = 50.0):
    """Detect cost anomalies"""
    try:
        anomalies = cost_engine.get_cost_anomalies(threshold_percentage=threshold_percentage)
        return {"anomalies": anomalies}
    except Exception as e:
        logger.error(f"Failed to detect cost anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cost/recommendations")
async def get_cost_recommendations():
    """Get cost optimization recommendations"""
    try:
        recommendations = cost_engine.generate_warehouse_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get cost recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Performance endpoints
@app.get("/api/performance/slow-queries")
async def get_slow_queries(days: int = 7, min_duration_ms: int = 10000):
    """Get slow queries"""
    try:
        queries = performance_advisor.get_slow_queries(days=days, min_duration_ms=min_duration_ms)
        return {"slow_queries": queries}
    except Exception as e:
        logger.error(f"Failed to get slow queries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/performance/analyze-query")
async def analyze_query(request: QueryAnalysisRequest):
    """Analyze a query for optimization opportunities"""
    try:
        analysis = performance_advisor.analyze_query(request.query_text)
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/query-profile/{query_id}")
async def get_query_profile(query_id: str):
    """Get detailed query profile"""
    try:
        profile = performance_advisor.get_query_profile(query_id)
        return profile
    except Exception as e:
        logger.error(f"Failed to get query profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/performance/recommendations")
async def get_performance_recommendations():
    """Get performance recommendations"""
    try:
        recommendations = performance_advisor.generate_performance_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get performance recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Query Explorer endpoints
@app.get("/api/queries/all")
async def get_all_queries(
    days: int = 7,
    limit: int = 100,
    execution_status: str = None,
    user_filter: str = None,
    warehouse_filter: str = None
):
    """Get all queries with optional filters"""
    try:
        queries = query_explorer.get_all_queries(
            days=days,
            limit=limit,
            execution_status=execution_status,
            user_filter=user_filter,
            warehouse_filter=warehouse_filter
        )
        return {"queries": queries, "total": len(queries)}
    except Exception as e:
        logger.error(f"Failed to get all queries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queries/{query_id}/profile")
async def get_query_detailed_profile(query_id: str):
    """Get detailed profile for a specific query"""
    try:
        profile = query_explorer.get_query_detailed_profile(query_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Query not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queries/{query_id}/analyze")
async def analyze_query_best_practices(query_id: str):
    """Analyze query against Snowflake best practices"""
    try:
        analysis = query_explorer.analyze_query_with_best_practices(query_id)
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Governance endpoints
@app.get("/api/governance/user-access-audit")
async def get_user_access_audit(days: int = 30):
    """Get user access audit"""
    try:
        audit = governance_hub.get_user_access_audit(days=days)
        return {"user_access": audit}
    except Exception as e:
        logger.error(f"Failed to get user access audit: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/governance/detect-sensitive-columns")
async def detect_sensitive_columns(request: SchemaAnalysisRequest):
    """Detect sensitive columns in a schema"""
    try:
        sensitive = governance_hub.detect_sensitive_columns(request.database, request.schema)
        return {"sensitive_columns": sensitive}
    except Exception as e:
        logger.error(f"Failed to detect sensitive columns: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/governance/masking-policies")
async def get_masking_policies():
    """Get existing masking policies"""
    try:
        policies = governance_hub.get_data_masking_policies()
        return {"masking_policies": policies}
    except Exception as e:
        logger.error(f"Failed to get masking policies: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/governance/failed-logins")
async def get_failed_logins(days: int = 7):
    """Get failed login attempts"""
    try:
        failed = governance_hub.get_failed_login_attempts(days=days)
        return {"failed_logins": failed}
    except Exception as e:
        logger.error(f"Failed to get failed logins: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/governance/compliance-report")
async def get_compliance_report():
    """Get compliance report"""
    try:
        report = governance_hub.generate_compliance_report()
        return report
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/governance/recommendations")
async def get_governance_recommendations():
    """Get governance recommendations"""
    try:
        recommendations = governance_hub.generate_governance_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get governance recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Migration endpoints
@app.post("/api/migration/convert-sql")
async def convert_sql(request: SQLConversionRequest):
    """Convert SQL from source dialect to Snowflake"""
    try:
        conversion = migration_toolkit.convert_sql_dialect(
            request.sql_text, request.source_dialect
        )
        return conversion
    except Exception as e:
        logger.error(f"Failed to convert SQL: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/migration/analyze-schema")
async def analyze_schema(request: SchemaAnalysisRequest):
    """Analyze schema for migration compatibility"""
    try:
        analysis = migration_toolkit.analyze_schema_compatibility(
            request.database, request.schema
        )
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/migration/recommendations")
async def get_migration_recommendations():
    """Get migration recommendations"""
    try:
        recommendations = migration_toolkit.generate_migration_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get migration recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# AI/ML Monitoring endpoints
@app.get("/api/ai-ml/summary")
async def get_ai_ml_summary(days: int = 7):
    """Get AI/ML usage summary"""
    try:
        cortex_summary = ai_ml_monitor.get_cortex_usage_summary(days=days)
        snowpark_ml = ai_ml_monitor.get_snowpark_ml_usage(days=days)
        cost_estimate = ai_ml_monitor.estimate_ai_cost(days=days)

        return {
            "cortex": cortex_summary,
            "snowpark_ml": snowpark_ml,
            "cost_estimate": cost_estimate,
        }
    except Exception as e:
        logger.error(f"Failed to get AI/ML summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/cortex-by-function")
async def get_cortex_by_function(days: int = 7):
    """Get Cortex usage by function"""
    try:
        usage = ai_ml_monitor.get_cortex_usage_by_function(days=days)
        return {"functions": usage}
    except Exception as e:
        logger.error(f"Failed to get Cortex usage by function: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/llm-models")
async def get_llm_model_usage(days: int = 7):
    """Get LLM model usage statistics"""
    try:
        usage = ai_ml_monitor.get_llm_model_usage(days=days)
        return {"models": usage}
    except Exception as e:
        logger.error(f"Failed to get LLM model usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/usage-by-user")
async def get_ai_ml_usage_by_user(days: int = 7):
    """Get AI/ML usage by user"""
    try:
        usage = ai_ml_monitor.get_cortex_usage_by_user(days=days)
        return {"users": usage}
    except Exception as e:
        logger.error(f"Failed to get AI/ML usage by user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/usage-trend")
async def get_ai_ml_usage_trend(days: int = 30):
    """Get AI/ML usage trend over time"""
    try:
        trend = ai_ml_monitor.get_cortex_usage_trend(days=days)
        return {"trend": trend}
    except Exception as e:
        logger.error(f"Failed to get AI/ML usage trend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/expensive-calls")
async def get_expensive_ai_calls(days: int = 7, min_duration_ms: int = 10000):
    """Get expensive AI/ML calls"""
    try:
        calls = ai_ml_monitor.get_expensive_cortex_calls(days=days, min_duration_ms=min_duration_ms)
        return {"expensive_calls": calls}
    except Exception as e:
        logger.error(f"Failed to get expensive AI calls: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/error-rate")
async def get_ai_ml_error_rate(days: int = 7):
    """Get AI/ML error rate statistics"""
    try:
        error_stats = ai_ml_monitor.get_cortex_error_rate(days=days)
        return error_stats
    except Exception as e:
        logger.error(f"Failed to get AI/ML error rate: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/recommendations")
async def get_ai_ml_recommendations():
    """Get AI/ML optimization recommendations"""
    try:
        recommendations = ai_ml_monitor.generate_ai_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Failed to get AI/ML recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/cortex-functions")
async def get_cortex_functions():
    """Get list of available Cortex functions"""
    try:
        functions = ai_ml_monitor.get_cortex_functions_list()
        return {"functions": functions}
    except Exception as e:
        logger.error(f"Failed to get Cortex functions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai-ml/supported-models")
async def get_supported_models():
    """Get list of supported LLM models"""
    try:
        models = ai_ml_monitor.get_supported_models_list()
        return {"models": models}
    except Exception as e:
        logger.error(f"Failed to get supported models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard endpoint
@app.get("/api/dashboard/overview")
async def get_dashboard_overview():
    """Get comprehensive dashboard overview"""
    try:
        overview = {
            "cost_summary": cost_engine.get_cost_summary(days=30),
            "cost_recommendations": cost_engine.generate_warehouse_recommendations()[:5],
            "performance_recommendations": performance_advisor.generate_performance_recommendations()[:5],
            "governance_recommendations": governance_hub.generate_governance_recommendations()[:5],
            "ai_ml_summary": ai_ml_monitor.get_cortex_usage_summary(days=7),
            "ai_ml_cost": ai_ml_monitor.estimate_ai_cost(days=7),
            "ai_ml_recommendations": ai_ml_monitor.generate_ai_recommendations()[:5],
        }
        return overview
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
