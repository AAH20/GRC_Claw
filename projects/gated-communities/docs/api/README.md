# Gated Communities API

## OpenAPI 3.1 Spec

```yaml
openapi: 3.1.0
info:
  title: Gated Communities API
  version: 1.0.0
  description: Manage gated communities, memberships, and access control.
servers:
  - url: https://api.example.com/v1
paths:
  /communities:
    get:
      summary: List communities
      parameters:
        - name: limit
          in: query
          schema: { type: integer, default: 20 }
        - name: offset
          in: query
          schema: { type: integer, default: 0 }
      responses:
        '200': { description: Paginated list of communities }
    post:
      summary: Create a community
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, visibility]
              properties:
                name: { type: string }
                visibility: { type: string, enum: [public, private, hidden] }
      responses:
        '201': { description: Community created }
  /communities/{id}:
    get:
      summary: Get community by ID
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200': { description: Community details }
        '404': { description: Not found }
    patch:
      summary: Update community
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name: { type: string }
                visibility: { type: string, enum: [public, private, hidden] }
      responses:
        '200': { description: Updated community }
    delete:
      summary: Delete community
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '204': { description: Deleted }
  /communities/{id}/members:
    get:
      summary: List members
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200': { description: Member list }
    post:
      summary: Add member
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id, role]
              properties:
                user_id: { type: string }
                role: { type: string, enum: [member, moderator, admin] }
      responses:
        '201': { description: Member added }
  /communities/{id}/members/{user_id}:
    delete:
      summary: Remove member
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
        - name: user_id
          in: path
          required: true
          schema: { type: string }
      responses:
        '204': { description: Member removed }
  /communities/{id}/join:
    post:
      summary: Request to join
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '202': { description: Join request submitted }
  /communities/{id}/leave:
    post:
      summary: Leave community
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '204': { description: Left community }
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Request/Response Examples

### Create Community
```bash
curl -X POST https://api.example.com/v1/communities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alpha", "visibility": "private"}'
```
Response `201`:
```json
{ "id": "cli_abc123", "name": "Alpha", "visibility": "private", "created_at": "2026-10-03T12:00:00Z" }
```

### List Communities
```bash
curl "https://api.example.com/v1/communities?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN"
```
Response `200`:
```json
{ "data": [{ "id": "cli_abc123", "name": "Alpha" }], "total": 1, "limit": 10, "offset": 0 }
```

### Add Member
```bash
- X POST https://api.example.com/v1/communities/cli_abc123/members \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "usr_xyz", "role": "member"}'
```
Response `201`:
```json
{ "community_id": "cli_abc123", "user_id": "usr_xyz", "role": "member", "joined_at": "2026-10-03T12:05:00Z" }
```

## Authentication

All endpoints require a Bearer JWT token. Include it in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

Tokens are obtained via the auth service and expire after 1 hour. Include the `sub` (user ID) and `scope` claims. The API validates the token signature, expiry, and required scopes before processing any request.

| Scope | Access |
|-------|--------|
| `communities:read` | GET endpoints |
| `communities:write` | POST, PATCH, DELETE endpoints |

## Rate Limiting

Rate limits are enforced per authenticated user:

| Tier | Requests/min | Burst |
|------|-------------|-------|
| Default | 60 | 10 |
| Premium | 300 | 50 |

Headers returned on every response:
- `X-RateLimit-Limit` — requests allowed per window
- `X-RateLimit-Remaining` — requests left in current window
- `X-RateLimit-Reset` — Unix timestamp when the window resets

When the limit is exceeded, the API returns `429 Too Many Requests` with a `Retry-After` header indicating seconds to wait.
