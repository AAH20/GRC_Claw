"""GraphQL endpoint."""

from fastapi import APIRouter, Depends, Request
from strawberry.fastapi import GraphQLRouter

from app.graphql.schema import schema
from app.middleware.auth import AuthContext, get_current_auth

router = APIRouter(tags=["GraphQL"])


async def get_graphql_context(request: Request, auth: AuthContext = Depends(get_current_auth)):
    """Get GraphQL context with authentication."""
    return {
        "request": request,
        "auth": auth,
    }


graphql_router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphql_ide="apollo-sandbox",
)

router.include_router(graphql_router, prefix="/graphql")
