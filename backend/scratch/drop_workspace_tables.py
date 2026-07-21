import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dev.db")

if not os.path.exists(db_path):
    print("Database file not found.")
    exit(1)

print(f"Connecting to database at: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [row[0] for row in cursor.fetchall()]
print(f"All tables: {all_tables}")

# Drop all _alembic_tmp_* tables
for table in all_tables:
    if table.startswith("_alembic_tmp_"):
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}"')
            print(f"Dropped temp table: {table}")
        except Exception as e:
            print(f"Error dropping {table}: {e}")

# Drop workspace-related tables
for table in ["workspace", "workspace_member", "comment", "audit_log"]:
    try:
        cursor.execute(f'DROP TABLE IF EXISTS "{table}"')
        print(f"Dropped table: {table}")
    except Exception as e:
        print(f"Error dropping {table}: {e}")

# Drop workspace_id column & index from these tables (if they exist)
tables_to_clean = [
    'account', 'bill', 'budget', 'daily_briefing', 'financial_event',
    'financial_insight', 'goal', 'import_history', 'import_template',
    'recurring_transaction', 'scenario', 'transaction'
]

for table in tables_to_clean:
    # Drop index
    try:
        cursor.execute(f'DROP INDEX IF EXISTS "ix_{table}_workspace_id"')
        print(f"Dropped index ix_{table}_workspace_id")
    except Exception as e:
        print(f"  index drop error on {table}: {e}")

    # Check if workspace_id column exists before trying to drop it
    try:
        cursor.execute(f'PRAGMA table_info("{table}")')
        cols = [row[1] for row in cursor.fetchall()]
        if 'workspace_id' in cols:
            cursor.execute(f'ALTER TABLE "{table}" DROP COLUMN workspace_id')
            print(f"Dropped workspace_id from {table}")
        else:
            print(f"  workspace_id not in {table}, skipping")
    except Exception as e:
        print(f"  column drop error on {table}: {e}")

conn.commit()
conn.close()
print("\nDatabase cleanup completed successfully.")
