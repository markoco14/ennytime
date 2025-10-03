"""This is moving the old shift_types table data to the new shifts table"""

from sqlalchemy import create_engine, text
import sqlite3

from app.core.config import get_settings

settings = get_settings()

def move_shifts():
    src_engine = create_engine(f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    with src_engine.connect() as src_conn, sqlite3.connect("db.sqlite3") as dest_conn:
        src_cursor = src_conn.execution_options(stream_results=True).execute(
            text("""
            SELECT id, long_name, short_name, user_id FROM etime_shift_types;
            """))

        dest_cursor = dest_conn.cursor()

        while rows := src_cursor.fetchmany(size=1000):
            dest_cursor.executemany("""
                INSERT INTO shifts (
                    id, long_name, short_name, user_id
                ) VALUES (?, ?, ?, ?)
            """, rows)
            
            dest_conn.commit()