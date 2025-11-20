"""
AI-Powered Performance Advisor
Query profiling, optimization recommendations, and automated tuning
"""
from typing import Dict, Any, List
import re
import logging
import sqlparse

logger = logging.getLogger(__name__)


class PerformanceAdvisor:
    """Analyzes and optimizes query performance"""

    def __init__(self, snowflake_manager):
        self.sf_manager = snowflake_manager

    def get_slow_queries(
        self, days: int = 7, min_duration_ms: int = 10000
    ) -> List[Dict[str, Any]]:
        """Identify slow-running queries"""
        try:
            query = f"""
            SELECT
                QUERY_ID,
                QUERY_TEXT,
                USER_NAME,
                WAREHOUSE_NAME,
                WAREHOUSE_SIZE,
                EXECUTION_TIME,
                TOTAL_ELAPSED_TIME,
                ROWS_PRODUCED,
                BYTES_SCANNED,
                PARTITIONS_SCANNED,
                START_TIME
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND TOTAL_ELAPSED_TIME > {min_duration_ms}
            AND EXECUTION_STATUS = 'SUCCESS'
            ORDER BY TOTAL_ELAPSED_TIME DESC
            LIMIT 50
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get slow queries: {str(e)}")
            return []

    def analyze_query(self, query_text: str) -> Dict[str, Any]:
        """Analyze a query and provide optimization recommendations"""
        recommendations = []
        issues = []

        # Parse the query
        parsed = sqlparse.parse(query_text)
        if not parsed:
            return {"recommendations": [], "issues": ["Unable to parse query"]}

        query_upper = query_text.upper()

        # Check for SELECT *
        if re.search(r"SELECT\s+\*", query_upper):
            issues.append("Using SELECT * can retrieve unnecessary columns")
            recommendations.append(
                "Specify only the columns you need instead of using SELECT *"
            )

        # Check for missing WHERE clause
        if "WHERE" not in query_upper and "SELECT" in query_upper:
            issues.append("No WHERE clause detected")
            recommendations.append(
                "Consider adding a WHERE clause to filter data and reduce scan size"
            )

        # Check for DISTINCT
        if "DISTINCT" in query_upper:
            issues.append("DISTINCT can be expensive on large datasets")
            recommendations.append(
                "Verify if DISTINCT is necessary; consider using GROUP BY if appropriate"
            )

        # Check for subqueries
        subquery_count = query_text.count("(SELECT")
        if subquery_count > 2:
            issues.append(f"Multiple subqueries detected ({subquery_count})")
            recommendations.append(
                "Consider using CTEs (WITH clauses) for better readability and potential performance improvement"
            )

        # Check for OR conditions
        if " OR " in query_upper:
            issues.append("OR conditions can prevent index usage")
            recommendations.append(
                "Consider rewriting OR conditions using UNION or IN clauses if possible"
            )

        # Check for LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", query_upper):
            issues.append("LIKE with leading wildcard prevents index usage")
            recommendations.append(
                "Avoid leading wildcards in LIKE patterns when possible"
            )

        # Check for JOINs
        join_count = len(re.findall(r"\bJOIN\b", query_upper))
        if join_count > 5:
            issues.append(f"Multiple JOINs detected ({join_count})")
            recommendations.append(
                "Review JOIN order and consider denormalizing data for frequently accessed patterns"
            )

        # Check for functions on indexed columns
        if re.search(r"WHERE\s+\w+\s*\(", query_upper):
            issues.append("Functions on columns in WHERE clause detected")
            recommendations.append(
                "Avoid using functions on columns in WHERE clause as they prevent index usage"
            )

        return {
            "issues": issues,
            "recommendations": recommendations,
            "complexity_score": len(issues),
            "severity": "HIGH" if len(issues) > 5 else "MEDIUM" if len(issues) > 2 else "LOW",
        }

    def get_query_profile(self, query_id: str) -> Dict[str, Any]:
        """Get detailed profile for a specific query"""
        try:
            query = f"""
            SELECT
                QUERY_ID,
                QUERY_TEXT,
                DATABASE_NAME,
                SCHEMA_NAME,
                WAREHOUSE_NAME,
                WAREHOUSE_SIZE,
                EXECUTION_TIME,
                COMPILATION_TIME,
                TOTAL_ELAPSED_TIME,
                BYTES_SCANNED,
                ROWS_PRODUCED,
                PARTITIONS_SCANNED,
                PARTITIONS_TOTAL,
                CREDITS_USED_CLOUD_SERVICES
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE QUERY_ID = '{query_id}'
            """
            results = self.sf_manager.execute_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Failed to get query profile: {str(e)}")
            return {}

    def suggest_clustering_keys(self, table_name: str, database: str, schema: str) -> List[str]:
        """Suggest potential clustering keys for a table"""
        suggestions = []

        try:
            # Get table columns
            query = f"""
            SELECT
                COLUMN_NAME,
                DATA_TYPE
            FROM {database}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = '{table_name}'
            """
            columns = self.sf_manager.execute_query(query)

            # Suggest date/timestamp columns
            for col in columns:
                col_type = col.get("DATA_TYPE", "").upper()
                col_name = col.get("COLUMN_NAME")

                if "DATE" in col_type or "TIMESTAMP" in col_type:
                    suggestions.append(
                        f"{col_name} (timestamp column - good for time-based queries)"
                    )
                elif col_name and ("ID" in col_name.upper() or "KEY" in col_name.upper()):
                    suggestions.append(f"{col_name} (key column - good for joins)")

        except Exception as e:
            logger.error(f"Failed to suggest clustering keys: {str(e)}")

        return suggestions

    def get_table_statistics(
        self, database: str, schema: str
    ) -> List[Dict[str, Any]]:
        """Get statistics for tables in a schema"""
        try:
            query = f"""
            SELECT
                TABLE_NAME,
                ROW_COUNT,
                BYTES,
                CLUSTERING_KEY,
                AUTO_CLUSTERING_ON
            FROM {database}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY BYTES DESC
            LIMIT 100
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get table statistics: {str(e)}")
            return []

    def generate_performance_recommendations(
        self,
    ) -> List[Dict[str, Any]]:
        """Generate overall performance recommendations"""
        recommendations = []

        try:
            # Get slow queries
            slow_queries = self.get_slow_queries(days=7, min_duration_ms=30000)

            for query_info in slow_queries[:10]:  # Top 10 slow queries
                query_text = query_info.get("QUERY_TEXT", "")
                analysis = self.analyze_query(query_text)

                if analysis["complexity_score"] > 0:
                    recommendations.append(
                        {
                            "type": "QUERY_OPTIMIZATION",
                            "severity": analysis["severity"],
                            "query_id": query_info.get("QUERY_ID"),
                            "execution_time_ms": query_info.get("TOTAL_ELAPSED_TIME"),
                            "issues": analysis["issues"],
                            "recommendations": analysis["recommendations"],
                        }
                    )

            # Add general recommendations
            recommendations.append(
                {
                    "type": "GENERAL",
                    "severity": "INFO",
                    "message": "Enable query result caching to reduce compute costs",
                    "recommendation": "Use SHOW PARAMETERS LIKE 'USE_CACHED_RESULT' to check cache settings",
                }
            )

            recommendations.append(
                {
                    "type": "GENERAL",
                    "severity": "INFO",
                    "message": "Consider using materialized views for frequently accessed aggregations",
                    "recommendation": "Identify repeated aggregation patterns in query history",
                }
            )

        except Exception as e:
            logger.error(f"Failed to generate performance recommendations: {str(e)}")

        return recommendations
