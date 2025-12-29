"""Report Templates API Endpoints - Phase 2.1"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.deps import current_user
from app.models.user import User
from app.services.report_template_service import ReportTemplateService


router = APIRouter(prefix="/api/report-templates", tags=["Report Templates"])


# Request/Response Models
class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: str = Field(..., pattern="^(expense|income|comprehensive)$")
    category_id: Optional[int] = None
    date_range_type: str = Field(default='custom')
    custom_days: Optional[int] = None
    filters: Optional[dict] = None
    default_export_format: str = Field(default='excel', pattern="^(excel|pdf)$")
    is_favorite: bool = False


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    report_type: Optional[str] = Field(None, pattern="^(expense|income|comprehensive)$")
    category_id: Optional[int] = None
    date_range_type: Optional[str] = None
    custom_days: Optional[int] = None
    filters: Optional[dict] = None
    default_export_format: Optional[str] = Field(None, pattern="^(excel|pdf)$")
    is_favorite: Optional[bool] = None


# ===== CRUD ENDPOINTS =====

@router.post("/")
async def create_template(
    template_data: TemplateCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Create a new report template"""
    try:
        service = ReportTemplateService(db)

        template = service.create_template(
            user_id=user.id,
            name=template_data.name,
            description=template_data.description,
            report_type=template_data.report_type,
            category_id=template_data.category_id,
            date_range_type=template_data.date_range_type,
            custom_days=template_data.custom_days,
            filters=template_data.filters,
            default_export_format=template_data.default_export_format,
            is_favorite=template_data.is_favorite
        )

        return JSONResponse({
            'success': True,
            'message': 'Template saved successfully',
            'template': {
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'report_type': template.report_type,
                'category_id': template.category_id,
                'category_name': template.category.name if template.category else None,
                'date_range_type': template.date_range_type,
                'custom_days': template.custom_days,
                'filters': template.filters,
                'default_export_format': template.default_export_format,
                'is_favorite': template.is_favorite,
                'use_count': template.use_count,
                'created_at': template.created_at.isoformat() if template.created_at else None
            }
        })

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def get_templates(
    favorites_only: bool = False,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get all templates for current user"""
    service = ReportTemplateService(db)
    templates = service.get_user_templates(user.id, favorites_only=favorites_only)

    return JSONResponse({
        'success': True,
        'templates': [
            {
                'id': t.id,
                'name': t.name,
                'description': t.description,
                'report_type': t.report_type,
                'category_id': t.category_id,
                'category_name': t.category.name if t.category else None,
                'date_range_type': t.date_range_type,
                'custom_days': t.custom_days,
                'filters': t.filters,
                'default_export_format': t.default_export_format,
                'is_favorite': t.is_favorite,
                'use_count': t.use_count,
                'last_used_at': t.last_used_at.isoformat() if t.last_used_at else None,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'updated_at': t.updated_at.isoformat() if t.updated_at else None
            }
            for t in templates
        ],
        'total': len(templates)
    })


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Get a specific template"""
    service = ReportTemplateService(db)
    template = service.get_template(template_id, user.id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return JSONResponse({
        'success': True,
        'template': {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'report_type': template.report_type,
            'category_id': template.category_id,
            'category_name': template.category.name if template.category else None,
            'date_range_type': template.date_range_type,
            'custom_days': template.custom_days,
            'filters': template.filters,
            'default_export_format': template.default_export_format,
            'is_favorite': template.is_favorite,
            'use_count': template.use_count,
            'last_used_at': template.last_used_at.isoformat() if template.last_used_at else None,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        }
    })


@router.put("/{template_id}")
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Update a template"""
    service = ReportTemplateService(db)

    # Only include non-None fields
    updates = {k: v for k, v in template_data.dict().items() if v is not None}

    template = service.update_template(template_id, user.id, **updates)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return JSONResponse({
        'success': True,
        'message': 'Template updated successfully',
        'template': {
            'id': template.id,
            'name': template.name,
            'is_favorite': template.is_favorite
        }
    })


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Delete a template"""
    service = ReportTemplateService(db)
    success = service.delete_template(template_id, user.id)

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")

    return JSONResponse({
        'success': True,
        'message': 'Template deleted successfully'
    })


@router.post("/{template_id}/use")
async def mark_template_used(
    template_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Mark template as used"""
    service = ReportTemplateService(db)
    template = service.mark_as_used(template_id, user.id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return JSONResponse({
        'success': True,
        'use_count': template.use_count
    })


@router.post("/{template_id}/toggle-favorite")
async def toggle_favorite(
    template_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    """Toggle template favorite status"""
    service = ReportTemplateService(db)
    template = service.toggle_favorite(template_id, user.id)

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return JSONResponse({
        'success': True,
        'message': f"Template {'added to' if template.is_favorite else 'removed from'} favorites",
        'is_favorite': template.is_favorite
    })
