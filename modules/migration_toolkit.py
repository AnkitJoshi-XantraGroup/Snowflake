"""
Migration & Integration Toolkit
AI-driven SQL conversion, schema mapping, and migration validation
"""
from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)


class MigrationToolkit:
    """Handles database migration and integration tasks"""

    def __init__(self, snowflake_manager):
        self.sf_manager = snowflake_manager

        # SQL dialect conversion patterns
        self.dialect_conversions = {
            "oracle_to_snowflake": {
                "NVL": "IFNULL",
                "SYSDATE": "CURRENT_TIMESTAMP()",
                "ROWNUM": "ROW_NUMBER() OVER (ORDER BY 1)",
                "DUAL": "",
                "VARCHAR2": "VARCHAR",
                "NUMBER": "NUMERIC",
            },
            "mssql_to_snowflake": {
                "GETDATE()": "CURRENT_TIMESTAMP()",
                "ISNULL": "IFNULL",
                "LEN": "LENGTH",
                "CONVERT": "TO_VARCHAR",
                "[dbo].": "",
            },
            "mysql_to_snowflake": {
                "NOW()": "CURRENT_TIMESTAMP()",
                "IFNULL": "COALESCE",
                "CONCAT": "CONCAT",
                "LIMIT": "LIMIT",  # Same in Snowflake
            },
        }

    def convert_sql_dialect(
        self, sql_text: str, source_dialect: str = "oracle"
    ) -> Dict[str, Any]:
        """Convert SQL from source dialect to Snowflake"""
        conversion_key = f"{source_dialect}_to_snowflake"
        conversions = self.dialect_conversions.get(conversion_key, {})

        converted_sql = sql_text
        applied_conversions = []

        for source_pattern, target_pattern in conversions.items():
            if source_pattern in converted_sql:
                converted_sql = converted_sql.replace(source_pattern, target_pattern)
                applied_conversions.append(
                    {
                        "from": source_pattern,
                        "to": target_pattern,
                    }
                )

        return {
            "original_sql": sql_text,
            "converted_sql": converted_sql,
            "conversions_applied": applied_conversions,
            "source_dialect": source_dialect,
            "target_dialect": "snowflake",
        }

    def analyze_schema_compatibility(
        self, database: str, schema: str
    ) -> Dict[str, Any]:
        """Analyze schema for migration compatibility"""
        issues = []
        warnings = []

        try:
            # Get table information
            query = f"""
            SELECT
                TABLE_NAME,
                TABLE_TYPE,
                ROW_COUNT,
                BYTES
            FROM {database}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{schema}'
            """
            tables = self.sf_manager.execute_query(query)

            # Get column information
            query = f"""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM {database}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            """
            columns = self.sf_manager.execute_query(query)

            # Analyze data types
            unsupported_types = ["BLOB", "CLOB", "XMLTYPE"]
            for col in columns:
                data_type = col.get("DATA_TYPE", "").upper()
                if any(unsupported in data_type for unsupported in unsupported_types):
                    issues.append(
                        {
                            "table": col.get("TABLE_NAME"),
                            "column": col.get("COLUMN_NAME"),
                            "issue": f"Data type {data_type} may need conversion",
                            "recommendation": "Consider using VARIANT or STRING type",
                        }
                    )

            # Check for large tables
            for table in tables:
                if table.get("BYTES", 0) > 1_000_000_000:  # > 1GB
                    warnings.append(
                        {
                            "table": table.get("TABLE_NAME"),
                            "size_bytes": table.get("BYTES"),
                            "warning": "Large table - plan for incremental migration",
                            "recommendation": "Use bulk loading with COPY INTO",
                        }
                    )

            return {
                "database": database,
                "schema": schema,
                "total_tables": len(tables),
                "total_columns": len(columns),
                "issues": issues,
                "warnings": warnings,
                "compatibility_score": max(
                    0, 100 - (len(issues) * 10 + len(warnings) * 5)
                ),
            }

        except Exception as e:
            logger.error(f"Failed to analyze schema compatibility: {str(e)}")
            return {"error": str(e)}

    def generate_ddl(
        self, database: str, schema: str, table_name: str
    ) -> Dict[str, Any]:
        """Generate DDL for a table"""
        try:
            query = f"""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM {database}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            columns = self.sf_manager.execute_query(query)

            if not columns:
                return {"error": "Table not found"}

            # Build CREATE TABLE statement
            ddl_lines = [f"CREATE TABLE {schema}.{table_name} ("]

            column_defs = []
            for col in columns:
                col_name = col.get("COLUMN_NAME")
                data_type = col.get("DATA_TYPE")
                is_nullable = col.get("IS_NULLABLE", "YES")
                default_val = col.get("COLUMN_DEFAULT")

                col_def = f"  {col_name} {data_type}"

                if is_nullable == "NO":
                    col_def += " NOT NULL"

                if default_val:
                    col_def += f" DEFAULT {default_val}"

                column_defs.append(col_def)

            ddl_lines.append(",\n".join(column_defs))
            ddl_lines.append(");")

            ddl = "\n".join(ddl_lines)

            return {
                "table_name": table_name,
                "ddl": ddl,
                "column_count": len(columns),
            }

        except Exception as e:
            logger.error(f"Failed to generate DDL: {str(e)}")
            return {"error": str(e)}

    def generate_copy_into_template(
        self, database: str, schema: str, table_name: str, stage_name: str = "@~"
    ) -> str:
        """Generate COPY INTO statement template"""
        template = f"""
