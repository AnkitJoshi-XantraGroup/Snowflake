"""
Governance & Security Hub
Role-based access control, data masking, sensitive data detection, and compliance
"""
from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)


class GovernanceSecurityHub:
    """Manages governance, security, and compliance"""

    def __init__(self, snowflake_manager):
        self.sf_manager = snowflake_manager

        # Patterns for sensitive data detection
        self.sensitive_patterns = {
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
            "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "CREDIT_CARD": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "IP_ADDRESS": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        }

        # Keywords indicating sensitive columns
        self.sensitive_column_keywords = [
            "SSN",
            "SOCIAL_SECURITY",
            "PASSWORD",
            "CREDIT_CARD",
            "CCN",
            "EMAIL",
            "PHONE",
            "SALARY",
            "DOB",
            "DATE_OF_BIRTH",
            "PASSPORT",
            "LICENSE",
        ]

    def get_user_access_audit(self, days: int = 30) -> List[Dict[str, Any]]:
        """Audit user access patterns"""
        try:
            query = f"""
            SELECT
                USER_NAME,
                COUNT(DISTINCT DATABASE_NAME) as DATABASES_ACCESSED,
                COUNT(DISTINCT SCHEMA_NAME) as SCHEMAS_ACCESSED,
                COUNT(*) as QUERY_COUNT,
                MAX(START_TIME) as LAST_ACCESS
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            GROUP BY USER_NAME
            ORDER BY QUERY_COUNT DESC
            LIMIT 100
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get user access audit: {str(e)}")
            return []

    def get_role_hierarchy(self) -> List[Dict[str, Any]]:
        """Get role hierarchy and grants"""
        try:
            query = """
            SELECT
                GRANTEE_NAME as ROLE,
                NAME as GRANTED_ROLE,
                GRANTED_ON,
                GRANTED_BY
            FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
            WHERE DELETED_ON IS NULL
            ORDER BY GRANTEE_NAME
            LIMIT 500
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get role hierarchy: {str(e)}")
            return []

    def detect_sensitive_columns(
        self, database: str, schema: str
    ) -> List[Dict[str, Any]]:
        """Detect potentially sensitive columns based on naming patterns"""
        sensitive_columns = []

        try:
            query = f"""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM {database}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            """
            columns = self.sf_manager.execute_query(query)

            for col in columns:
                col_name = col.get("COLUMN_NAME", "").upper()
                table_name = col.get("TABLE_NAME")
                data_type = col.get("DATA_TYPE")

                # Check if column name contains sensitive keywords
                for keyword in self.sensitive_column_keywords:
                    if keyword in col_name:
                        sensitive_columns.append(
                            {
                                "table": table_name,
                                "column": col.get("COLUMN_NAME"),
                                "data_type": data_type,
                                "classification": keyword,
                                "recommendation": "Consider applying data masking or encryption",
                            }
                        )
                        break

        except Exception as e:
            logger.error(f"Failed to detect sensitive columns: {str(e)}")

        return sensitive_columns

    def get_data_masking_policies(self) -> List[Dict[str, Any]]:
        """Get existing masking policies"""
        try:
            query = """
            SELECT
                POLICY_NAME,
                POLICY_SCHEMA,
                POLICY_KIND,
                POLICY_OWNER,
                CREATED
            FROM SNOWFLAKE.ACCOUNT_USAGE.MASKING_POLICIES
            WHERE DELETED IS NULL
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get masking policies: {str(e)}")
            return []

    def generate_masking_policy_template(
        self, column_type: str, policy_name: str
    ) -> str:
        """Generate a template for a masking policy"""
        templates = {
            "EMAIL": f"""
CREATE MASKING POLICY {policy_name} AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ADMIN', 'SECURITY_ADMIN') THEN val
    ELSE CONCAT(LEFT(val, 2), '***@', SPLIT_PART(val, '@', -1))
  END;
            """,
            "SSN": f"""
CREATE MASKING POLICY {policy_name} AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ADMIN', 'SECURITY_ADMIN') THEN val
    ELSE 'XXX-XX-' || RIGHT(val, 4)
  END;
            """,
            "CREDIT_CARD": f"""
CREATE MASKING POLICY {policy_name} AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ADMIN', 'SECURITY_ADMIN') THEN val
    ELSE 'XXXX-XXXX-XXXX-' || RIGHT(val, 4)
  END;
            """,
            "PHONE": f"""
CREATE MASKING POLICY {policy_name} AS (val STRING) RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ADMIN', 'SECURITY_ADMIN') THEN val
    ELSE 'XXX-XXX-' || RIGHT(val, 4)
  END;
            """,
        }

        return templates.get(column_type, f"-- No template available for {column_type}")

    def get_failed_login_attempts(self, days: int = 7) -> List[Dict[str, Any]]:
        """Detect potential security threats from failed logins"""
        try:
            query = f"""
            SELECT
                USER_NAME,
                CLIENT_IP,
                COUNT(*) as FAILED_ATTEMPTS,
                MAX(EVENT_TIMESTAMP) as LAST_ATTEMPT
            FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
            WHERE EVENT_TIMESTAMP >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
            AND IS_SUCCESS = 'NO'
            GROUP BY USER_NAME, CLIENT_IP
            HAVING COUNT(*) > 5
            ORDER BY FAILED_ATTEMPTS DESC
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get failed login attempts: {str(e)}")
            return []

    def get_privilege_grants(self, role_name: str = None) -> List[Dict[str, Any]]:
        """Get privilege grants for a role or all roles"""
        try:
            role_filter = f"AND GRANTEE_NAME = '{role_name}'" if role_name else ""

            query = f"""
            SELECT
                CREATED_ON,
                PRIVILEGE,
                GRANTED_ON,
                NAME as OBJECT_NAME,
                GRANTEE_NAME as ROLE,
                GRANTED_BY
            FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
            WHERE DELETED_ON IS NULL
            {role_filter}
            ORDER BY CREATED_ON DESC
            LIMIT 500
            """
            return self.sf_manager.execute_query(query)
        except Exception as e:
            logger.error(f"Failed to get privilege grants: {str(e)}")
            return []

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate a compliance dashboard report"""
        report = {
            "timestamp": str(datetime.now()),
            "sections": {},
        }

        try:
            # Security incidents (failed logins)
            failed_logins = self.get_failed_login_attempts(days=7)
            report["sections"]["security_incidents"] = {
                "failed_login_count": len(failed_logins),
                "high_risk_ips": [
                    f["CLIENT_IP"]
                    for f in failed_logins[:5]
                    if f.get("FAILED_ATTEMPTS", 0) > 10
                ],
                "status": "CRITICAL" if len(failed_logins) > 10 else "OK",
            }

            # Data masking compliance
            masking_policies = self.get_data_masking_policies()
            report["sections"]["data_protection"] = {
                "masking_policies_count": len(masking_policies),
                "status": "OK" if len(masking_policies) > 0 else "NEEDS_ATTENTION",
                "recommendation": "Consider implementing masking policies for sensitive data"
                if len(masking_policies) == 0
                else "Review and update masking policies regularly",
            }

            # Access control
            user_audit = self.get_user_access_audit(days=30)
            report["sections"]["access_control"] = {
                "active_users_count": len(user_audit),
                "status": "OK",
                "recommendation": "Regular access review recommended",
            }

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {str(e)}")
            report["error"] = str(e)

        return report

    def generate_governance_recommendations(
        self,
    ) -> List[Dict[str, Any]]:
        """Generate governance and security recommendations"""
        recommendations = []

        try:
            # Check for failed logins
            failed_logins = self.get_failed_login_attempts(days=7)
            if failed_logins:
                for login in failed_logins[:5]:
                    if login.get("FAILED_ATTEMPTS", 0) > 10:
                        recommendations.append(
                            {
                                "type": "SECURITY_THREAT",
                                "severity": "CRITICAL",
                                "user": login.get("USER_NAME"),
                                "ip": login.get("CLIENT_IP"),
                                "failed_attempts": login.get("FAILED_ATTEMPTS"),
                                "message": "Multiple failed login attempts detected",
                                "recommendation": "Investigate and consider blocking IP or user",
                            }
                        )

            # Check for masking policies
            masking_policies = self.get_data_masking_policies()
            if len(masking_policies) == 0:
                recommendations.append(
                    {
                        "type": "DATA_PROTECTION",
                        "severity": "HIGH",
                        "message": "No data masking policies detected",
                        "recommendation": "Implement masking policies for sensitive data columns",
                    }
                )

        except Exception as e:
            logger.error(f"Failed to generate governance recommendations: {str(e)}")

        return recommendations


from datetime import datetime
