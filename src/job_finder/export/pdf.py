from __future__ import annotations

from pathlib import Path
import re

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors


def _parse_markdown_to_content(md_content: str) -> list:
    """Parse markdown content into reportlab platypus elements."""
    from reportlab.platypus import Paragraph, Spacer, PageBreak
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        fontName='Helvetica-Bold',
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2e5a8c'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold',
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
        spaceAfter=4,
    )
    
    link_style = ParagraphStyle(
        'Link',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.blue,
        spaceAfter=2,
    )
    
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip empty lines
        if not line.strip():
            i += 1
            continue
        
        # Check for main title (# heading)
        if line.startswith('# '):
            title_text = line[2:].strip()
            elements.append(Paragraph(title_text, title_style))
            elements.append(Spacer(1, 0.1 * inch))
            i += 1
            continue
        
        # Check for job number heading (## heading)
        if line.startswith('## '):
            heading_text = line[3:].strip()
            elements.append(Spacer(1, 0.08 * inch))
            elements.append(Paragraph(heading_text, heading_style))
            i += 1
            continue
        
        # Check for bullet points (- text)
        if line.startswith('- '):
            bullet_text = line[2:].strip()
            # Format as indented paragraph with bullet
            elements.append(Paragraph(f"• {bullet_text}", body_style))
            i += 1
            continue
        
        # Regular paragraph
        if line.strip():
            elements.append(Paragraph(line.strip(), body_style))
        
        i += 1
    
    return elements


def export_markdown_to_pdf(md_file: Path, pdf_file: Path) -> None:
    """Convert a markdown file to PDF."""
    if not md_file.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_file}")
    
    # Read markdown content
    md_content = md_file.read_text(encoding='utf-8')
    
    # Parse markdown to reportlab elements
    elements = _parse_markdown_to_content(md_content)
    
    # Create PDF
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=A4,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    
    # Build PDF
    doc.build(elements)


def export_shortlists_to_pdf(data_dir: Path) -> dict[str, Path]:
    """Convert all markdown shortlists in a directory to PDF."""
    data_dir = Path(data_dir)
    pdf_files = {}
    
    # Find all shortlist markdown files
    for md_file in sorted(data_dir.glob('shortlist_*.md')):
        pdf_file = md_file.with_suffix('.pdf')
        try:
            export_markdown_to_pdf(md_file, pdf_file)
            pdf_files[md_file.stem] = pdf_file
        except Exception as e:
            print(f"Error converting {md_file} to PDF: {e}")
    
    # Also convert main shortlist.md if it exists
    main_shortlist = data_dir / 'shortlist.md'
    if main_shortlist.exists():
        pdf_file = main_shortlist.with_suffix('.pdf')
        try:
            export_markdown_to_pdf(main_shortlist, pdf_file)
            pdf_files['shortlist'] = pdf_file
        except Exception as e:
            print(f"Error converting {main_shortlist} to PDF: {e}")
    
    return pdf_files
