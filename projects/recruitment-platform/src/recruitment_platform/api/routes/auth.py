"""Authentication routes for recruitment-platform."""
from __future__ import annotations

import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from jose import jwt
from pydantic import BaseModel
from recruitment_platform.security.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter()

DB_PATH = os.getenv("DATABASE_PATH", "./test_validation.db")


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _init_db() -> None:
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'recruiter',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    # Add missing columns if they don't exist (for pre-existing tables)
    existing_cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "password_hash" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "is_active" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    conn.commit()
    conn.close()


_init_db()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (request.email,)
    ).fetchone()
    conn.close()

    if not row or not verify_password(request.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
    }
    token = create_access_token({"sub": row["id"], "email": row["email"]})
    return AuthResponse(user=user, token=token)


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest) -> AuthResponse:
    conn = _get_db()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (request.email,)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    password_hash = get_password_hash(request.password)
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (request.name, request.email, password_hash, "recruiter"),
    )
    user_id = str(cursor.lastrowid)
    conn.commit()
    conn.close()

    user = {
        "id": user_id,
        "name": request.name,
        "email": request.email,
        "role": "recruiter",
    }
    token = create_access_token({"sub": user_id, "email": request.email})
    return AuthResponse(user=user, token=token)
