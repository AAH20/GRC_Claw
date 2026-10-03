# ADR 0001: Use JWT for Authentication

## Status
Accepted

## Context
The recruitment platform needs a secure, stateless authentication mechanism that supports both web and API clients.

## Decision
Use JSON Web Tokens (JWT) with HS256 algorithm for authentication. Access tokens expire after 30 minutes, refresh tokens after 7 days.

## Consequences
- Stateless authentication enables horizontal scaling
- Short-lived access tokens reduce security risk
- Refresh tokens enable seamless re-authentication
