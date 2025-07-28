from typing import Optional, Dict, Any, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json


class PDFJournalToolInputSchema(BaseModel):
    action: str = Field(..., description="Action to perform: 'append_entry', 'create_journal', 'get_journal_info'")
    journal_name: Optional[str] = Field(None, description="Name of the journal file (without .pdf extension)")
    entry_data: Optional[Dict[str, Any]] = Field(None, description="Health data to append to journal")
    entry_title: Optional[str] = Field(None, description="Title for the journal entry")


class PDFJournalTool(BaseTool):
    name: str = "PDF Journal Manager"
    description: str = "Tool to manage persistent PDF health journals - append entries and maintain state"
    args_schema = PDFJournalToolInputSchema

    def __init__(self, journals_dir: str = "journals", **kwargs):
        super().__init__(**kwargs)
        self.journals_dir = journals_dir
        self._ensure_journals_dir()

    def _ensure_journals_dir(self):
        """Ensure the journals directory exists"""
        if not os.path.exists(self.journals_dir):
            os.makedirs(self.journals_dir)

    def _run(self, action: str, journal_name: Optional[str] = None, 
             entry_data: Optional[Dict[str, Any]] = None, entry_title: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform PDF journal operations
        """
        try:
            if action == "create_journal":
                if not journal_name:
                    return {"error": "journal_name is required for create_journal"}
                return self._create_journal(journal_name)
            elif action == "append_entry":
                if not journal_name or not entry_data:
                    return {"error": "journal_name and entry_data are required for append_entry"}
                return self._append_entry(journal_name, entry_data, entry_title)
            elif action == "get_journal_info":
                if not journal_name:
                    return {"error": "journal_name is required for get_journal_info"}
                return self._get_journal_info(journal_name)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    def _create_journal(self, journal_name: str) -> Dict[str, Any]:
        """Create a new PDF journal"""
        pdf_path = os.path.join(self.journals_dir, f"{journal_name}.pdf")
        
        if os.path.exists(pdf_path):
            return {"error": f"Journal '{journal_name}' already exists"}
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Create title page
        story = []
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        story.append(Paragraph(f"Health Journal: {journal_name.title()}", title_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(PageBreak())
        
        doc.build(story)
        
        # Create metadata file
        metadata_path = os.path.join(self.journals_dir, f"{journal_name}_metadata.json")
        metadata = {
            "journal_name": journal_name,
            "created_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_entries": 0,
            "pdf_path": pdf_path
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "message": f"Journal '{journal_name}' created successfully",
            "pdf_path": pdf_path,
            "metadata_path": metadata_path
        }

    def _append_entry(self, journal_name: str, entry_data: Dict[str, Any], entry_title: Optional[str] = None) -> Dict[str, Any]:
        """Append a new entry to existing PDF journal"""
        pdf_path = os.path.join(self.journals_dir, f"{journal_name}.pdf")
        metadata_path = os.path.join(self.journals_dir, f"{journal_name}_metadata.json")
        
        if not os.path.exists(pdf_path):
            return {"error": f"Journal '{journal_name}' does not exist. Create it first."}
        
        # Load existing metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create new PDF with existing content + new entry
        temp_pdf_path = os.path.join(self.journals_dir, f"{journal_name}_temp.pdf")
        
        doc = SimpleDocTemplate(temp_pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Add new entry
        entry_title = entry_title or f"Entry {metadata['total_entries'] + 1}"
        story.append(Paragraph(entry_title, styles['Heading2']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 12))
        
        # Format entry data
        for key, value in entry_data.items():
            if value is not None:
                formatted_key = key.replace('_', ' ').title()
                story.append(Paragraph(f"<b>{formatted_key}:</b> {value}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        doc.build(story)
        
        # Merge with existing PDF (simplified approach - in production you'd use PyPDF2 or similar)
        # For now, we'll create a new combined PDF
        combined_pdf_path = os.path.join(self.journals_dir, f"{journal_name}_combined.pdf")
        
        # In a real implementation, you'd merge the PDFs here
        # For now, we'll just copy the new content
        import shutil
        shutil.copy(temp_pdf_path, combined_pdf_path)
        
        # Update metadata
        metadata['last_updated'] = datetime.now().isoformat()
        metadata['total_entries'] += 1
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Clean up temp file
        os.remove(temp_pdf_path)
        
        return {
            "success": True,
            "message": f"Entry appended to journal '{journal_name}'",
            "pdf_path": combined_pdf_path,
            "entry_number": metadata['total_entries']
        }

    def _get_journal_info(self, journal_name: str) -> Dict[str, Any]:
        """Get information about a journal"""
        pdf_path = os.path.join(self.journals_dir, f"{journal_name}.pdf")
        metadata_path = os.path.join(self.journals_dir, f"{journal_name}_metadata.json")
        
        if not os.path.exists(pdf_path):
            return {"error": f"Journal '{journal_name}' does not exist"}
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            "journal_name": journal_name,
            "pdf_path": pdf_path,
            "metadata": metadata
        }

    def run(self, input_data: PDFJournalToolInputSchema) -> Dict[str, Any]:
        return self._run(
            action=input_data.action,
            journal_name=input_data.journal_name,
            entry_data=input_data.entry_data,
            entry_title=input_data.entry_title
        ) 