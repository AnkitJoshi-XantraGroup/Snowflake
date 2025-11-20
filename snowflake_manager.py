"""
Snowflake Connection Manager
Handles authentication and connection pooling
"""
import snowflake.connector
from snowflake.connector import DictCursor
from typing import Optional, Dict, Any, List
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SnowflakeManager:
    """Manages Snowflake connections and queries"""

    def __init__(self):
        self.connection = None
        self.credentials: Optional[Dict[str, str]] = None

    def set_credentials(
        self,
        account: str,
        user: str,
        password: str,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None,
    ):
        """Store Snowflake credentials"""
        self.credentials = {
            "account": account,
            "user": user,
            "password": password,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "role": role,
        }

    def test_connection(self) -> Dict[str, Any]:
        """Test Snowflake connection with stored credentials"""
        if not self.credentials:
            return {"success": False, "error": "No credentials configured"}

        try:
            conn = snowflake.connector.connect(
                account=self.credentials["account"],
                user=self.credentials["user"],
                password=self.credentials["password"],
                warehouse=self.credentials.get("warehouse"),
                database=self.credentials.get("database"),
                schema=self.credentials.get("schema"),
                role=self.credentials.get("role"),
            )

            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            return {
                "success": True,
                "message": "Connection successful",
                "version": version,
            }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {"success": False, "error": str(e)}

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if not self.credentials:
            raise ValueError("Credentials not configured")

        conn = None
        try:
            conn = snowflake.connector.connect(
                account=self.credentials["account"],
                user=self.credentials["user"],
                password=self.credentials["password"],
                warehouse=self.credentials.get("warehouse"),
                database=self.credentials.get("database"),
                schema=self.credentials.get("schema"),
                role=self.credentials.get("role"),
            )
            yield conn
        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(DictCursor)
                cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                return results
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def get_warehouses(self) -> List[Dict[str, Any]]:
        """Get list of all warehouses"""
        query = "SHOW WAREHOUSES"
        return self.execute_query(query)

    def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of all databases"""
        query = "SHOW DATABASES"
        return self.execute_query(query)

    def get_schemas(self, database: str) -> List[Dict[str, Any]]:
        """Get list of schemas in a database"""
        query = f"SHOW SCHEMAS IN DATABASE {database}"
        return self.execute_query(query)


# Global instance
snowflake_manager = SnowflakeManager()
