from sqlalchemy import create_engine, text
import sqlite3

from app.core.config import get_settings

settings = get_settings()

def move_users():
    src_engine = create_engine(f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")

    with src_engine.connect() as src_conn, sqlite3.connect("db.sqlite3") as dest_conn:
        src_cursor = src_conn.execution_options(stream_results=True).execute(
            text("""
            SELECT display_name, first_name, last_name, email, hashed_password, is_superuser, is_admin, is_active, is_verified, verified_at, created_at, updated_at, birthday, username FROM etime_users;
        """))

        dest_cursor = dest_conn.cursor()

        while rows := src_cursor.fetchmany(size=1000):
            new_rows = []

            for row in rows:
                row = list(row)
                for index in [10, 11, 12]:
                    if row[index] is not None:
                        row[index] = row[index].strftime("%Y-%m-%d %H:%M:%S")
                new_rows.append(tuple(row))

            dest_cursor.executemany("""
                INSERT INTO users (
                    display_name, first_name, last_name, email, hashed_password, is_superuser, is_admin, is_active, is_verified, verified_at, created_at, updated_at, birthday, username
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, new_rows)
            
            dest_conn.commit()