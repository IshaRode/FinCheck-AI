"""
Database connection and migration manager for FinCheck AI.
Manages Supabase PostgreSQL connection and pgvector extension verification.
"""

import os
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import psycopg2
from psycopg2.extras import RealDictCursor
from backend.app.config import settings


def get_db_connection():
    """Returns a new psycopg2 connection using the configured DATABASE_URL."""
    if not settings.DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is not set. Please provide your Supabase connection string in the .env file."
        )
    return psycopg2.connect(settings.DATABASE_URL)


def verify_connection() -> dict:
    """
    Verifies connection to PostgreSQL, checks pgvector extension,
    and validates halfvec type support.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. PostgreSQL version
            cur.execute("SELECT version();")
            pg_version = cur.fetchone()["version"]

            # 2. Check if vector extension is available or installed
            cur.execute(
                "SELECT installed_version, default_version FROM pg_available_extensions WHERE name = 'vector';"
            )
            ext_info = cur.fetchone()
            if not ext_info:
                raise RuntimeError("pgvector extension is not available in this PostgreSQL instance.")

            # 3. Ensure vector extension is created
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()

            # 4. Verify halfvec type exists
            cur.execute(
                "SELECT typname FROM pg_type WHERE typname = 'halfvec';"
            )
            halfvec_info = cur.fetchone()
            has_halfvec = halfvec_info is not None
            if not has_halfvec:
                raise RuntimeError(
                    "pgvector is installed, but the 'halfvec' type is unavailable. "
                    "A modern pgvector version (>= 0.7.0) is required for halfvec(2048)."
                )

            return {
                "status": "connected",
                "pg_version": pg_version,
                "pgvector_version": ext_info.get("installed_version") or ext_info.get("default_version"),
                "halfvec_supported": True,
            }
    finally:
        conn.close()


def apply_migrations(schema_path: Optional[str] = None):
    """Applies database/schema.sql to create tables, indexes, and RPC functions."""
    if schema_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        schema_path = str(base_dir / "database" / "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_commands = f.read()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql_commands)
        conn.commit()
        print(f"[SUCCESS] Database migrations applied successfully from {schema_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        info = verify_connection()
        print("[SUCCESS] Connected to database:")
        for k, v in info.items():
            print(f"  {k}: {v}")
        apply_migrations()
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
