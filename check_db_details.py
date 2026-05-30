
from pathlib import Path
from sqlalchemy import create_engine, text

print("Checking for app.db files...")
for path in Path(".").rglob("app.db"):
    print(f"\nChecking database at: {path.resolve()}")
    engine = create_engine(f"sqlite:///{path.resolve()}")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables found: {tables}")
            
            # If it has tables, check counts
            if tables:
                for table in ['platform_transactions', 'bank_settlements', 'reconciliation_runs']:
                    if table in tables:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.fetchone()[0]
                        print(f"{table}: {count} rows")
                        
                        if count > 0:
                            sample_result = conn.execute(text(f"SELECT * FROM {table} LIMIT 1"))
                            row = sample_result.fetchone()
                            print(f"Sample row (first row): {row}")
    except Exception as e:
        print(f"Error: {e}")
