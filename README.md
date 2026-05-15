# SQLite Lab MCP Server (FastMCP + SQLite)

This repository contains a complete MCP server implementation for the lab requirements.

Implemented tools:

- `search`
- `insert`
- `aggregate`

Implemented resources:

- `schema://database`
- `schema://table/{table_name}`

The server uses a SQLite database with strict validation for table names, column names, operators, and aggregate requests.

## Project Structure

```text
pseudocode/
  db.py
  init_db.py
  mcp_server.py
  verify_server.py
  tests/
    test_server.py
requirements.txt
Rubric.md
Tips.md
```

## Setup

1. Create a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Initialize database (optional, server auto-initializes if missing):

```powershell
python .\pseudocode\init_db.py
```

## Run Server

Start MCP server over stdio:

```powershell
python .\pseudocode\mcp_server.py
```

Optional custom DB path:

```powershell
$env:SQLITE_LAB_DB = "D:\\1Labs\\DAY26\\Day26-Track3-MCP-tool-integration\\pseudocode\\lab.db"
python .\pseudocode\mcp_server.py
```

## Tool Descriptions

### `search`

Query rows from a validated table with optional filters, ordering, and pagination.

Input highlights:

- `table` (required)
- `columns` (optional list)
- `filters` (optional list of `{column, op, value}`)
- `order_by`, `descending` (optional)
- `limit`, `offset` (optional)

Supported operators:

- `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `in`

### `insert`

Insert one row into a validated table using parameterized SQL.

Input highlights:

- `table` (required)
- `values` (required non-empty object)

### `aggregate`

Run aggregate queries with optional filters and grouping.

Input highlights:

- `table` (required)
- `metric` (required): `count`, `avg`, `sum`, `min`, `max`
- `column` (required for non-`count` metrics)
- `filters` (optional)
- `group_by` (optional string or list)

## Resources

- `schema://database`: full schema JSON for all tables
- `schema://table/{table_name}`: full schema JSON for a single table

## Safety and Validation

The server rejects:

- unknown tables
- unknown columns
- unsupported operators
- invalid aggregate metric or missing aggregate column
- empty or invalid inserts

All SQL execution uses parameterized values for dynamic inputs where appropriate.

## Verification Steps

### 1. Repeatable script

Run:

```powershell
python .\pseudocode\verify_server.py
```

This checks:

- DB initialization
- table/schema discovery
- valid `search`, `insert`, `aggregate`
- invalid table/operator rejection

### 2. Automated tests

Run:

```powershell
python -m unittest discover -s .\pseudocode\tests -p "test_*.py"
```

### 3. MCP Inspector

Run inspector against the local server:

```powershell
npx -y @modelcontextprotocol/inspector python .\pseudocode\mcp_server.py
```

Verify in Inspector:

- tools are discoverable (`search`, `insert`, `aggregate`)
- resources are discoverable (`schema://database`, `schema://table/{table_name}`)
- valid calls succeed
- invalid calls return clear errors

## MCP Client Integration Example (Gemini CLI)

```powershell
gemini mcp add sqlite-lab python D:\1Labs\DAY26\Day26-Track3-MCP-tool-integration\pseudocode\mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
```

Expected:

- server alias `sqlite-lab` appears as connected
- tools can be discovered and used in prompts

Example prompt:

```text
Use the sqlite-lab MCP server. Show the top 2 students by average enrollment score, then read schema://table/students.
```

## Demo Checklist

- Start server successfully
- Discover all tools
- Discover both resources
- Run valid `search`, `insert`, `aggregate` calls
- Demonstrate invalid request handling
- Show one MCP client using the server
- Record a short demo video (~2 minutes) and add the link here