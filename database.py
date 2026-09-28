import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

DATABASE_NAME = "licenses.db"

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT UNIQUE NOT NULL,
        user_id TEXT DEFAULT NULL,          -- Stores Discord Snowflake string
        is_activated INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        activated_at DATETIME DEFAULT NULL
    );
    """
    with get_connection() as conn:
        conn.execute(create_table_query)

def generate_license() -> str:
    new_key = str(uuid.uuid4()).upper()
    query = "INSERT INTO licenses (license_key) VALUES (?);"
    with get_connection() as conn:
        conn.execute(query, (new_key,))
    return new_key

def activate_license(license_key: str, user_id: str) -> Dict[str, Any]:
    if not isinstance(user_id, str) or not user_id.isdigit():
        return {"status": "ERROR", "message": "Invalid user_id format. Must be a numeric string."}

    select_query = "SELECT is_activated, user_id, activated_at FROM licenses WHERE license_key = ?;"
    update_query = """
        UPDATE licenses 
        SET is_activated = 1, user_id = ?, activated_at = ? 
        WHERE license_key = ?;
    """
    
    with get_connection() as conn:
        cursor = conn.execute(select_query, (license_key,))
        row = cursor.fetchone()
        
        if not row:
            return {"status": "INVALID", "message": "License key not found."}
        
        if row["is_activated"] == 1:
            return {
                "status": "ALREADY_ACTIVE", 
                "message": f"License is already claimed by user {row['user_id']}.",
                "user_id": row["user_id"],
                "activated_at": row["activated_at"]
            }
        
        user_check_query = "SELECT license_key FROM licenses WHERE user_id = ?;"
        if conn.execute(user_check_query, (user_id,)).fetchone():
            return {"status": "LIMIT_EXCEEDED", "message": "This Discord user already has an active license."}
        
        now_ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        
        conn.execute(update_query, (user_id, now_ts, license_key))
        
        return {
            "status": "ACTIVATED", 
            "message": "License successfully bound to Discord user.",
            "user_id": user_id,
            "activated_at": now_ts
        }