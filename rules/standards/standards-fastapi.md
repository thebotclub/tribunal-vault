# FastAPI Project Standards

## Project Structure
- Organise by feature, not by layer: `src/feature/{router,service,models,schemas}.py`
- Keep routers thin — business logic belongs in service layer
- Use `APIRouter` with `prefix` and `tags` for all route groups

## Request/Response Schemas
- Separate Pydantic schemas for request (input) and response (output)
- Never expose ORM models directly as response schemas
- Use `model_config = ConfigDict(from_attributes=True)` for ORM→schema conversion
- Validate at the boundary — never trust raw request data past the schema layer

## Dependency Injection
- Use FastAPI `Depends()` for database sessions, auth, and shared services
- Database sessions must always be injected — never instantiated inside route handlers
- Scope sessions to request lifecycle using generator dependencies

## Async Best Practices
- Mark route handlers `async def` when doing I/O (DB, HTTP calls, file ops)
- Use `asyncio.gather()` for concurrent I/O operations
- Never call blocking code inside async handlers — use `run_in_executor` if unavoidable

## Error Handling
- Raise `HTTPException` for client errors (4xx) with descriptive `detail`
- Use exception handlers (`@app.exception_handler`) for domain exceptions
- Always return consistent error response shapes

## Testing (TDD)
- Use `pytest` + `httpx.AsyncClient` with `app` fixture
- Test each endpoint: success, validation error (422), auth error (401/403), not found (404)
- Use `pytest-asyncio` with `asyncio_mode = "auto"`
- Factory fixtures for test data — never use production data

## Performance
- Use connection pooling (SQLAlchemy `create_async_engine` with pool settings)
- Add pagination to all list endpoints (`limit`/`offset` or cursor-based)
- Cache expensive queries with Redis where latency matters

## Security
- Always authenticate via dependency injection — never inline auth checks
- Validate and sanitise all path/query parameters even after Pydantic validation
- Set `CORS`, `TrustedHost`, and rate-limiting middleware in production
