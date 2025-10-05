"""
PDF Export Service for generating visual financial reports with charts
"""
import io
import base64
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from sqlalchemy.orm import Session
import pandas as pd

from app.models.entry import Entry
from app.models.category import Category
from app.core.currency import CurrencyService
from app.services.user_preferences import UserPreferencesService


class PDFExportService:
    def __init__(self):
        self.currency_service = CurrencyService()
        self.user_preferences_service = UserPreferencesService()
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    async def export_financial_report_to_pdf(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None,
        report_type: str = "all"
    ) -> io.BytesIO:
        """
        Export comprehensive financial report to PDF with charts
        
        Args:
            db: Database session
            user_id: User ID to filter entries
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            category_id: Category ID for filtering (optional)
            report_type: Type of report ("all", "income", "expense")
        
        Returns:
            BytesIO object containing the PDF file
        """
        # Get user currency
        user_currency = self.user_preferences_service.get_user_currency(db, user_id)
        
        # Build query
        query = db.query(Entry).filter(Entry.user_id == user_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(Entry.date >= start_date)
        if end_date:
            query = query.filter(Entry.date <= end_date)
        
        # Apply category filter
        if category_id:
            query = query.filter(Entry.category_id == category_id)
        
        # Apply type filter
        if report_type in ["income", "expense"]:
            query = query.filter(Entry.type == report_type)
        
        # Get entries with category information
        entries = query.join(Category, Entry.category_id == Category.id).order_by(Entry.date.asc()).all()
        
        # Create PDF buffer
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        normal_style = styles['Normal']
        
        # Build story (content)
        story = []
        
        # Title
        story.append(Paragraph("Financial Report", title_style))
        story.append(Spacer(1, 12))
        
        # Report metadata
        metadata_data = [
            ["Report Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Date Range:", self._format_date_range(start_date, end_date)],
            ["Category:", self._get_category_name(db, category_id)],
            ["Type:", report_type.title() if report_type != "all" else "All Types"],
            ["Currency:", user_currency]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Summary", heading_style))
        
        # Calculate totals
        total_income, total_expense, category_totals = await self._calculate_totals(entries, user_currency)
        net_balance = total_income - total_expense
        
        summary_data = [
            ["Total Income", f"{user_currency} {total_income:,.2f}"],
            ["Total Expense", f"{user_currency} {total_expense:,.2f}"],
            ["Net Balance", f"{user_currency} {net_balance:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('BACKGROUND', (1, 0), (1, -1), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Category breakdown
        if category_totals:
            story.append(Paragraph("Category Breakdown", heading_style))
            
            category_data = [["Category", "Income", "Expense", "Net"]]
            for category_name, totals in sorted(category_totals.items()):
                category_data.append([
                    category_name,
                    f"{user_currency} {totals['income']:,.2f}",
                    f"{user_currency} {totals['expense']:,.2f}",
                    f"{user_currency} {totals['income'] - totals['expense']:,.2f}"
                ])
            
            category_table = Table(category_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            category_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(category_table)
            story.append(Spacer(1, 20))
        
        # Generate and add charts
        if entries:
            # Income vs Expense chart
            if report_type in ["all", "income", "expense"]:
                chart_img = await self._create_income_expense_chart(entries, user_currency)
                if chart_img:
                    story.append(Paragraph("Income vs Expense Overview", heading_style))
                    story.append(Image(chart_img, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 20))
            
            # Category distribution chart
            if len(category_totals) > 1:
                chart_img = self._create_category_chart(category_totals, user_currency)
                if chart_img:
                    story.append(Paragraph("Category Distribution", heading_style))
                    story.append(Image(chart_img, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 20))
            
            # Monthly trend chart
            if len(entries) > 1:
                chart_img = await self._create_monthly_trend_chart(entries, user_currency)
                if chart_img:
                    story.append(Paragraph("Monthly Trend", heading_style))
                    story.append(Image(chart_img, width=6*inch, height=4*inch))
                    story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)
        
        return pdf_buffer
    
    def _format_date_range(self, start_date: Optional[date], end_date: Optional[date]) -> str:
        """Format date range for display"""
        if start_date and end_date:
            return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        elif start_date:
            return f"From {start_date.strftime('%Y-%m-%d')}"
        elif end_date:
            return f"Until {end_date.strftime('%Y-%m-%d')}"
        else:
            return "All time"
    
    def _get_category_name(self, db: Session, category_id: Optional[int]) -> str:
        """Get category name by ID"""
        if category_id:
            category = db.query(Category).filter(Category.id == category_id).first()
            return category.name if category else "Unknown"
        return "All Categories"
    
    async def _calculate_totals(self, entries: List[Entry], user_currency: str) -> tuple:
        """Calculate totals from entries"""
        total_income = 0
        total_expense = 0
        category_totals = {}
        
        for entry in entries:
            converted_amount = await self.currency_service.convert_amount(
                entry.amount, entry.currency, user_currency
            )
            
            category_name = entry.category.name
            if category_name not in category_totals:
                category_totals[category_name] = {"income": 0, "expense": 0}
            
            if entry.type.lower() == "income":
                total_income += converted_amount
                category_totals[category_name]["income"] += converted_amount
            else:
                total_expense += converted_amount
                category_totals[category_name]["expense"] += converted_amount
        
        return total_income, total_expense, category_totals
    
    async def _create_income_expense_chart(self, entries: List[Entry], user_currency: str) -> Optional[io.BytesIO]:
        """Create income vs expense pie chart"""
        try:
            total_income = 0
            total_expense = 0
            
            for entry in entries:
                converted_amount = await self.currency_service.convert_amount(
                    entry.amount, entry.currency, user_currency
                )
                
                if entry.type.lower() == "income":
                    total_income += converted_amount
                else:
                    total_expense += converted_amount
            
            if total_income == 0 and total_expense == 0:
                return None
            
            # Create pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            
            labels = []
            sizes = []
            colors_list = []
            
            if total_income > 0:
                labels.append(f"Income\n({user_currency} {total_income:,.2f})")
                sizes.append(total_income)
                colors_list.append('#2E8B57')  # Sea Green
            
            if total_expense > 0:
                labels.append(f"Expense\n({user_currency} {total_expense:,.2f})")
                sizes.append(total_expense)
                colors_list.append('#DC143C')  # Crimson
            
            ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
            ax.set_title('Income vs Expense Distribution', fontsize=14, fontweight='bold')
            
            # Save to BytesIO
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            print(f"Error creating income/expense chart: {e}")
            return None
    
    def _create_category_chart(self, category_totals: Dict[str, Dict[str, float]], user_currency: str) -> Optional[io.BytesIO]:
        """Create category distribution chart"""
        try:
            if not category_totals:
                return None
            
            # Prepare data
            categories = list(category_totals.keys())
            income_values = [category_totals[cat]["income"] for cat in categories]
            expense_values = [category_totals[cat]["expense"] for cat in categories]
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            
            x = range(len(categories))
            width = 0.35
            
            bars1 = ax.bar([i - width/2 for i in x], income_values, width, label='Income', color='#2E8B57')
            bars2 = ax.bar([i + width/2 for i in x], expense_values, width, label='Expense', color='#DC143C')
            
            ax.set_xlabel('Categories')
            ax.set_ylabel(f'Amount ({user_currency})')
            ax.set_title('Income and Expense by Category', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Add value labels on bars
            for bar in bars1:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:,.0f}',
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 3),
                              textcoords="offset points",
                              ha='center', va='bottom', fontsize=8)
            
            for bar in bars2:
                height = bar.get_height()
                if height > 0:
                    ax.annotate(f'{height:,.0f}',
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 3),
                              textcoords="offset points",
                              ha='center', va='bottom', fontsize=8)
            
            plt.tight_layout()
            
            # Save to BytesIO
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            print(f"Error creating category chart: {e}")
            return None
    
    async def _create_monthly_trend_chart(self, entries: List[Entry], user_currency: str) -> Optional[io.BytesIO]:
        """Create monthly trend chart"""
        try:
            if len(entries) < 2:
                return None
            
            # Prepare data
            df_data = []
            for entry in entries:
                converted_amount = await self.currency_service.convert_amount(
                    entry.amount, entry.currency, user_currency
                )
                df_data.append({
                    'date': entry.date,
                    'type': entry.type,
                    'amount': converted_amount
                })
            
            df = pd.DataFrame(df_data)
            df['month'] = df['date'].dt.to_period('M')
            
            # Group by month and type
            monthly_data = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
            
            if monthly_data.empty:
                return None
            
            # Create line chart
            fig, ax = plt.subplots(figsize=(12, 6))
            
            if 'income' in monthly_data.columns:
                ax.plot(monthly_data.index.astype(str), monthly_data['income'], 
                       marker='o', linewidth=2, label='Income', color='#2E8B57')
            
            if 'expense' in monthly_data.columns:
                ax.plot(monthly_data.index.astype(str), monthly_data['expense'], 
                       marker='s', linewidth=2, label='Expense', color='#DC143C')
            
            ax.set_xlabel('Month')
            ax.set_ylabel(f'Amount ({user_currency})')
            ax.set_title('Monthly Income and Expense Trend', fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Rotate x-axis labels
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Save to BytesIO
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer
            
        except Exception as e:
            print(f"Error creating monthly trend chart: {e}")
            return None
