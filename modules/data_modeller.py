"""
Data Modeller Module
Provides table relationships, data lineage, and DAG visualization
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataModeller:
    """Data Modeller for table relationships, lineage, and DAG visualization"""

    def __init__(self, snowflake_manager):
        """
        Initialize Data Modeller

        Args:
            snowflake_manager: SnowflakeManager instance
        """
        self.sf_manager = snowflake_manager

    def get_table_relationships(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get table relationships including primary keys, foreign keys, and constraints

        Args:
            database: Database name (optional, uses session default if not provided)
            schema: Schema name (optional, uses session default if not provided)

        Returns:
            Dictionary containing tables, relationships, and metadata
        """
        try:
            with self.sf_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Build database/schema filter
                db_filter = f"AND t.TABLE_SCHEMA = '{schema}'" if schema else ""
                if database:
                    db_filter = f"AND t.TABLE_CATALOG = '{database}' {db_filter}"
                else:
                    # Use current database
                    cursor.execute("SELECT CURRENT_DATABASE()")
                    database = cursor.fetchone()[0]
                    db_filter = f"AND t.TABLE_CATALOG = '{database}' {db_filter}"

                # Get all tables with row counts
                tables_query = f"""
                SELECT
                    t.TABLE_CATALOG,
                    t.TABLE_SCHEMA,
                    t.TABLE_NAME,
                    t.TABLE_TYPE,
                    t.ROW_COUNT,
                    t.BYTES,
                    t.CREATED,
                    t.LAST_ALTERED,
                    t.COMMENT
                FROM INFORMATION_SCHEMA.TABLES t
                WHERE t.TABLE_TYPE IN ('BASE TABLE', 'VIEW')
                {db_filter}
                ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME
                """
                cursor.execute(tables_query)
                tables_data = cursor.fetchall()

                tables = []
                for row in tables_data:
                    tables.append({
                        "database": row[0],
                        "schema": row[1],
                        "name": row[2],
                        "type": row[3],
                        "row_count": row[4],
                        "size_bytes": row[5],
                        "created": row[6].isoformat() if row[6] else None,
                        "last_altered": row[7].isoformat() if row[7] else None,
                        "comment": row[8],
                        "full_name": f"{row[0]}.{row[1]}.{row[2]}"
                    })

                # Get primary keys
                pk_query = f"""
                SELECT
                    TABLE_CATALOG,
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    CONSTRAINT_NAME,
                    COLUMN_NAME
                FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE
                WHERE CONSTRAINT_NAME IN (
                    SELECT CONSTRAINT_NAME
                    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
                    WHERE CONSTRAINT_TYPE = 'PRIMARY KEY'
                    {db_filter.replace('t.', '')}
                )
                ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
                """
                cursor.execute(pk_query)
                pk_data = cursor.fetchall()

                primary_keys = {}
                for row in pk_data:
                    table_key = f"{row[0]}.{row[1]}.{row[2]}"
                    if table_key not in primary_keys:
                        primary_keys[table_key] = {
                            "constraint_name": row[3],
                            "columns": []
                        }
                    primary_keys[table_key]["columns"].append(row[4])

                # Get foreign keys
                fk_query = f"""
                SELECT
                    rc.CONSTRAINT_CATALOG,
                    rc.CONSTRAINT_SCHEMA,
                    kcu1.TABLE_NAME AS FK_TABLE,
                    kcu1.COLUMN_NAME AS FK_COLUMN,
                    kcu2.TABLE_SCHEMA AS REF_SCHEMA,
                    kcu2.TABLE_NAME AS REF_TABLE,
                    kcu2.COLUMN_NAME AS REF_COLUMN,
                    rc.CONSTRAINT_NAME,
                    rc.UPDATE_RULE,
                    rc.DELETE_RULE
                FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu1
                    ON rc.CONSTRAINT_CATALOG = kcu1.CONSTRAINT_CATALOG
                    AND rc.CONSTRAINT_SCHEMA = kcu1.CONSTRAINT_SCHEMA
                    AND rc.CONSTRAINT_NAME = kcu1.CONSTRAINT_NAME
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu2
                    ON rc.UNIQUE_CONSTRAINT_CATALOG = kcu2.CONSTRAINT_CATALOG
                    AND rc.UNIQUE_CONSTRAINT_SCHEMA = kcu2.CONSTRAINT_SCHEMA
                    AND rc.UNIQUE_CONSTRAINT_NAME = kcu2.CONSTRAINT_NAME
                WHERE rc.CONSTRAINT_CATALOG = '{database}'
                {schema and f"AND rc.CONSTRAINT_SCHEMA = '{schema}'" or ''}
                ORDER BY kcu1.TABLE_NAME, rc.CONSTRAINT_NAME, kcu1.ORDINAL_POSITION
                """
                cursor.execute(fk_query)
                fk_data = cursor.fetchall()

                foreign_keys = []
                for row in fk_data:
                    foreign_keys.append({
                        "source_table": f"{row[0]}.{row[1]}.{row[2]}",
                        "source_column": row[3],
                        "target_table": f"{row[0]}.{row[4]}.{row[5]}",
                        "target_column": row[6],
                        "constraint_name": row[7],
                        "update_rule": row[8],
                        "delete_rule": row[9]
                    })

                # Get columns for all tables
                columns_query = f"""
                SELECT
                    TABLE_CATALOG,
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    COLUMN_NAME,
                    ORDINAL_POSITION,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT,
                    COMMENT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_CATALOG = '{database}'
                {schema and f"AND TABLE_SCHEMA = '{schema}'" or ''}
                ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
                """
                cursor.execute(columns_query)
                columns_data = cursor.fetchall()

                columns_by_table = {}
                for row in columns_data:
                    table_key = f"{row[0]}.{row[1]}.{row[2]}"
                    if table_key not in columns_by_table:
                        columns_by_table[table_key] = []
                    columns_by_table[table_key].append({
                        "name": row[3],
                        "position": row[4],
                        "data_type": row[5],
                        "nullable": row[6] == 'YES',
                        "default": row[7],
                        "comment": row[8]
                    })

                return {
                    "database": database,
                    "schema": schema,
                    "tables": tables,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys,
                    "columns": columns_by_table,
                    "summary": {
                        "total_tables": len(tables),
                        "total_relationships": len(foreign_keys),
                        "total_primary_keys": len(primary_keys)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get table relationships: {str(e)}")
            raise

    def get_object_lineage(
        self,
        object_name: str,
        object_type: str = "TABLE",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get upstream and downstream lineage for a Snowflake object

        Args:
            object_name: Fully qualified object name (DB.SCHEMA.OBJECT)
            object_type: Type of object (TABLE, VIEW, etc.)
            days: Number of days to look back for access history

        Returns:
            Dictionary containing upstream and downstream dependencies
        """
        try:
            with self.sf_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Parse object name
                parts = object_name.upper().split('.')
                if len(parts) != 3:
                    raise ValueError("Object name must be fully qualified (DATABASE.SCHEMA.OBJECT)")

                database, schema, obj = parts

                # Get upstream dependencies (objects this object depends on)
                upstream_query = f"""
                SELECT DISTINCT
                    referenced_database,
                    referenced_schema,
                    referenced_object_name,
                    referenced_object_domain,
                    COUNT(*) as reference_count
                FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                WHERE referencing_database = '{database}'
                AND referencing_schema = '{schema}'
                AND referencing_object_name = '{obj}'
                AND referenced_object_deleted IS NULL
                GROUP BY 1, 2, 3, 4
                ORDER BY reference_count DESC
                """
                cursor.execute(upstream_query)
                upstream_data = cursor.fetchall()

                upstream = []
                for row in upstream_data:
                    upstream.append({
                        "database": row[0],
                        "schema": row[1],
                        "name": row[2],
                        "type": row[3],
                        "full_name": f"{row[0]}.{row[1]}.{row[2]}",
                        "reference_count": row[4]
                    })

                # Get downstream dependencies (objects that depend on this object)
                downstream_query = f"""
                SELECT DISTINCT
                    referencing_database,
                    referencing_schema,
                    referencing_object_name,
                    referencing_object_domain,
                    COUNT(*) as reference_count
                FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                WHERE referenced_database = '{database}'
                AND referenced_schema = '{schema}'
                AND referenced_object_name = '{obj}'
                AND referencing_object_deleted IS NULL
                GROUP BY 1, 2, 3, 4
                ORDER BY reference_count DESC
                """
                cursor.execute(downstream_query)
                downstream_data = cursor.fetchall()

                downstream = []
                for row in downstream_data:
                    downstream.append({
                        "database": row[0],
                        "schema": row[1],
                        "name": row[2],
                        "type": row[3],
                        "full_name": f"{row[0]}.{row[1]}.{row[2]}",
                        "reference_count": row[4]
                    })

                # Get column-level lineage from access history
                column_lineage_query = f"""
                SELECT
                    value:objectName::string AS source_object,
                    value:objectDomain::string AS source_type,
                    value:columns AS source_columns,
                    direct_objects_accessed
                FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
                LATERAL FLATTEN(input => base_objects_accessed)
                WHERE query_start_time >= DATEADD(day, -{days}, CURRENT_TIMESTAMP())
                AND (value:objectName::string = '{database}.{schema}.{obj}'
                     OR ARRAY_CONTAINS('{database}.{schema}.{obj}'::variant, direct_objects_accessed))
                LIMIT 1000
                """

                try:
                    cursor.execute(column_lineage_query)
                    lineage_data = cursor.fetchall()

                    column_lineage = []
                    for row in lineage_data:
                        if row[2]:  # source_columns
                            column_lineage.append({
                                "source_object": row[0],
                                "source_type": row[1],
                                "columns": row[2],
                                "accessed_objects": row[3]
                            })
                except Exception as e:
                    logger.warning(f"Could not retrieve column lineage: {str(e)}")
                    column_lineage = []

                return {
                    "object": {
                        "database": database,
                        "schema": schema,
                        "name": obj,
                        "type": object_type,
                        "full_name": object_name
                    },
                    "upstream": upstream,
                    "downstream": downstream,
                    "column_lineage": column_lineage,
                    "summary": {
                        "upstream_count": len(upstream),
                        "downstream_count": len(downstream),
                        "total_dependencies": len(upstream) + len(downstream)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get object lineage: {str(e)}")
            raise

    def get_task_dag(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get Task DAG (Directed Acyclic Graph) showing task dependencies

        Args:
            database: Database name (optional)
            schema: Schema name (optional)

        Returns:
            Dictionary containing task nodes and edges for DAG visualization
        """
        try:
            with self.sf_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Build filter
                db_filter = ""
                if database:
                    db_filter = f"WHERE DATABASE_NAME = '{database}'"
                    if schema:
                        db_filter += f" AND SCHEMA_NAME = '{schema}'"
                elif schema:
                    db_filter = f"WHERE SCHEMA_NAME = '{schema}'"

                # Get all tasks
                tasks_query = f"""
                SELECT
                    DATABASE_NAME,
                    SCHEMA_NAME,
                    NAME,
                    STATE,
                    SCHEDULE,
                    WAREHOUSE,
                    CREATED_ON,
                    LAST_COMMITTED_ON,
                    OWNER,
                    COMMENT,
                    PREDECESSORS,
                    CONDITION,
                    ALLOW_OVERLAPPING_EXECUTION,
                    ERROR_INTEGRATION,
                    LAST_SUSPENDED_ON
                FROM SNOWFLAKE.ACCOUNT_USAGE.TASKS
                {db_filter}
                AND DELETED IS NULL
                ORDER BY DATABASE_NAME, SCHEMA_NAME, NAME
                """
                cursor.execute(tasks_query)
                tasks_data = cursor.fetchall()

                nodes = []
                edges = []

                for row in tasks_data:
                    task_full_name = f"{row[0]}.{row[1]}.{row[2]}"

                    # Create node
                    node = {
                        "id": task_full_name,
                        "database": row[0],
                        "schema": row[1],
                        "name": row[2],
                        "state": row[3],
                        "schedule": row[4],
                        "warehouse": row[5],
                        "created_on": row[6].isoformat() if row[6] else None,
                        "last_committed": row[7].isoformat() if row[7] else None,
                        "owner": row[8],
                        "comment": row[9],
                        "condition": row[11],
                        "allow_overlapping": row[12],
                        "error_integration": row[13],
                        "last_suspended": row[14].isoformat() if row[14] else None
                    }
                    nodes.append(node)

                    # Parse predecessors to create edges
                    predecessors = row[10]
                    if predecessors:
                        # Predecessors can be a string or array
                        if isinstance(predecessors, str):
                            pred_list = [p.strip() for p in predecessors.split(',')]
                        else:
                            pred_list = predecessors

                        for pred in pred_list:
                            if pred:
                                edges.append({
                                    "from": pred,
                                    "to": task_full_name,
                                    "type": "task_dependency"
                                })

                # Get task execution history
                task_history_query = f"""
                SELECT
                    DATABASE_NAME,
                    SCHEMA_NAME,
                    NAME,
                    STATE,
                    SCHEDULED_TIME,
                    COMPLETED_TIME,
                    ERROR_CODE,
                    ERROR_MESSAGE
                FROM SNOWFLAKE.ACCOUNT_USAGE.TASK_HISTORY
                WHERE SCHEDULED_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
                {db_filter.replace('WHERE', 'AND') if db_filter else ''}
                ORDER BY SCHEDULED_TIME DESC
                LIMIT 1000
                """
                cursor.execute(task_history_query)
                history_data = cursor.fetchall()

                task_history = []
                for row in history_data:
                    task_history.append({
                        "task": f"{row[0]}.{row[1]}.{row[2]}",
                        "state": row[3],
                        "scheduled_time": row[4].isoformat() if row[4] else None,
                        "completed_time": row[5].isoformat() if row[5] else None,
                        "error_code": row[6],
                        "error_message": row[7]
                    })

                return {
                    "database": database,
                    "schema": schema,
                    "nodes": nodes,
                    "edges": edges,
                    "execution_history": task_history,
                    "summary": {
                        "total_tasks": len(nodes),
                        "total_dependencies": len(edges),
                        "active_tasks": len([n for n in nodes if n["state"] == "started"]),
                        "suspended_tasks": len([n for n in nodes if n["state"] == "suspended"])
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get task DAG: {str(e)}")
            raise

    def get_procedure_dependencies(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get stored procedure dependencies and call graph

        Args:
            database: Database name (optional)
            schema: Schema name (optional)

        Returns:
            Dictionary containing procedures and their dependencies
        """
        try:
            with self.sf_manager.get_connection() as conn:
                cursor = conn.cursor()

                # Build filter
                db_filter = ""
                if database:
                    db_filter = f"WHERE PROCEDURE_CATALOG = '{database}'"
                    if schema:
                        db_filter += f" AND PROCEDURE_SCHEMA = '{schema}'"
                elif schema:
                    db_filter = f"WHERE PROCEDURE_SCHEMA = '{schema}'"

                # Get all procedures
                procedures_query = f"""
                SELECT
                    PROCEDURE_CATALOG,
                    PROCEDURE_SCHEMA,
                    PROCEDURE_NAME,
                    PROCEDURE_LANGUAGE,
                    PROCEDURE_DEFINITION,
                    CREATED,
                    LAST_ALTERED,
                    COMMENT
                FROM INFORMATION_SCHEMA.PROCEDURES
                {db_filter}
                ORDER BY PROCEDURE_CATALOG, PROCEDURE_SCHEMA, PROCEDURE_NAME
                """
                cursor.execute(procedures_query)
                procedures_data = cursor.fetchall()

                procedures = []
                for row in procedures_data:
                    procedures.append({
                        "database": row[0],
                        "schema": row[1],
                        "name": row[2],
                        "language": row[3],
                        "definition": row[4],
                        "created": row[5].isoformat() if row[5] else None,
                        "last_altered": row[6].isoformat() if row[6] else None,
                        "comment": row[7],
                        "full_name": f"{row[0]}.{row[1]}.{row[2]}"
                    })

                # Get procedure dependencies from OBJECT_DEPENDENCIES
                dependencies = []
                edges = []

                for proc in procedures:
                    proc_parts = proc["full_name"].split('.')

                    dep_query = f"""
                    SELECT DISTINCT
                        referenced_database,
                        referenced_schema,
                        referenced_object_name,
                        referenced_object_domain
                    FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                    WHERE referencing_database = '{proc_parts[0]}'
                    AND referencing_schema = '{proc_parts[1]}'
                    AND referencing_object_name = '{proc_parts[2]}'
                    AND referenced_object_deleted IS NULL
                    """
                    cursor.execute(dep_query)
                    dep_data = cursor.fetchall()

                    for dep_row in dep_data:
                        ref_full_name = f"{dep_row[0]}.{dep_row[1]}.{dep_row[2]}"
                        dependencies.append({
                            "procedure": proc["full_name"],
                            "referenced_object": ref_full_name,
                            "object_type": dep_row[3]
                        })

                        edges.append({
                            "from": proc["full_name"],
                            "to": ref_full_name,
                            "type": "procedure_dependency"
                        })

                return {
                    "database": database,
                    "schema": schema,
                    "procedures": procedures,
                    "dependencies": dependencies,
                    "edges": edges,
                    "summary": {
                        "total_procedures": len(procedures),
                        "total_dependencies": len(dependencies)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get procedure dependencies: {str(e)}")
            raise

    def get_all_objects_lineage(
        self,
        database: str,
        schema: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get comprehensive lineage for all objects in a database/schema

        Args:
            database: Database name
            schema: Schema name (optional)
            limit: Maximum number of objects to return

        Returns:
            Dictionary containing all object relationships
        """
        try:
            with self.sf_manager.get_connection() as conn:
                cursor = conn.cursor()

                schema_filter = f"AND referenced_schema = '{schema}'" if schema else ""

                # Get all object dependencies
                all_deps_query = f"""
                SELECT DISTINCT
                    referencing_database,
                    referencing_schema,
                    referencing_object_name,
                    referencing_object_domain,
                    referenced_database,
                    referenced_schema,
                    referenced_object_name,
                    referenced_object_domain
                FROM SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES
                WHERE (referenced_database = '{database}' OR referencing_database = '{database}')
                {schema_filter}
                AND referencing_object_deleted IS NULL
                AND referenced_object_deleted IS NULL
                LIMIT {limit}
                """
                cursor.execute(all_deps_query)
                deps_data = cursor.fetchall()

                nodes = {}
                edges = []

                for row in deps_data:
                    # Add referencing object as node
                    ref_id = f"{row[0]}.{row[1]}.{row[2]}"
                    if ref_id not in nodes:
                        nodes[ref_id] = {
                            "id": ref_id,
                            "database": row[0],
                            "schema": row[1],
                            "name": row[2],
                            "type": row[3]
                        }

                    # Add referenced object as node
                    target_id = f"{row[4]}.{row[5]}.{row[6]}"
                    if target_id not in nodes:
                        nodes[target_id] = {
                            "id": target_id,
                            "database": row[4],
                            "schema": row[5],
                            "name": row[6],
                            "type": row[7]
                        }

                    # Add edge
                    edges.append({
                        "from": ref_id,
                        "to": target_id,
                        "source_type": row[3],
                        "target_type": row[7]
                    })

                return {
                    "database": database,
                    "schema": schema,
                    "nodes": list(nodes.values()),
                    "edges": edges,
                    "summary": {
                        "total_objects": len(nodes),
                        "total_relationships": len(edges)
                    }
                }

        except Exception as e:
            logger.error(f"Failed to get all objects lineage: {str(e)}")
            raise
