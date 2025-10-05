"""
Reports API endpoints for Excel and PDF export functionality
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.deps import current_user
from app.db.session import get_db
from app.services.excel_export import ExcelExportService
from app.services.pdf_export import PDFExportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/excel/entries")
async def export_entries_excel(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Category ID"),
    report_type: str = Query("all", description="Report type: all, income, or expense"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Export entries to Excel format with detailed information
    """
    # Parse date parameters
    start_date = None
    end_date = None
    if start:
        start_date = date.fromisoformat(start)
    if end:
        end_date = date.fromisoformat(end)
    
    # Parse category parameter
    category_id = None
    if category and category.strip():
        try:
            category_id = int(category)
        except ValueError:
            category_id = None
    
    # Generate Excel report
    excel_service = ExcelExportService()
    excel_buffer = await excel_service.export_entries_to_excel(
        db=db,
        user_id=user.id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        report_type=report_type
    )
    
    # Generate filename
    filename_parts = ["financial_report"]
    if start_date:
        filename_parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    if end_date:
        filename_parts.append(f"to_{end_date.strftime('%Y%m%d')}")
    if category_id:
        filename_parts.append(f"category_{category_id}")
    if report_type != "all":
        filename_parts.append(report_type)
    
    filename = "_".join(filename_parts) + ".xlsx"
    
    return StreamingResponse(
        io=excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/excel/categories")
async def export_categories_excel(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Export category summary to Excel format
    """
    # Parse date parameters
    start_date = None
    end_date = None
    if start:
        start_date = date.fromisoformat(start)
    if end:
        end_date = date.fromisoformat(end)
    
    # Generate Excel report
    excel_service = ExcelExportService()
    excel_buffer = await excel_service.export_category_summary_to_excel(
        db=db,
        user_id=user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Generate filename
    filename_parts = ["category_summary"]
    if start_date:
        filename_parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    if end_date:
        filename_parts.append(f"to_{end_date.strftime('%Y%m%d')}")
    
    filename = "_".join(filename_parts) + ".xlsx"
    
    return StreamingResponse(
        io=excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/pdf/financial")
async def export_financial_pdf(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Category ID"),
    report_type: str = Query("all", description="Report type: all, income, or expense"),
    user=Depends(current_user),
    db: Session = Depends(get_db),
):
    """
    Export comprehensive financial report to PDF with charts
    """
    # Parse date parameters
    start_date = None
    end_date = None
    if start:
        start_date = date.fromisoformat(start)
    if end:
        end_date = date.fromisoformat(end)
    
    # Parse category parameter
    category_id = None
    if category and category.strip():
        try:
            category_id = int(category)
        except ValueError:
            category_id = None
    
    # Generate PDF report
    pdf_service = PDFExportService()
    pdf_buffer = await pdf_service.export_financial_report_to_pdf(
        db=db,
        user_id=user.id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        report_type=report_type
    )
    
    # Generate filename
    filename_parts = ["financial_report"]
    if start_date:
        filename_parts.append(f"from_{start_date.strftime('%Y%m%d')}")
    if end_date:
        filename_parts.append(f"to_{end_date.strftime('%Y%m%d')}")
    if category_id:
        filename_parts.append(f"category_{category_id}")
    if report_type != "all":
        filename_parts.append(report_type)
    
    filename = "_".join(filename_parts) + ".pdf"
    
    return StreamingResponse(
        io=pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
