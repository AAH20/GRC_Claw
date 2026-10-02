"""Document management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from onboarding_automator.agents import DocumentCollectorAgent
from onboarding_automator.integrations.store import InMemoryStore
from onboarding_automator.models import AgentResponse, Document, DocumentCreate, DocumentUpdate

__all__ = ["router"]

router = APIRouter()


def get_store(request: Request) -> InMemoryStore:
    """Dependency to get the in-memory store from app state."""
    return request.app.state.store


@router.post("", response_model=Document, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_data: DocumentCreate,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Document:
    """Register a new document for an onboarding plan.

    Args:
        doc_data: The document creation data.

    Returns:
        The newly created document record.
    """
    document = Document(
        plan_id=doc_data.plan_id,
        task_id=doc_data.task_id,
        name=doc_data.name,
        document_type=doc_data.document_type,
        metadata=doc_data.metadata,
    )
    await store.save_document(document)

    # Add document to parent plan
    plan = await store.get_plan(doc_data.plan_id)
    if plan:
        plan.documents.append(document.id)
        await store.save_plan(plan)

    return document


@router.get("", response_model=list[Document])
async def list_documents(
    store: InMemoryStore = Depends(get_store)  # noqa: B008
    plan_id: UUID | None = None,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Document]:
    """List documents with optional filtering.

    Args:
        plan_id: Filter by parent plan ID.
        status_filter: Filter by document status.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        List of matching documents.
    """
    documents = await store.list_documents(plan_id=plan_id)
    if status_filter:
        documents = [d for d in documents if d.status.value == status_filter]
    return documents[skip : skip + limit]


@router.get("/{document_id}", response_model=Document)
async def get_document(
    document_id: UUID,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Document:
    """Get a specific document by ID.

    Args:
        document_id: The document's unique identifier.

    Returns:
        The requested document.

    Raises:
        HTTPException: If the document is not found.
    """
    document = await store.get_document(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )
    return document


@router.patch("/{document_id}", response_model=Document)
async def update_document(
    document_id: UUID,
    update_data: DocumentUpdate,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> Document:
    """Update document status and metadata.

    Args:
        document_id: The document's unique identifier.
        update_data: The fields to update.

    Returns:
        The updated document.

    Raises:
        HTTPException: If the document is not found.
    """
    document = await store.get_document(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    if update_data.status is not None:
        document.status = update_data.status
    if update_data.rejection_reason is not None:
        document.rejection_reason = update_data.rejection_reason
    if update_data.metadata is not None:
        document.metadata.update(update_data.metadata)

    from datetime import datetime

    document.updated_at = datetime.utcnow()
    await store.save_document(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> None:
    """Delete a document.

    Args:
        document_id: The document's unique identifier.

    Raises:
        HTTPException: If the document is not found.
    """
    deleted = await store.delete_document(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )


@router.post("/{document_id}/verify", response_model=AgentResponse)
async def verify_document(
    document_id: UUID,
    request: Request,
    store: InMemoryStore = Depends(get_store)  # noqa: B008
) -> AgentResponse:
    """Trigger document verification via the DocumentCollectorAgent.

    Args:
        document_id: The document's unique identifier.
        request: The incoming request.

    Returns:
        AgentResponse with the verification result.

    Raises:
        HTTPException: If the document is not found.
    """
    document = await store.get_document(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found",
        )

    agent = DocumentCollectorAgent(request.app.state.settings)
    return await agent.verify_document(document)
