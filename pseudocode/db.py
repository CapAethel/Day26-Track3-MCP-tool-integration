import sqlite3
from pathlib import Path


class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""


class SQLiteAdapter:
    """SQLite adapter used by MCP tools with strict request validation."""

    SUPPORTED_OPERATORS = {
        "eq": "=",
        "ne": "!=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "like": "LIKE",
        "in": "IN",
    }

    SUPPORTED_METRICS = {"count", "avg", "sum", "min", "max"}

    def __init__(self, db_path):
        self.db_path = str(Path(db_path))

    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def list_tables(self):
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def get_table_schema(self, table):
        self._validate_table(table)
        with self.connect() as connection:
            rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        return [
            {
                "cid": row["cid"],
                "name": row["name"],
                "type": row["type"],
                "notnull": bool(row["notnull"]),
                "default": row["dflt_value"],
                "pk": bool(row["pk"]),
            }
            for row in rows
        ]

    def get_database_schema(self):
        return {table: self.get_table_schema(table) for table in self.list_tables()}

    def search(
        self,
        table,
        columns=None,
        filters=None,
        limit=20,
        offset=0,
        order_by=None,
        descending=False,
    ):
        self._validate_table(table)
        table_columns = self._table_columns(table)
        selected_columns = self._normalize_columns(columns, table_columns)
        where_sql, parameters = self._build_where_clause(table_columns, filters or [])

        try:
            limit = int(limit)
            offset = int(offset)
        except (TypeError, ValueError):
            raise ValidationError("limit and offset must be integers")

        if limit <= 0 or limit > 1000:
            raise ValidationError("limit must be between 1 and 1000")
        if offset < 0:
            raise ValidationError("offset must be >= 0")

        order_sql = ""
        if order_by is not None:
            if order_by not in table_columns:
                raise ValidationError(f"unknown order_by column '{order_by}'")
            direction = "DESC" if descending else "ASC"
            order_sql = f" ORDER BY {order_by} {direction}"

        sql = (
            f"SELECT {', '.join(selected_columns)} FROM {table}{where_sql}"
            f"{order_sql} LIMIT ? OFFSET ?"
        )
        parameters.extend([limit, offset])

        with self.connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()

        return [dict(row) for row in rows]

    def insert(self, table, values):
        self._validate_table(table)
        if not isinstance(values, dict) or not values:
            raise ValidationError("values must be a non-empty object")

        table_columns = self._table_columns(table)
        payload = dict(values)

        for column_name in payload:
            if column_name not in table_columns:
                raise ValidationError(f"unknown column '{column_name}' for table '{table}'")

        columns = list(payload.keys())
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        parameters = [payload[column] for column in columns]

        with self.connect() as connection:
            cursor = connection.execute(sql, parameters)
            connection.commit()
            inserted_id = cursor.lastrowid

        return {"id": inserted_id, "table": table, "values": payload}

    def aggregate(self, table, metric, column=None, filters=None, group_by=None):
        self._validate_table(table)
        table_columns = self._table_columns(table)

        metric_normalized = str(metric).lower()
        if metric_normalized not in self.SUPPORTED_METRICS:
            raise ValidationError(
                f"unsupported metric '{metric}'. Supported: {sorted(self.SUPPORTED_METRICS)}"
            )

        if metric_normalized == "count":
            target_expression = "*" if column is None else self._validate_column(column, table_columns)
        else:
            if column is None:
                raise ValidationError(f"column is required for metric '{metric_normalized}'")
            target_expression = self._validate_column(column, table_columns)

        group_by_columns = self._normalize_group_by(group_by, table_columns)
        where_sql, parameters = self._build_where_clause(table_columns, filters or [])

        select_parts = []
        if group_by_columns:
            select_parts.extend(group_by_columns)
        select_parts.append(f"{metric_normalized.upper()}({target_expression}) AS value")

        group_sql = f" GROUP BY {', '.join(group_by_columns)}" if group_by_columns else ""
        sql = f"SELECT {', '.join(select_parts)} FROM {table}{where_sql}{group_sql}"

        with self.connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()

        return [dict(row) for row in rows]

    def _validate_table(self, table):
        if table not in self.list_tables():
            raise ValidationError(f"unknown table '{table}'")

    def _table_columns(self, table):
        return {column["name"] for column in self.get_table_schema(table)}

    def _normalize_columns(self, columns, allowed_columns):
        if columns is None:
            return sorted(allowed_columns)
        if not isinstance(columns, list) or not columns:
            raise ValidationError("columns must be a non-empty list")
        normalized = []
        for column in columns:
            normalized.append(self._validate_column(column, allowed_columns))
        return normalized

    def _validate_column(self, column, allowed_columns):
        if column not in allowed_columns:
            raise ValidationError(f"unknown column '{column}'")
        return column

    def _normalize_group_by(self, group_by, allowed_columns):
        if group_by is None:
            return []
        if isinstance(group_by, str):
            return [self._validate_column(group_by, allowed_columns)]
        if not isinstance(group_by, list) or not group_by:
            raise ValidationError("group_by must be a column name or non-empty list")
        return [self._validate_column(column, allowed_columns) for column in group_by]

    def _build_where_clause(self, allowed_columns, filters):
        if not filters:
            return "", []
        if not isinstance(filters, list):
            raise ValidationError("filters must be a list")

        clauses = []
        parameters = []
        for item in filters:
            if not isinstance(item, dict):
                raise ValidationError("each filter must be an object")

            column = item.get("column")
            op = item.get("op", "eq")
            value = item.get("value")

            self._validate_column(column, allowed_columns)
            if op not in self.SUPPORTED_OPERATORS:
                raise ValidationError(
                    f"unsupported operator '{op}'. Supported: {sorted(self.SUPPORTED_OPERATORS)}"
                )

            if op == "in":
                if not isinstance(value, list) or not value:
                    raise ValidationError("operator 'in' requires a non-empty list value")
                placeholders = ", ".join(["?"] * len(value))
                clauses.append(f"{column} IN ({placeholders})")
                parameters.extend(value)
            else:
                clauses.append(f"{column} {self.SUPPORTED_OPERATORS[op]} ?")
                parameters.append(value)

        return f" WHERE {' AND '.join(clauses)}", parameters
