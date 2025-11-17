import sqlite3

DB_PATH = "d:\\ExplainNet\\explainnet.db"

ALTER_STATEMENTS = [
    ("sentiments", "gemini_justification", "TEXT"),
    ("sentiments", "gemini_sarcasm_score", "REAL"),
    ("sentiments", "hf_justification", "TEXT"),

    ("comments", "hf_justification", "TEXT"),
    ("comments", "gemini_justification", "TEXT"),
    ("comments", "gemini_sarcasm_score", "REAL"),

    ("news_articles", "gemini_justification", "TEXT"),
    ("news_articles", "gemini_sarcasm_score", "REAL"),
    ("news_articles", "hf_justification", "TEXT"),
]


def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    return column in cols


def add_column(cursor, table, column, col_type):
    print(f"Adding column {column} to {table} ({col_type})")
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for table, column, col_type in ALTER_STATEMENTS:
        try:
            if not column_exists(cur, table, column):
                add_column(cur, table, column, col_type)
            else:
                print(f"Column {column} already exists in {table}, skipping.")
        except sqlite3.OperationalError as e:
            print(f"OperationalError for {table}.{column}: {e}")
        except Exception as e:
            print(f"Error processing {table}.{column}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")


if __name__ == '__main__':
    main()
