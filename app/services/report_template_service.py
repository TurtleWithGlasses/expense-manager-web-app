"""Report Template Service - Phase 2.1"""
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.report_template import ReportTemplate


class ReportTemplateService:
    """Service for managing custom report templates"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        user_id: int,
        name: str,
        report_type: str,
        description: str = None,
        date_range_type: str = 'custom',
        custom_days: int = None,
        filters: Dict = None,
        default_export_format: str = 'excel',
        is_favorite: bool = False
    ) -> ReportTemplate:
        """Create a new report template"""
        template = ReportTemplate(
            user_id=user_id,
            name=name,
            description=description,
            report_type=report_type,
            date_range_type=date_range_type,
            custom_days=custom_days,
            filters=filters or {},
            default_export_format=default_export_format,
            is_favorite=is_favorite
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)

        return template

    def get_user_templates(
        self,
        user_id: int,
        favorites_only: bool = False
    ) -> List[ReportTemplate]:
        """Get all templates for a user"""
        query = self.db.query(ReportTemplate).filter(
            ReportTemplate.user_id == user_id
        )

        if favorites_only:
            query = query.filter(ReportTemplate.is_favorite == True)

        return query.order_by(
            desc(ReportTemplate.is_favorite),
            desc(ReportTemplate.last_used_at),
            desc(ReportTemplate.created_at)
        ).all()

    def get_template(self, template_id: int, user_id: int) -> Optional[ReportTemplate]:
        """Get a specific template"""
        return self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id,
            ReportTemplate.user_id == user_id
        ).first()

    def update_template(
        self,
        template_id: int,
        user_id: int,
        **updates
    ) -> Optional[ReportTemplate]:
        """Update a template"""
        template = self.get_template(template_id, user_id)
        if not template:
            return None

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(template)

        return template

    def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a template"""
        template = self.get_template(template_id, user_id)
        if not template:
            return False

        self.db.delete(template)
        self.db.commit()
        return True

    def mark_as_used(self, template_id: int, user_id: int) -> Optional[ReportTemplate]:
        """Mark template as used (increment use count and update last used)"""
        template = self.get_template(template_id, user_id)
        if not template:
            return None

        template.use_count += 1
        template.last_used_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(template)

        return template

    def toggle_favorite(self, template_id: int, user_id: int) -> Optional[ReportTemplate]:
        """Toggle favorite status"""
        template = self.get_template(template_id, user_id)
        if not template:
            return None

        template.is_favorite = not template.is_favorite
        template.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(template)

        return template
