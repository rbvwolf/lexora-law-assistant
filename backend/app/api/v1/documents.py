from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentGenerateResponse,
    TemplateListResponse,
)
from app.services.doc_service import doc_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/templates", response_model=TemplateListResponse)
async def get_templates() -> TemplateListResponse:
    """Return active legal document templates and their expected field schemas."""
    templates = doc_service.list_templates()
    return TemplateListResponse(templates=templates)


@router.post("/generate", response_model=DocumentGenerateResponse)
async def generate_document(request: DocumentGenerateRequest) -> DocumentGenerateResponse:
    """Generate both .docx and .pdf files in parallel from unified data model.

    Direct PII is injected straight into doc_service, completely bypassing the LLM.
    """
    template = doc_service.get_template(request.template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "TEMPLATE_NOT_FOUND", "message": f"Template '{request.template_id}' bulunamadı."},
        )

    file_id, docx_url, pdf_url, expires_at = await doc_service.generate_documents(
        template_id=request.template_id,
        case_params=request.case_params,
        pii=request.pii,
    )

    return DocumentGenerateResponse(
        file_id=file_id,
        docx_url=docx_url,
        pdf_url=pdf_url,
        expires_at=expires_at,
    )


@router.get("/download/{file_id}")
async def download_document(file_id: str):
    """Serve generated .docx or .pdf file from temporary storage."""
    file_path = doc_service.resolve_download_path(file_id)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "FILE_EXPIRED_OR_NOT_FOUND", "message": "İstenen dosya bulunamadı veya süresi doldu."},
        )

    media_type = "application/pdf" if file_id.endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path=file_path, filename=file_path.name, media_type=media_type)
