"""
AI & ML Monitoring Module
Track Snowflake Cortex AI models, agents, and credit consumption
"""
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AIMLMonitor:
    """Monitors Snowflake AI/ML features including Cortex models and agents"""

    def __init__(self, snowflake_manager):
        self.sf_manager = snowflake_manager

        # Snowflake Cortex AI functions
        self.cortex_functions = [
            'SNOWFLAKE.CORTEX.COMPLETE',
            'SNOWFLAKE.CORTEX.SENTIMENT',
            'SNOWFLAKE.CORTEX.TRANSLATE',
            'SNOWFLAKE.CORTEX.SUMMARIZE',
            'SNOWFLAKE.CORTEX.EXTRACT_ANSWER',
            'SNOWFLAKE.CORTEX.CLASSIFY_TEXT',
            'SNOWFLAKE.CORTEX.EMBED_TEXT_768',
            'SNOWFLAKE.CORTEX.EMBED_TEXT_1024',
        ]

        # Supported LLM models
        self.llm_models = [
            'snowflake-arctic',
            'llama3-8b',
            'llama3-70b',
            'llama3.1-8b',
            'llama3.1-70b',
            'llama3.1-405b',
            'mistral-large',
            'mistral-large2',
            'mixtral-8x7b',
            'gemma-7b',
            'reka-core',
            'reka-flash',
            'jamba-instruct',
            'jamba-1.5-mini',
            'jamba-1.5-large',
        ]

    def get_cortex_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of Cortex AI usage and credits"""
        try:
            query = f"""
            SELECT
                COUNT(*) as TOTAL_CALLS,
                COUNT(DISTINCT USER_NAME) as UNIQUE_USERS,
                COUNT(DISTINCT DATABASE_NAME) as DATABASES_USED,
                SUM(CREDITS_USED_CLOUD_SERVICES) as TOTAL_CREDITS
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND (
                QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX%'
                OR QUERY_TEXT ILIKE '%COMPLETE(%'
                OR QUERY_TEXT ILIKE '%SENTIMENT(%'
                OR QUERY_TEXT ILIKE '%TRANSLATE(%'
            )
            """
            results = self.sf_manager.execute_query(query)

            if results:
                summary = results[0]
                return {
                    "total_calls": int(summary.get("TOTAL_CALLS", 0)),
                    "unique_users": int(summary.get("UNIQUE_USERS", 0)),
                    "databases_used": int(summary.get("DATABASES_USED", 0)),
                    "total_credits": float(summary.get("TOTAL_CREDITS", 0) or 0),
                    "period_days": days,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Cortex usage summary: {str(e)}")
            return {}

    def get_cortex_usage_by_function(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get usage breakdown by Cortex function"""
        try:
            query = f"""
            WITH cortex_queries AS (
                SELECT
                    QUERY_TEXT,
                    USER_NAME,
                    START_TIME,
                    TOTAL_ELAPSED_TIME,
                    CREDITS_USED_CLOUD_SERVICES,
                    CASE
                        WHEN QUERY_TEXT ILIKE '%COMPLETE(%' THEN 'COMPLETE (LLM)'
                        WHEN QUERY_TEXT ILIKE '%SENTIMENT(%' THEN 'SENTIMENT'
                        WHEN QUERY_TEXT ILIKE '%TRANSLATE(%' THEN 'TRANSLATE'
                        WHEN QUERY_TEXT ILIKE '%SUMMARIZE(%' THEN 'SUMMARIZE'
                        WHEN QUERY_TEXT ILIKE '%EXTRACT_ANSWER(%' THEN 'EXTRACT_ANSWER'
                        WHEN QUERY_TEXT ILIKE '%CLASSIFY_TEXT(%' THEN 'CLASSIFY_TEXT'
                        WHEN QUERY_TEXT ILIKE '%EMBED_TEXT_768(%' THEN 'EMBED_TEXT_768'
                        WHEN QUERY_TEXT ILIKE '%EMBED_TEXT_1024(%' THEN 'EMBED_TEXT_1024'
                        ELSE 'OTHER_CORTEX'
                    END as FUNCTION_NAME
                FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
                WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
                AND QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX%'
            )
            SELECT
                FUNCTION_NAME,
                COUNT(*) as CALL_COUNT,
                AVG(TOTAL_ELAPSED_TIME) as AVG_DURATION_MS,
                SUM(CREDITS_USED_CLOUD_SERVICES) as TOTAL_CREDITS,
                COUNT(DISTINCT USER_NAME) as UNIQUE_USERS
            FROM cortex_queries
            GROUP BY FUNCTION_NAME
            ORDER BY CALL_COUNT DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get Cortex usage by function: {str(e)}")
            return []

    def get_llm_model_usage(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get usage statistics by LLM model"""
        try:
            # Build dynamic CASE statement for all models
            model_cases = []
            for model in self.llm_models:
                model_cases.append(
                    f"WHEN QUERY_TEXT ILIKE '%{model}%' THEN '{model}'"
                )

            query = f"""
            WITH llm_queries AS (
                SELECT
                    QUERY_TEXT,
                    USER_NAME,
                    START_TIME,
                    TOTAL_ELAPSED_TIME,
                    CREDITS_USED_CLOUD_SERVICES,
                    CASE
                        {chr(10).join(model_cases)}
                        ELSE 'UNKNOWN_MODEL'
                    END as MODEL_NAME
                FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
                WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
                AND (
                    QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX.COMPLETE%'
                    OR QUERY_TEXT ILIKE '%COMPLETE(%'
                )
            )
            SELECT
                MODEL_NAME,
                COUNT(*) as TOTAL_CALLS,
                AVG(TOTAL_ELAPSED_TIME) as AVG_DURATION_MS,
                SUM(CREDITS_USED_CLOUD_SERVICES) as TOTAL_CREDITS,
                COUNT(DISTINCT USER_NAME) as UNIQUE_USERS
            FROM llm_queries
            WHERE MODEL_NAME != 'UNKNOWN_MODEL'
            GROUP BY MODEL_NAME
            ORDER BY TOTAL_CALLS DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get LLM model usage: {str(e)}")
            return []

    def get_cortex_usage_by_user(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get Cortex usage breakdown by user"""
        try:
            query = f"""
            SELECT
                USER_NAME,
                COUNT(*) as TOTAL_CALLS,
                SUM(CREDITS_USED_CLOUD_SERVICES) as TOTAL_CREDITS,
                AVG(TOTAL_ELAPSED_TIME) as AVG_DURATION_MS,
                MIN(START_TIME) as FIRST_USE,
                MAX(START_TIME) as LAST_USE
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX%'
            GROUP BY USER_NAME
            ORDER BY TOTAL_CALLS DESC
            LIMIT 50
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get Cortex usage by user: {str(e)}")
            return []

    def get_cortex_usage_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily trend of Cortex usage"""
        try:
            query = f"""
            SELECT
                DATE(START_TIME) as DATE,
                COUNT(*) as DAILY_CALLS,
                SUM(CREDITS_USED_CLOUD_SERVICES) as DAILY_CREDITS,
                COUNT(DISTINCT USER_NAME) as UNIQUE_USERS
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX%'
            GROUP BY DATE
            ORDER BY DATE DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get Cortex usage trend: {str(e)}")
            return []

    def get_expensive_cortex_calls(self, days: int = 7, min_duration_ms: int = 10000) -> List[Dict[str, Any]]:
        """Get expensive/slow Cortex AI calls"""
        try:
            query = f"""
            SELECT
                QUERY_ID,
                USER_NAME,
                START_TIME,
                TOTAL_ELAPSED_TIME,
                CREDITS_USED_CLOUD_SERVICES,
                SUBSTRING(QUERY_TEXT, 1, 200) as QUERY_PREVIEW
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX%'
            AND TOTAL_ELAPSED_TIME > {min_duration_ms}
            ORDER BY TOTAL_ELAPSED_TIME DESC
            LIMIT 100
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get expensive Cortex calls: {str(e)}")
            return []

    def get_cortex_error_rate(self, days: int = 7) -> Dict[str, Any]:
        """Calculate error rate for Cortex calls"""
        try:
            query = f"""
            SELECT
                COUNT(*) as TOTAL_CALLS,
                SUM(CASE WHEN EXECUTION_STATUS = 'SUCCESS' THEN 1 ELSE 0 END) as SUCCESSFUL_CALLS,
                SUM(CASE WHEN EXECUTION_STATUS != 'SUCCESS' THEN 1 ELSE 0 END) as FAILED_CALLS,
                (FAILED_CALLS / NULLIF(TOTAL_CALLS, 0) * 100) as ERROR_RATE_PCT
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND QUERY_TEXT ILIKE '%SNOWFLAKE.CORTEX%'
            """
            results = self.sf_manager.execute_query(query)

            if results:
                stats = results[0]
                return {
                    "total_calls": int(stats.get("TOTAL_CALLS", 0)),
                    "successful_calls": int(stats.get("SUCCESSFUL_CALLS", 0)),
                    "failed_calls": int(stats.get("FAILED_CALLS", 0)),
                    "error_rate_pct": float(stats.get("ERROR_RATE_PCT", 0) or 0),
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Cortex error rate: {str(e)}")
            return {}

    def get_snowpark_ml_usage(self, days: int = 7) -> Dict[str, Any]:
        """Get Snowpark ML and model inference usage"""
        try:
            query = f"""
            SELECT
                COUNT(*) as TOTAL_CALLS,
                SUM(CREDITS_USED_CLOUD_SERVICES) as TOTAL_CREDITS,
                COUNT(DISTINCT USER_NAME) as UNIQUE_USERS
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND (
                QUERY_TEXT ILIKE '%SNOWPARK%ML%'
                OR QUERY_TEXT ILIKE '%MODEL.PREDICT%'
                OR QUERY_TEXT ILIKE '%SYSTEM$PREDICT%'
            )
            """
            results = self.sf_manager.execute_query(query)

            if results:
                summary = results[0]
                return {
                    "total_calls": int(summary.get("TOTAL_CALLS", 0)),
                    "total_credits": float(summary.get("TOTAL_CREDITS", 0) or 0),
                    "unique_users": int(summary.get("UNIQUE_USERS", 0)),
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get Snowpark ML usage: {str(e)}")
            return {}

    def estimate_ai_cost(self, days: int = 7, credit_rate: float = 4.0) -> Dict[str, Any]:
        """Estimate cost for AI/ML features"""
        try:
            cortex_summary = self.get_cortex_usage_summary(days)
            snowpark_ml = self.get_snowpark_ml_usage(days)

            cortex_credits = cortex_summary.get("total_credits", 0)
            snowpark_credits = snowpark_ml.get("total_credits", 0)
            total_credits = cortex_credits + snowpark_credits

            return {
                "cortex_credits": cortex_credits,
                "snowpark_ml_credits": snowpark_credits,
                "total_ai_credits": total_credits,
                "estimated_cost_usd": total_credits * credit_rate,
                "credit_rate_used": credit_rate,
                "period_days": days,
                "breakdown": {
                    "cortex_cost_usd": cortex_credits * credit_rate,
                    "snowpark_ml_cost_usd": snowpark_credits * credit_rate,
                }
            }
        except Exception as e:
            logger.error(f"Failed to estimate AI cost: {str(e)}")
            return {}

    def generate_ai_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for AI/ML optimization"""
        recommendations = []

        try:
            # Check error rate
            error_stats = self.get_cortex_error_rate(days=7)
            if error_stats.get("error_rate_pct", 0) > 5:
                recommendations.append({
                    "type": "HIGH_ERROR_RATE",
                    "severity": "HIGH",
                    "category": "AI_QUALITY",
                    "message": f"Cortex AI error rate is {error_stats['error_rate_pct']:.1f}%",
                    "recommendation": "Review failed queries and implement better error handling",
                    "failed_calls": error_stats.get("failed_calls", 0),
                })

            # Check for expensive calls
            expensive_calls = self.get_expensive_cortex_calls(days=7, min_duration_ms=30000)
            if len(expensive_calls) > 10:
                recommendations.append({
                    "type": "SLOW_AI_CALLS",
                    "severity": "MEDIUM",
                    "category": "AI_PERFORMANCE",
                    "message": f"Found {len(expensive_calls)} slow Cortex AI calls (>30 seconds)",
                    "recommendation": "Consider optimizing prompts, using smaller models, or implementing caching",
                })

            # Check model usage patterns
            model_usage = self.get_llm_model_usage(days=7)
            if model_usage:
                # Check if using expensive models unnecessarily
                large_models = [m for m in model_usage if any(
                    size in m.get("MODEL_NAME", "").lower()
                    for size in ["405b", "70b", "large"]
                )]
                if large_models and len(large_models) > 0:
                    total_large_calls = sum(m.get("TOTAL_CALLS", 0) for m in large_models)
                    recommendations.append({
                        "type": "MODEL_OPTIMIZATION",
                        "severity": "MEDIUM",
                        "category": "AI_COST",
                        "message": f"High usage of large models ({total_large_calls} calls)",
                        "recommendation": "Evaluate if smaller models (8b, 7b) can meet requirements for some use cases",
                    })

            # General best practices
            cortex_summary = self.get_cortex_usage_summary(days=30)
            if cortex_summary.get("total_calls", 0) > 1000:
                recommendations.append({
                    "type": "BEST_PRACTICE",
                    "severity": "INFO",
                    "category": "AI_OPTIMIZATION",
                    "message": "High volume of Cortex AI usage detected",
                    "recommendation": "Consider implementing result caching and batch processing for similar queries",
                })

        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {str(e)}")

        return recommendations

    def get_cortex_functions_list(self) -> List[Dict[str, str]]:
        """Get list of available Cortex functions with descriptions"""
        return [
            {
                "function": "COMPLETE",
                "description": "LLM text completion with various models",
                "use_case": "General purpose text generation, Q&A, summarization",
            },
            {
                "function": "SENTIMENT",
                "description": "Analyze sentiment of text (-1 to 1)",
                "use_case": "Customer feedback analysis, social media monitoring",
            },
            {
                "function": "TRANSLATE",
                "description": "Translate text between languages",
                "use_case": "Multi-language support, content localization",
            },
            {
                "function": "SUMMARIZE",
                "description": "Summarize long text into key points",
                "use_case": "Document summarization, meeting notes",
            },
            {
                "function": "EXTRACT_ANSWER",
                "description": "Extract answers from context",
                "use_case": "Document Q&A, information retrieval",
            },
            {
                "function": "CLASSIFY_TEXT",
                "description": "Classify text into categories",
                "use_case": "Content categorization, ticket routing",
            },
            {
                "function": "EMBED_TEXT_768",
                "description": "Generate 768-dim text embeddings",
                "use_case": "Semantic search, similarity matching",
            },
            {
                "function": "EMBED_TEXT_1024",
                "description": "Generate 1024-dim text embeddings",
                "use_case": "Advanced semantic search, RAG applications",
            },
        ]

    def get_supported_models_list(self) -> List[Dict[str, str]]:
        """Get list of supported LLM models with details"""
        return [
            {
                "model": "snowflake-arctic",
                "provider": "Snowflake",
                "size": "Large",
                "best_for": "General purpose, Snowflake-optimized",
            },
            {
                "model": "llama3.1-405b",
                "provider": "Meta",
                "size": "405B params",
                "best_for": "Complex reasoning, high-quality outputs",
            },
            {
                "model": "llama3.1-70b",
                "provider": "Meta",
                "size": "70B params",
                "best_for": "Balanced performance and cost",
            },
            {
                "model": "llama3.1-8b",
                "provider": "Meta",
                "size": "8B params",
                "best_for": "Fast, cost-effective tasks",
            },
            {
                "model": "mistral-large2",
                "provider": "Mistral AI",
                "size": "Large",
                "best_for": "Multilingual, code generation",
            },
            {
                "model": "mixtral-8x7b",
                "provider": "Mistral AI",
                "size": "8x7B MoE",
                "best_for": "Efficient large model alternative",
            },
            {
                "model": "reka-flash",
                "provider": "Reka",
                "size": "Medium",
                "best_for": "Fast inference, multimodal",
            },
            {
                "model": "jamba-1.5-large",
                "provider": "AI21 Labs",
                "size": "Large",
                "best_for": "Long context windows",
            },
        ]
