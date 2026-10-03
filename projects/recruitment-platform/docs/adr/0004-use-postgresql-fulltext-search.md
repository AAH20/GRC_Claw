# ADR 0004: Use PostgreSQL Full-Text Search

## Status
Accepted

## Context
The platform needs efficient full-text search across jobs, candidates, and skills.

## Decision
Use PostgreSQL's built-in tsvector/tsquery with GIN indexes for full-text search, supplemented by pg_trgm for fuzzy matching.

## Consequences
- No external search engine dependency
- Trigram indexes enable fuzzy matching
- Weighted ranking provides relevant results
