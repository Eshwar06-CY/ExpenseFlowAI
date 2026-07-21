import sqlite3

def main():
    conn = sqlite3.connect('backend/dev.db')
    cursor = conn.cursor()
    
    # 1. Print all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print("Tables before cleanup:", tables)
    
    # 2. Drop import_history, import_template, and alembic tmp table
    for table in ["import_history", "import_template", "_alembic_tmp_transaction"]:
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{table}"')
            print(f"Dropped table {table} if existed.")
        except Exception as e:
            print(f"Failed to drop table {table}:", e)
            
    # 3. Print columns in transaction
    cursor.execute('PRAGMA table_info("transaction")')
    cols = [c[1] for c in cursor.fetchall()]
    print("Columns in transaction:", cols)
    
    if "import_id" in cols:
        try:
            cursor.execute('ALTER TABLE "transaction" DROP COLUMN import_id')
            print("Dropped column import_id from transaction.")
        except Exception as e:
            print("Failed to drop import_id column:", e)
            
    # 4. Print all tables after cleanup
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables_after = [t[0] for t in cursor.fetchall()]
    print("Tables after cleanup:", tables_after)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
