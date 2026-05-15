import json
import os

from fastmcp import FastMCP

from db import SQLiteAdapter, ValidationError
from init_db import create_database


def _build_adapter():
    db_path = os.getenv("SQLITE_LAB_DB")
    if db_path:
        if not os.path.exists(db_path):
            create_database(db_path=db_path, reset=True)
    else:
        db_path = create_database(reset=False)
    return SQLiteAdapter(db_path)


adapter = _build_adapter()
mcp = FastMCP("SQLite Lab MCP Server")


@mcp.tool(name="search")
def search(
    table,
    filters=None,
    columns=None,
    limit=20,
    offset=0,
    order_by=None,
    descending=False,
):
    """Search rows in a validated table with optional filters and pagination."""
    try:
        rows = adapter.search(
            table=table,
            columns=columns,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
        )
        return {
            "table": table,
            "count": len(rows),
            "limit": int(limit),
            "offset": int(offset),
            "rows": rows,
        }
    except ValidationError as error:
        raise ValueError(str(error)) from error


@mcp.tool(name="insert")
def insert(table, values):
    """Insert one row into a validated table using parameterized SQL."""
    try:
        result = adapter.insert(table=table, values=values)
        return {"inserted": result}
    except ValidationError as error:
        raise ValueError(str(error)) from error


@mcp.tool(name="aggregate")
def aggregate(table, metric, column=None, filters=None, group_by=None):
    """Compute count/avg/sum/min/max over validated table columns."""
    try:
        rows = adapter.aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by,
        )
        return {
            "table": table,
            "metric": metric,
            "column": column,
            "group_by": group_by,
            "rows": rows,
        }
    except ValidationError as error:
        raise ValueError(str(error)) from error


@mcp.resource("schema://database")
def database_schema():
    """Return a JSON schema snapshot for all tables in the database."""
    return json.dumps(adapter.get_database_schema(), indent=2)


@mcp.resource("schema://table/{table_name}")
def table_schema(table_name):
    """Return a JSON schema snapshot for one validated table."""
    try:
        schema = {table_name: adapter.get_table_schema(table_name)}
        return json.dumps(schema, indent=2)
    except ValidationError as error:
        raise ValueError(str(error)) from error


if __name__ == "__main__":
    mcp.run()
