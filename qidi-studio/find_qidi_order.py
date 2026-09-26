import sqlite3

conn = sqlite3.connect('/mnt/hdd/rag_file_map.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

for t in tables:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in cur.fetchall()]
    print(f"\nTable {t} cols: {cols}")
    
    # Search for QIDI in text columns
    text_cols = [c for c in cols if 'id' not in c.lower() or c.lower() in ('subject', 'path', 'filename', 'title', 'body', 'sender', 'recipient', 'query', 'content')]
    for c in cols:
        try:
            query = f"SELECT * FROM {t} WHERE {c} LIKE '%qidi%' LIMIT 10"
            cur.execute(query)
            rows = cur.fetchall()
            if rows:
                print(f"--> Found {len(rows)} rows in {t}.{c}:")
                for row in rows[:5]:
                    print("   ", row[:5])
        except Exception as e:
            pass

        try:
            query = f"SELECT * FROM {t} WHERE {c} LIKE '%702-%' LIMIT 10"
            cur.execute(query)
            rows = cur.fetchall()
            if rows:
                print(f"--> Found Amazon Order in {t}.{c}:")
                for row in rows[:5]:
                    print("   ", row[:5])
        except Exception:
            pass
