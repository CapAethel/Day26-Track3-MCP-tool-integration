import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT UNIQUE,
    age INTEGER CHECK (age >= 0)
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    credits INTEGER NOT NULL DEFAULT 3
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    score REAL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, email, age) VALUES
('Alice Nguyen', 'A1', 'alice@example.com', 21),
('Bao Tran', 'A1', 'bao@example.com', 22),
('Chi Le', 'B2', 'chi@example.com', 20),
('Duc Pham', 'B2', 'duc@example.com', 23);

INSERT INTO courses (code, title, credits) VALUES
('SQL101', 'Introduction to SQL', 3),
('PY201', 'Applied Python', 4),
('STAT110', 'Statistics Fundamentals', 3);

INSERT INTO enrollments (student_id, course_id, score) VALUES
(1, 1, 8.5),
(1, 2, 9.0),
(2, 1, 7.8),
(2, 3, 8.1),
(3, 2, 8.7),
(4, 3, 7.4);
"""


def create_database(db_path=None, reset=True):
    """Create the SQLite database with deterministic schema and seed data."""
    if db_path is None:
        db_path = Path(__file__).resolve().parent / "lab.db"
    else:
        db_path = Path(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset and db_path.exists():
        db_path.unlink()

    with sqlite3.connect(str(db_path)) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.executescript(SEED_SQL)
        connection.commit()

    return str(db_path)


if __name__ == "__main__":
    path = create_database()
    print(path)
