from sqlalchemy import create_engine, text
import sqlite3

from app.core.config import get_settings

settings = get_settings()

def move_user_signins():
    src_engine = create_engine(f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    with src_engine.connect() as src_conn, sqlite3.connect("db.sqlite3") as dest_conn:
        src_cursor = src_conn.execution_options(stream_results=True).execute(
            text("""
            SELECT id, user_id, ip_address, user_agent, status, signin_at FROM etime_user_signins;
        """))

        dest_cursor = dest_conn.cursor()

        while rows := src_cursor.fetchmany(size=1000):
            new_rows = []

            for row in rows:
                row = list(row)
                if row[5] is not None:
                    row[5] = row[5].strftime("%Y-%m-%d %H:%M:%S")
                new_rows.append(tuple(row))

            dest_cursor.executemany("""
                INSERT INTO user_signins (
                    id, user_id, ip_address, user_agent, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, new_rows)
            
            dest_conn.commit()