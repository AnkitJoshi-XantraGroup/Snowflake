"""
Cost Intelligence Engine
Real-time monitoring, predictive alerts, and automated warehouse right-sizing
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CostIntelligenceEngine:
    """Monitors and optimizes Snowflake costs"""

    def __init__(self, snowflake_manager):
        self.sf_manager = snowflake_manager

    def get_warehouse_metering_history(
        self, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get warehouse usage and cost metrics"""
        try:
            query = f"""
            SELECT
                WAREHOUSE_NAME,
                START_TIME,
                END_TIME,
                CREDITS_USED,
                CREDITS_USED_COMPUTE,
                CREDITS_USED_CLOUD_SERVICES
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            ORDER BY START_TIME DESC
            LIMIT 1000
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get warehouse metering: {str(e)}")
            return []

    def get_query_costs(self, days: int = 7) -> List[Dict[str, Any]]:
        """Analyze cost per query"""
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
                CREDITS_USED_CLOUD_SERVICES,
                START_TIME
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND EXECUTION_STATUS = 'SUCCESS'
            ORDER BY TOTAL_ELAPSED_TIME DESC
            LIMIT 100
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get query costs: {str(e)}")
            return []

    def detect_idle_warehouses(
        self, idle_threshold_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Identify warehouses that have been idle"""
        try:
            query = f"""
            SELECT
                WAREHOUSE_NAME,
                MAX(END_TIME) as LAST_USED,
                DATEDIFF('minute', MAX(END_TIME), CURRENT_TIMESTAMP()) as IDLE_MINUTES
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
            GROUP BY WAREHOUSE_NAME
            HAVING IDLE_MINUTES > {idle_threshold_minutes}
            ORDER BY IDLE_MINUTES DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to detect idle warehouses: {str(e)}")
            return []

    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get overall cost summary"""
        try:
            query = f"""
            SELECT
                SUM(CREDITS_USED) as TOTAL_CREDITS,
                SUM(CREDITS_USED_COMPUTE) as COMPUTE_CREDITS,
                SUM(CREDITS_USED_CLOUD_SERVICES) as CLOUD_SERVICE_CREDITS,
                COUNT(DISTINCT WAREHOUSE_NAME) as WAREHOUSE_COUNT
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            """
            results = self.sf_manager.execute_query(query)

            if results:
                summary = results[0]
                # Estimate cost (assuming $4 per credit - adjust based on actual rate)
                credit_rate = 4.0
                return {
                    "total_credits": float(summary.get("TOTAL_CREDITS", 0)),
                    "compute_credits": float(summary.get("COMPUTE_CREDITS", 0)),
                    "cloud_service_credits": float(
                        summary.get("CLOUD_SERVICE_CREDITS", 0)
                    ),
                    "warehouse_count": int(summary.get("WAREHOUSE_COUNT", 0)),
                    "estimated_cost_usd": float(summary.get("TOTAL_CREDITS", 0))
                    * credit_rate,
                    "period_days": days,
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to get cost summary: {str(e)}")
            return {}

    def get_cost_by_warehouse(self, days: int = 7) -> List[Dict[str, Any]]:
        """Break down costs by warehouse"""
        try:
            query = f"""
            SELECT
                WAREHOUSE_NAME,
                SUM(CREDITS_USED) as TOTAL_CREDITS,
                COUNT(*) as EXECUTION_COUNT,
                AVG(CREDITS_USED) as AVG_CREDITS_PER_HOUR
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            GROUP BY WAREHOUSE_NAME
            ORDER BY TOTAL_CREDITS DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get cost by warehouse: {str(e)}")
            return []

    def get_cost_anomalies(
        self, threshold_percentage: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Detect unusual cost spikes"""
        try:
            query = f"""
            WITH daily_costs AS (
                SELECT
                    DATE(START_TIME) as DATE,
                    SUM(CREDITS_USED) as DAILY_CREDITS
                FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
                WHERE START_TIME >= DATEADD(day, -30, CURRENT_TIMESTAMP())
                GROUP BY DATE
            ),
            avg_costs AS (
                SELECT AVG(DAILY_CREDITS) as AVG_DAILY_CREDITS
                FROM daily_costs
            )
            SELECT
                dc.DATE,
                dc.DAILY_CREDITS,
                ac.AVG_DAILY_CREDITS,
                ((dc.DAILY_CREDITS - ac.AVG_DAILY_CREDITS) / ac.AVG_DAILY_CREDITS * 100) as PERCENT_CHANGE
            FROM daily_costs dc
            CROSS JOIN avg_costs ac
            WHERE ((dc.DAILY_CREDITS - ac.AVG_DAILY_CREDITS) / ac.AVG_DAILY_CREDITS * 100) > {threshold_percentage}
            ORDER BY dc.DATE DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to detect cost anomalies: {str(e)}")
            return []

    def generate_warehouse_recommendations(
        self,
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for warehouse optimization"""
        recommendations = []

        try:
            # Check for idle warehouses
            idle_warehouses = self.detect_idle_warehouses(idle_threshold_minutes=30)
            for wh in idle_warehouses:
                recommendations.append(
                    {
                        "type": "IDLE_WAREHOUSE",
                        "severity": "HIGH",
                        "warehouse": wh.get("WAREHOUSE_NAME"),
                        "message": f"Warehouse has been idle for {wh.get('IDLE_MINUTES')} minutes. Consider suspending or reducing auto-suspend time.",
                        "potential_savings": "Medium-High",
                    }
                )

            # Check for cost anomalies
            anomalies = self.get_cost_anomalies(threshold_percentage=30)
            for anomaly in anomalies[:5]:  # Top 5 anomalies
                recommendations.append(
                    {
                        "type": "COST_SPIKE",
                        "severity": "CRITICAL",
                        "date": str(anomaly.get("DATE")),
                        "message": f"Cost spike detected: {anomaly.get('PERCENT_CHANGE', 0):.1f}% above average",
                        "credits_used": float(anomaly.get("DAILY_CREDITS", 0)),
                        "potential_savings": "High",
                    }
                )

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")

        return recommendations
