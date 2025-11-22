"""
Query Explorer with Best Practices Analyzer
Detailed query profiling and Snowflake best practice recommendations
"""
from typing import Dict, Any, List
import re
import logging
import sqlparse

logger = logging.getLogger(__name__)


class QueryExplorer:
    """Explores queries with detailed profiling and best practice recommendations"""

    def __init__(self, snowflake_manager):
        self.sf_manager = snowflake_manager

    def get_all_queries(
        self,
        days: int = 7,
        limit: int = 100,
        execution_status: str = None,
        user_filter: str = None,
        warehouse_filter: str = None
    ) -> List[Dict[str, Any]]:
        """Get list of all queries with optional filters"""
        try:
            filters = [f"START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())"]

            if execution_status:
                filters.append(f"EXECUTION_STATUS = '{execution_status}'")
            if user_filter:
                filters.append(f"USER_NAME ILIKE '%{user_filter}%'")
            if warehouse_filter:
                filters.append(f"WAREHOUSE_NAME ILIKE '%{warehouse_filter}%'")

            where_clause = " AND ".join(filters)

            query = f"""
            SELECT
                QUERY_ID,
                QUERY_TEXT,
                USER_NAME,
                WAREHOUSE_NAME,
                WAREHOUSE_SIZE,
                DATABASE_NAME,
                SCHEMA_NAME,
                EXECUTION_STATUS,
                ERROR_CODE,
                ERROR_MESSAGE,
                START_TIME,
                END_TIME,
                TOTAL_ELAPSED_TIME,
                EXECUTION_TIME,
                COMPILATION_TIME,
                QUEUED_PROVISIONING_TIME,
                QUEUED_REPAIR_TIME,
                QUEUED_OVERLOAD_TIME,
                BYTES_SCANNED,
                ROWS_PRODUCED,
                ROWS_INSERTED,
                ROWS_UPDATED,
                ROWS_DELETED,
                PARTITIONS_SCANNED,
                PARTITIONS_TOTAL,
                BYTES_WRITTEN,
                BYTES_WRITTEN_TO_RESULT,
                BYTES_READ_FROM_RESULT,
                CREDITS_USED_CLOUD_SERVICES,
                QUERY_TYPE
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE {where_clause}
            ORDER BY START_TIME DESC
            LIMIT {limit}
            """

            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get all queries: {str(e)}")
            return []

    def get_query_detailed_profile(self, query_id: str) -> Dict[str, Any]:
        """Get comprehensive profile for a specific query"""
        try:
            query = f"""
            SELECT
                QUERY_ID,
                QUERY_TEXT,
                USER_NAME,
                ROLE_NAME,
                WAREHOUSE_NAME,
                WAREHOUSE_SIZE,
                WAREHOUSE_TYPE,
                DATABASE_NAME,
                SCHEMA_NAME,
                EXECUTION_STATUS,
                ERROR_CODE,
                ERROR_MESSAGE,
                START_TIME,
                END_TIME,
                TOTAL_ELAPSED_TIME,
                EXECUTION_TIME,
                COMPILATION_TIME,
                QUEUED_PROVISIONING_TIME,
                QUEUED_REPAIR_TIME,
                QUEUED_OVERLOAD_TIME,
                TRANSACTION_BLOCKED_TIME,
                BYTES_SCANNED,
                PERCENTAGE_SCANNED_FROM_CACHE,
                BYTES_WRITTEN,
                BYTES_WRITTEN_TO_RESULT,
                BYTES_READ_FROM_RESULT,
                ROWS_PRODUCED,
                ROWS_INSERTED,
                ROWS_UPDATED,
                ROWS_DELETED,
                ROWS_UNLOADED,
                BYTES_DELETED,
                PARTITIONS_SCANNED,
                PARTITIONS_TOTAL,
                BYTES_SPILLED_TO_LOCAL_STORAGE,
                BYTES_SPILLED_TO_REMOTE_STORAGE,
                BYTES_SENT_OVER_THE_NETWORK,
                QUERY_LOAD_PERCENT,
                IS_CLIENT_GENERATED_STATEMENT,
                QUERY_ACCELERATION_BYTES_SCANNED,
                QUERY_ACCELERATION_PARTITIONS_SCANNED,
                QUERY_ACCELERATION_UPPER_LIMIT_SCALE_FACTOR,
                TRANSACTION_ID,
                SESSION_ID,
                CREDITS_USED_CLOUD_SERVICES,
                RELEASE_VERSION,
                EXTERNAL_FUNCTION_TOTAL_INVOCATIONS,
                EXTERNAL_FUNCTION_TOTAL_SENT_ROWS,
                EXTERNAL_FUNCTION_TOTAL_RECEIVED_ROWS,
                EXTERNAL_FUNCTION_TOTAL_SENT_BYTES,
                EXTERNAL_FUNCTION_TOTAL_RECEIVED_BYTES,
                QUERY_TAG,
                QUERY_TYPE,
                CLUSTER_NUMBER,
                QUERY_HASH,
                QUERY_HASH_VERSION,
                QUERY_PARAMETERIZED_HASH,
                QUERY_PARAMETERIZED_HASH_VERSION
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE QUERY_ID = '{query_id}'
            """

            results = self.sf_manager.execute_query(query)
            return results[0] if results else {}
        except Exception as e:
            logger.error(f"Failed to get query detailed profile: {str(e)}")
            return {}

    def analyze_query_with_best_practices(self, query_id: str) -> Dict[str, Any]:
        """Analyze query against Snowflake best practices"""
        profile = self.get_query_detailed_profile(query_id)

        if not profile:
            return {"error": "Query not found"}

        recommendations = []
        warnings = []
        successes = []
        metrics = {}

        # Extract key metrics
        total_time = profile.get("TOTAL_ELAPSED_TIME", 0) or 0
        execution_time = profile.get("EXECUTION_TIME", 0) or 0
        compilation_time = profile.get("COMPILATION_TIME", 0) or 0
        bytes_scanned = profile.get("BYTES_SCANNED", 0) or 0
        cache_percentage = profile.get("PERCENTAGE_SCANNED_FROM_CACHE", 0) or 0
        partitions_scanned = profile.get("PARTITIONS_SCANNED", 0) or 0
        partitions_total = profile.get("PARTITIONS_TOTAL", 0) or 0
        bytes_spilled_local = profile.get("BYTES_SPILLED_TO_LOCAL_STORAGE", 0) or 0
        bytes_spilled_remote = profile.get("BYTES_SPILLED_TO_REMOTE_STORAGE", 0) or 0
        query_text = profile.get("QUERY_TEXT", "")

        # Calculate partition efficiency
        partition_efficiency = 0
        if partitions_total > 0:
            partition_efficiency = (partitions_scanned / partitions_total) * 100

        # Best Practice 1: Result Caching
        if cache_percentage > 80:
            successes.append({
                "practice": "Result Caching",
                "message": f"Excellent cache utilization: {cache_percentage:.1f}% from cache",
                "impact": "HIGH"
            })
        elif cache_percentage > 0:
            recommendations.append({
                "practice": "Result Caching",
                "severity": "INFO",
                "message": f"Moderate cache usage: {cache_percentage:.1f}% from cache",
                "suggestion": "Similar queries can benefit from result caching. Consider using RESULT_SCAN() for repeated patterns.",
                "impact": "MEDIUM"
            })
        else:
            recommendations.append({
                "practice": "Result Caching",
                "severity": "LOW",
                "message": "No cache utilization detected",
                "suggestion": "Enable result caching with USE_CACHED_RESULT = TRUE or use RESULT_SCAN() for repeated queries.",
                "impact": "MEDIUM"
            })

        # Best Practice 2: Partition Pruning
        if partitions_total > 0:
            if partition_efficiency < 10:
                successes.append({
                    "practice": "Partition Pruning",
                    "message": f"Excellent partition pruning: Only {partition_efficiency:.1f}% of partitions scanned",
                    "details": f"{partitions_scanned} out of {partitions_total} partitions",
                    "impact": "HIGH"
                })
            elif partition_efficiency < 30:
                recommendations.append({
                    "practice": "Partition Pruning",
                    "severity": "INFO",
                    "message": f"Good partition pruning: {partition_efficiency:.1f}% of partitions scanned",
                    "suggestion": "Consider adding more specific filters to reduce partition scanning further.",
                    "impact": "MEDIUM"
                })
            else:
                recommendations.append({
                    "practice": "Partition Pruning",
                    "severity": "HIGH",
                    "message": f"Poor partition pruning: {partition_efficiency:.1f}% of partitions scanned",
                    "suggestion": "Add clustering keys on frequently filtered columns or use more selective WHERE clauses.",
                    "impact": "HIGH",
                    "details": f"Scanned {partitions_scanned} out of {partitions_total} partitions"
                })

        # Best Practice 3: Data Spillage
        if bytes_spilled_remote > 0:
            gb_spilled = bytes_spilled_remote / (1024**3)
            warnings.append({
                "practice": "Memory Management",
                "severity": "CRITICAL",
                "message": f"Remote storage spillage detected: {gb_spilled:.2f} GB",
                "suggestion": "Use a larger warehouse size or optimize query to reduce memory usage. Remote spillage significantly impacts performance.",
                "impact": "CRITICAL"
            })
        elif bytes_spilled_local > 0:
            gb_spilled = bytes_spilled_local / (1024**3)
            recommendations.append({
                "practice": "Memory Management",
                "severity": "MEDIUM",
                "message": f"Local storage spillage: {gb_spilled:.2f} GB",
                "suggestion": "Consider using a larger warehouse or optimizing the query to fit in memory.",
                "impact": "MEDIUM"
            })
        else:
            successes.append({
                "practice": "Memory Management",
                "message": "No data spillage - query fits in memory",
                "impact": "HIGH"
            })

        # Best Practice 4: Compilation Time
        if total_time > 0:
            compilation_ratio = (compilation_time / total_time) * 100
            if compilation_ratio > 20:
                recommendations.append({
                    "practice": "Query Compilation",
                    "severity": "MEDIUM",
                    "message": f"High compilation time: {compilation_ratio:.1f}% of total time",
                    "suggestion": "Consider using prepared statements or simplifying complex queries. High compilation time may indicate overly complex SQL.",
                    "impact": "MEDIUM"
                })

        # Best Practice 5: Query Complexity Analysis
        query_analysis = self._analyze_query_text(query_text)
        recommendations.extend(query_analysis)

        # Best Practice 6: Data Volume
        if bytes_scanned > 10 * 1024**3:  # > 10 GB
            gb_scanned = bytes_scanned / (1024**3)
            recommendations.append({
                "practice": "Data Volume",
                "severity": "MEDIUM",
                "message": f"Large data scan: {gb_scanned:.2f} GB scanned",
                "suggestion": "Consider adding filters, using clustering keys, or creating materialized views for frequently accessed aggregations.",
                "impact": "HIGH"
            })

        # Best Practice 7: Warehouse Sizing
        warehouse_size = profile.get("WAREHOUSE_SIZE")
        if execution_time > 60000 and warehouse_size in ["X-SMALL", "SMALL"]:  # > 1 minute
            recommendations.append({
                "practice": "Warehouse Sizing",
                "severity": "MEDIUM",
                "message": f"Long execution time ({execution_time/1000:.1f}s) on {warehouse_size} warehouse",
                "suggestion": "Consider using a larger warehouse for better performance. Larger warehouses provide more compute resources.",
                "impact": "HIGH"
            })

        # Metrics Summary
        metrics = {
            "total_elapsed_time_seconds": total_time / 1000 if total_time else 0,
            "execution_time_seconds": execution_time / 1000 if execution_time else 0,
            "compilation_time_seconds": compilation_time / 1000 if compilation_time else 0,
            "cache_percentage": cache_percentage,
            "partition_efficiency": partition_efficiency,
            "bytes_scanned_gb": bytes_scanned / (1024**3) if bytes_scanned else 0,
            "bytes_spilled_local_gb": bytes_spilled_local / (1024**3) if bytes_spilled_local else 0,
            "bytes_spilled_remote_gb": bytes_spilled_remote / (1024**3) if bytes_spilled_remote else 0,
            "warehouse_size": warehouse_size,
            "rows_produced": profile.get("ROWS_PRODUCED", 0),
        }

        # Calculate overall score
        score = self._calculate_performance_score(
            cache_percentage,
            partition_efficiency,
            bytes_spilled_local,
            bytes_spilled_remote,
            compilation_ratio if total_time > 0 else 0
        )

        return {
            "query_id": query_id,
            "query_text": query_text[:500],  # First 500 chars
            "profile": profile,
            "metrics": metrics,
            "recommendations": recommendations,
            "warnings": warnings,
            "successes": successes,
            "performance_score": score,
            "status": profile.get("EXECUTION_STATUS"),
        }

    def _analyze_query_text(self, query_text: str) -> List[Dict[str, Any]]:
        """Analyze query text for best practices"""
        recommendations = []

        if not query_text:
            return recommendations

        query_upper = query_text.upper()

        # Check for SELECT *
        if re.search(r'SELECT\s+\*', query_upper):
            recommendations.append({
                "practice": "Column Selection",
                "severity": "MEDIUM",
                "message": "SELECT * detected",
                "suggestion": "Explicitly list required columns instead of using SELECT * to reduce data transfer and improve performance.",
                "impact": "MEDIUM"
            })

        # Check for missing WHERE clause in SELECT
        if 'SELECT' in query_upper and 'WHERE' not in query_upper and 'LIMIT' not in query_upper:
            if 'FROM' in query_upper:
                recommendations.append({
                    "practice": "Data Filtering",
                    "severity": "HIGH",
                    "message": "No WHERE clause or LIMIT detected",
                    "suggestion": "Add WHERE clause to filter data and reduce full table scans. Use LIMIT for exploratory queries.",
                    "impact": "HIGH"
                })

        # Check for DISTINCT
        if 'DISTINCT' in query_upper:
            recommendations.append({
                "practice": "Query Optimization",
                "severity": "INFO",
                "message": "DISTINCT keyword detected",
                "suggestion": "DISTINCT can be expensive on large datasets. Consider if GROUP BY would be more appropriate or if duplicates can be eliminated earlier in the pipeline.",
                "impact": "MEDIUM"
            })

        # Check for subqueries
        subquery_count = query_text.count('(SELECT')
        if subquery_count > 2:
            recommendations.append({
                "practice": "Query Structure",
                "severity": "MEDIUM",
                "message": f"Multiple subqueries detected ({subquery_count})",
                "suggestion": "Consider using CTEs (WITH clauses) for better readability and potential performance improvements.",
                "impact": "MEDIUM"
            })

        # Check for LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", query_upper):
            recommendations.append({
                "practice": "String Matching",
                "severity": "MEDIUM",
                "message": "LIKE with leading wildcard detected",
                "suggestion": "Leading wildcards prevent index usage. Consider full-text search or alternative patterns if possible.",
                "impact": "MEDIUM"
            })

        # Check for UNION vs UNION ALL
        if 'UNION ' in query_text and 'UNION ALL' not in query_upper:
            recommendations.append({
                "practice": "Set Operations",
                "severity": "LOW",
                "message": "UNION detected (implicit DISTINCT)",
                "suggestion": "Use UNION ALL if duplicates don't matter - it's faster as it skips the DISTINCT operation.",
                "impact": "LOW"
            })

        # Check for ORDER BY without LIMIT
        if 'ORDER BY' in query_upper and 'LIMIT' not in query_upper:
            recommendations.append({
                "practice": "Result Ordering",
                "severity": "LOW",
                "message": "ORDER BY without LIMIT",
                "suggestion": "If you don't need all rows sorted, add LIMIT to reduce sorting overhead.",
                "impact": "LOW"
            })

        return recommendations

    def _calculate_performance_score(
        self,
        cache_percentage: float,
        partition_efficiency: float,
        bytes_spilled_local: int,
        bytes_spilled_remote: int,
        compilation_ratio: float
    ) -> int:
        """Calculate overall performance score (0-100)"""
        score = 100

        # Cache utilization (up to -20 points)
        if cache_percentage == 0:
            score -= 10
        elif cache_percentage < 50:
            score -= 5

        # Partition efficiency (up to -25 points)
        if partition_efficiency > 50:
            score -= 25
        elif partition_efficiency > 30:
            score -= 15
        elif partition_efficiency > 10:
            score -= 5

        # Spillage (up to -30 points)
        if bytes_spilled_remote > 0:
            score -= 30
        elif bytes_spilled_local > 0:
            score -= 10

        # Compilation ratio (up to -15 points)
        if compilation_ratio > 30:
            score -= 15
        elif compilation_ratio > 20:
            score -= 10
        elif compilation_ratio > 10:
            score -= 5

        return max(0, score)

    def get_query_execution_plan(self, query_text: str) -> str:
        """Get EXPLAIN plan for a query"""
        try:
            # Clean and prepare query
            query_text = query_text.strip()
            if query_text.endswith(';'):
                query_text = query_text[:-1]

            explain_query = f"EXPLAIN {query_text}"
            results = self.sf_manager.execute_query(explain_query)

            # Format execution plan
            plan_lines = []
            for row in results:
                plan_lines.append(str(row))

            return "\n".join(plan_lines)
        except Exception as e:
            logger.error(f"Failed to get execution plan: {str(e)}")
            return f"Unable to generate execution plan: {str(e)}"

    def compare_queries(self, query_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple queries side by side"""
        comparisons = []

        for query_id in query_ids[:5]:  # Limit to 5 queries
            profile = self.get_query_detailed_profile(query_id)
            if profile:
                comparisons.append({
                    "query_id": query_id,
                    "execution_time": profile.get("EXECUTION_TIME", 0),
                    "bytes_scanned": profile.get("BYTES_SCANNED", 0),
                    "rows_produced": profile.get("ROWS_PRODUCED", 0),
                    "cache_percentage": profile.get("PERCENTAGE_SCANNED_FROM_CACHE", 0),
                    "warehouse_size": profile.get("WAREHOUSE_SIZE"),
                })

        return {"comparisons": comparisons}
