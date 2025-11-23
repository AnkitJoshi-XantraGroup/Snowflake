"""
Snowflake Connection Manager
Handles authentication and connection pooling
Supports: Password, Private Key, and Config File authentication
"""
import snowflake.connector
from snowflake.connector import DictCursor
from typing import Optional, Dict, Any, List
import logging
from contextlib import contextmanager
import json
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


class SnowflakeManager:
    """Manages Snowflake connections and queries"""

    def __init__(self):
        self.connection = None
        self.credentials: Optional[Dict[str, Any]] = None
        self.auth_type: str = "password"  # password, private_key, or config_file

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

    def _load_private_key(self, private_key_path: str, passphrase: Optional[str] = None):
        """Load RSA private key from file"""
        try:
            with open(private_key_path, "rb") as key_file:
                private_key_bytes = key_file.read()

            # Parse the private key
            if passphrase:
                private_key = serialization.load_pem_private_key(
                    private_key_bytes,
                    password=passphrase.encode(),
                    backend=default_backend()
                )
            else:
                private_key = serialization.load_pem_private_key(
                    private_key_bytes,
                    password=None,
                    backend=default_backend()
                )

            # Serialize to DER format for Snowflake
            private_key_der = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            logger.info("Private key loaded successfully")
            return private_key_der

        except Exception as e:
            logger.error(f"Failed to load private key: {str(e)}")
            raise ValueError(f"Failed to load private key: {str(e)}")

    def _load_config_file(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON or TOML file"""
        try:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")

            with open(config_path, 'r') as f:
                if config_path.endswith('.json'):
                    config = json.load(f)
                elif config_path.endswith('.toml'):
                    try:
                        import toml
                        config = toml.load(f)
                    except ImportError:
                        raise ImportError("toml library required for .toml files. Install with: pip install toml")
                else:
                    # Try JSON by default
                    config = json.load(f)

            logger.info(f"Config loaded from {config_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load config file: {str(e)}")
            raise ValueError(f"Failed to load config file: {str(e)}")

    def set_credentials(
        self,
        account: str,
        user: str,
        password: Optional[str] = None,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None,
        private_key_path: Optional[str] = None,
        private_key_passphrase: Optional[str] = None,
    ):
        """Store Snowflake credentials with password authentication"""
        # Normalize the account identifier
        normalized_account = self._normalize_account_identifier(account)

        self.auth_type = "password"
        self.credentials = {
            "account": normalized_account,
            "user": user,
            "password": password,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "role": role,
        }

        # If private key is provided, use key-pair authentication
        if private_key_path:
            try:
                private_key_der = self._load_private_key(private_key_path, private_key_passphrase)
                self.auth_type = "private_key"
                self.credentials["private_key"] = private_key_der
                self.credentials.pop("password", None)  # Remove password if using key
                logger.info("Using private key authentication")
            except Exception as e:
                logger.error(f"Failed to load private key, falling back to password auth: {str(e)}")

    def set_credentials_from_key(
        self,
        account: str,
        user: str,
        private_key_path: str,
        private_key_passphrase: Optional[str] = None,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None,
    ):
        """Store Snowflake credentials with private key authentication"""
        normalized_account = self._normalize_account_identifier(account)
        private_key_der = self._load_private_key(private_key_path, private_key_passphrase)

        self.auth_type = "private_key"
        self.credentials = {
            "account": normalized_account,
            "user": user,
            "private_key": private_key_der,
            "warehouse": warehouse,
            "database": database,
            "schema": schema,
            "role": role,
        }
        logger.info("Private key authentication configured")

    def set_credentials_from_config(self, config_path: str, connection_name: str = "default"):
        """Load Snowflake credentials from configuration file"""
        config = self._load_config_file(config_path)

        # Support different config formats
        if connection_name in config:
            conn_config = config[connection_name]
        elif "connections" in config and connection_name in config["connections"]:
            conn_config = config["connections"][connection_name]
        else:
            conn_config = config

        # Extract credentials
        account = conn_config.get("account")
        user = conn_config.get("user") or conn_config.get("username")
        password = conn_config.get("password")
        private_key_path = conn_config.get("private_key_path") or conn_config.get("private_key")
        private_key_passphrase = conn_config.get("private_key_passphrase")
        warehouse = conn_config.get("warehouse")
        database = conn_config.get("database")
        schema = conn_config.get("schema")
        role = conn_config.get("role")

        if not account or not user:
            raise ValueError("Config file must contain 'account' and 'user' fields")

        # Determine authentication method
        if private_key_path:
            self.set_credentials_from_key(
                account=account,
                user=user,
                private_key_path=private_key_path,
                private_key_passphrase=private_key_passphrase,
                warehouse=warehouse,
                database=database,
                schema=schema,
                role=role
            )
        elif password:
            self.set_credentials(
                account=account,
                user=user,
                password=password,
                warehouse=warehouse,
                database=database,
                schema=schema,
                role=role
            )
        else:
            raise ValueError("Config file must contain either 'password' or 'private_key_path'")

        logger.info(f"Credentials loaded from config file: {config_path}")

    def test_connection(self) -> Dict[str, Any]:
        """Test Snowflake connection with stored credentials"""
        if not self.credentials:
            return {"success": False, "error": "No credentials configured"}

        try:
            logger.info(f"Testing connection to account: {self.credentials['account']} using {self.auth_type} authentication")

            # Build connection parameters
            conn_params = {
                "account": self.credentials["account"],
                "user": self.credentials["user"],
                "login_timeout": 60,
                "network_timeout": 60,
            }

            # Add authentication method
            if self.auth_type == "private_key" and "private_key" in self.credentials:
                conn_params["private_key"] = self.credentials["private_key"]
                logger.info("Using private key authentication")
            elif "password" in self.credentials and self.credentials["password"]:
                conn_params["password"] = self.credentials["password"]
                logger.info("Using password authentication")
            else:
                return {"success": False, "error": "No valid authentication method configured"}

            # Add optional parameters only if they're provided
            if self.credentials.get("warehouse"):
                conn_params["warehouse"] = self.credentials["warehouse"]
            if self.credentials.get("database"):
                conn_params["database"] = self.credentials["database"]
            if self.credentials.get("schema"):
                conn_params["schema"] = self.credentials["schema"]
            if self.credentials.get("role"):
                conn_params["role"] = self.credentials["role"]

            logger.info(f"Connection parameters: account={conn_params['account']}, user={conn_params['user']}, auth={self.auth_type}")

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
                "auth_method": self.auth_type,
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
                "login_timeout": 60,
                "network_timeout": 60,
            }

            # Add authentication method
            if self.auth_type == "private_key" and "private_key" in self.credentials:
                conn_params["private_key"] = self.credentials["private_key"]
            elif "password" in self.credentials and self.credentials["password"]:
                conn_params["password"] = self.credentials["password"]
            else:
                raise ValueError("No valid authentication method configured")

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