-- COPY INTO template for {table_name}
COPY INTO {database}.{schema}.{table_name}
FROM {stage_name}/{table_name}/
FILE_FORMAT = (
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('NULL', 'null', '')
    ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
)
ON_ERROR = 'CONTINUE'
VALIDATION_MODE = 'RETURN_ERRORS';

-- To validate without loading:
-- VALIDATION_MODE = 'RETURN_ALL_ERRORS'

-- To see loaded files:
-- SELECT * FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
--     TABLE_NAME=>'{table_name}',
--     START_TIME=>DATEADD(hours, -1, CURRENT_TIMESTAMP())
-- ));
        """
        return template

    def validate_migration(
        self, source_table: str, target_table: str
    ) -> Dict[str, Any]:
        """Generate validation queries for migration"""
        validation_queries = {
            "row_count_check": f"""
-- Validate row counts match
SELECT
    'SOURCE' as TABLE_TYPE,
    COUNT(*) as ROW_COUNT
FROM {source_table}
UNION ALL
SELECT
    'TARGET' as TABLE_TYPE,
    COUNT(*) as ROW_COUNT
FROM {target_table};
            """,
            "checksum_check": f"""
-- Validate data integrity with checksum
SELECT
    'SOURCE' as TABLE_TYPE,
    HASH(*) as DATA_HASH
FROM {source_table}
UNION ALL
SELECT
    'TARGET' as TABLE_TYPE,
    HASH(*) as DATA_HASH
FROM {target_table};
            """,
            "column_comparison": f"""
-- Compare column statistics
SELECT
    'SOURCE' as TABLE_TYPE,
    COUNT(*) as TOTAL_ROWS,
    COUNT(DISTINCT *) as DISTINCT_ROWS
FROM {source_table}
UNION ALL
SELECT
    'TARGET' as TABLE_TYPE,
    COUNT(*) as TOTAL_ROWS,
    COUNT(DISTINCT *) as DISTINCT_ROWS
FROM {target_table};
            """,
        }

        return {
            "source_table": source_table,
            "target_table": target_table,
            "validation_queries": validation_queries,
        }

    def generate_etl_pipeline_template(
        self, pipeline_name: str, source_type: str = "S3"
    ) -> str:
        """Generate ELT pipeline template"""
        template = f"""
-- ELT Pipeline Template: {pipeline_name}
-- Source: {source_type}

-- Step 1: Create file format
CREATE OR REPLACE FILE FORMAT {pipeline_name}_csv_format
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    NULL_IF = ('NULL', 'null', '')
    FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- Step 2: Create external stage (for S3)
CREATE OR REPLACE STAGE {pipeline_name}_stage
    URL = 's3://your-bucket/path/'
    CREDENTIALS = (AWS_KEY_ID = 'your-key' AWS_SECRET_KEY = 'your-secret')
    FILE_FORMAT = {pipeline_name}_csv_format;

-- Step 3: Create target table
CREATE OR REPLACE TABLE {pipeline_name}_target (
    -- Define your columns here
    id NUMBER,
    data VARCHAR,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Step 4: Create staging table for validation
CREATE OR REPLACE TABLE {pipeline_name}_staging LIKE {pipeline_name}_target;

-- Step 5: Load data into staging
COPY INTO {pipeline_name}_staging
FROM @{pipeline_name}_stage
ON_ERROR = 'CONTINUE';

-- Step 6: Validate staging data
SELECT * FROM {pipeline_name}_staging LIMIT 10;

-- Step 7: Merge into target (upsert pattern)
MERGE INTO {pipeline_name}_target AS target
USING {pipeline_name}_staging AS source
ON target.id = source.id
WHEN MATCHED THEN
    UPDATE SET
        target.data = source.data,
        target.created_at = source.created_at
WHEN NOT MATCHED THEN
    INSERT (id, data, created_at)
    VALUES (source.id, source.data, source.created_at);

-- Step 8: Create task for automation (optional)
CREATE OR REPLACE TASK {pipeline_name}_task
    WAREHOUSE = 'YOUR_WAREHOUSE'
    SCHEDULE = 'USING CRON 0 */6 * * * UTC'  -- Every 6 hours
AS
    COPY INTO {pipeline_name}_staging
    FROM @{pipeline_name}_stage
    ON_ERROR = 'CONTINUE';

-- Enable task
-- ALTER TASK {pipeline_name}_task RESUME;
        """
        return template

    def generate_migration_recommendations(
        self,
    ) -> List[Dict[str, Any]]:
        """Generate migration best practice recommendations"""
        recommendations = [
            {
                "type": "BEST_PRACTICE",
                "severity": "INFO",
                "category": "Planning",
                "message": "Perform migration in phases",
                "recommendation": "Start with small, non-critical tables to validate the process",
            },
            {
                "type": "BEST_PRACTICE",
                "severity": "INFO",
                "category": "Data Loading",
                "message": "Use COPY INTO for bulk loading",
                "recommendation": "COPY INTO is more efficient than INSERT for large datasets",
            },
            {
                "type": "BEST_PRACTICE",
                "severity": "INFO",
                "category": "Validation",
                "message": "Always validate data after migration",
                "recommendation": "Compare row counts, checksums, and sample data between source and target",
            },
            {
                "type": "BEST_PRACTICE",
                "severity": "INFO",
                "category": "Performance",
                "message": "Consider clustering keys for large tables",
                "recommendation": "Add clustering keys on frequently filtered columns after initial load",
            },
            {
                "type": "BEST_PRACTICE",
                "severity": "INFO",
                "category": "Cost Optimization",
                "message": "Use appropriate warehouse size",
                "recommendation": "Start with X-Small warehouse and scale up if needed during migration",
            },
        ]

        return recommendations
