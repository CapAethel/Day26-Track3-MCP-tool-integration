import json
from pathlib import Path

from db import SQLiteAdapter, ValidationError
from init_db import create_database


def run_verification():
    db_path = create_database(reset=True)
    adapter = SQLiteAdapter(db_path)

    checks = []

    checks.append({
        "name": "server_database_initialized",
        "ok": Path(db_path).exists(),
        "details": db_path,
    })

    tables = adapter.list_tables()
    checks.append({
        "name": "tables_discoverable",
        "ok": set(tables) == {"students", "courses", "enrollments"},
        "details": tables,
    })

    search_rows = adapter.search(
        table="students",
        filters=[{"column": "cohort", "op": "eq", "value": "A1"}],
        order_by="name",
        limit=10,
    )
    checks.append({
        "name": "search_valid_call",
        "ok": len(search_rows) >= 1,
        "details": search_rows,
    })

    inserted = adapter.insert(
        table="students",
        values={"name": "Emi Vu", "cohort": "A1", "email": "emi@example.com", "age": 24},
    )
    checks.append({
        "name": "insert_valid_call",
        "ok": bool(inserted.get("id")),
        "details": inserted,
    })

    agg_rows = adapter.aggregate(
        table="enrollments",
        metric="avg",
        column="score",
        group_by=None,
    )
    checks.append({
        "name": "aggregate_valid_call",
        "ok": len(agg_rows) == 1 and agg_rows[0].get("value") is not None,
        "details": agg_rows,
    })

    try:
        adapter.search(table="missing_table")
        checks.append({
            "name": "invalid_table_rejected",
            "ok": False,
            "details": "Expected ValidationError",
        })
    except ValidationError as error:
        checks.append({
            "name": "invalid_table_rejected",
            "ok": True,
            "details": str(error),
        })

    try:
        adapter.search(
            table="students",
            filters=[{"column": "cohort", "op": "contains", "value": "A"}],
        )
        checks.append({
            "name": "invalid_operator_rejected",
            "ok": False,
            "details": "Expected ValidationError",
        })
    except ValidationError as error:
        checks.append({
            "name": "invalid_operator_rejected",
            "ok": True,
            "details": str(error),
        })

    return checks


def main():
    checks = run_verification()
    passed = sum(1 for check in checks if check["ok"])
    summary = {
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
