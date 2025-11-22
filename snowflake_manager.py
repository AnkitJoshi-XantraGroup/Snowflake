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

    def _normalize_account_identifier(self, account: str) -> str:
        """
        Normalize Snowflake account identifier
        Removes common suffixes that users might include
        """
        account = account.strip()

        # Remove https:// or http:// if present
        account = account.replace("https://", "").replace("http://", "")

        # Remove .snowflakecomputing.com if present
        if ".snowflakecomputing.com" in account:
            account = account.replace(".snowflakecomputing.com", "")

        # Remove trailing slashes
        account = account.rstrip("/")

        logger.info(f"Normalized account identifier: {account}")
        return account

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
        # Normalize the account identifier
        normalized_account = self._normalize_account_identifier(account)

        self.credentials = {
            "account": normalized_account,
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
            logger.info(f"Testing connection to account: {self.credentials['account']}")

            # Build connection parameters
            conn_params = {
                "account": self.credentials["account"],
                "user": self.credentials["user"],
                "password": self.credentials["password"],
                "login_timeout": 60,  # Increase timeout
                "network_timeout": 60,
            }

            # Add optional parameters only if they're provided
            if self.credentials.get("warehouse"):
                conn_params["warehouse"] = self.credentials["warehouse"]
            if self.credentials.get("database"):
                conn_params["database"] = self.credentials["database"]
            if self.credentials.get("schema"):
                conn_params["schema"] = self.credentials["schema"]
            if self.credentials.get("role"):
                conn_params["role"] = self.credentials["role"]

            logger.info(f"Connection parameters: account={conn_params['account']}, user={conn_params['user']}")

            conn = snowflake.connector.connect(**conn_params)

            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]

            # Get additional connection info
            cursor.execute("SELECT CURRENT_ACCOUNT()")
            current_account = cursor.fetchone()[0]

            cursor.execute("SELECT CURRENT_USER()")
            current_user = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            logger.info("Connection test successful")

            return {
                "success": True,
                "message": "Connection successful",
                "version": version,
                "account": current_account,
                "user": current_user,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Connection test failed: {error_msg}")

            # Provide more helpful error messages
            helpful_msg = error_msg
            if "250001" in error_msg:
                helpful_msg = (
                    "Could not connect to Snowflake. Please check:\n"
                    "1. Account identifier format (e.g., 'abc12345' or 'orgname-accountname')\n"
                    "2. Network connectivity (firewall, proxy, VPN)\n"
                    "3. Credentials are correct\n\n"
                    f"Original error: {error_msg}"
                )
            elif "incorrect username or password" in error_msg.lower():
                helpful_msg = "Incorrect username or password. Please verify your credentials."
            elif "does not exist" in error_msg.lower():
                helpful_msg = f"Account identifier may be incorrect. Please verify the format.\n\nOriginal error: {error_msg}"

            return {"success": False, "error": helpful_msg}

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if not self.credentials:
            raise ValueError("Credentials not configured")

        conn = None
        try:
            # Build connection parameters
            conn_params = {
                "account": self.credentials["account"],
                "user": self.credentials["user"],
                "password": self.credentials["password"],
                "login_timeout": 60,
                "network_timeout": 60,
            }

            # Add optional parameters only if they're provided
            if self.credentials.get("warehouse"):
                conn_params["warehouse"] = self.credentials["warehouse"]
            if self.credentials.get("database"):
                conn_params["database"] = self.credentials["database"]
            if self.credentials.get("schema"):
                conn_params["schema"] = self.credentials["schema"]
            if self.credentials.get("role"):
                conn_params["role"] = self.credentials["role"]

            conn = snowflake.connector.connect(**conn_params)
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
