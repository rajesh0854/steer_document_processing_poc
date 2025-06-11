import PyPDF2
import fitz  # PyMuPDF
import pandas as pd
import tabula
import camelot
import pdfplumber
from typing import Dict, List, Any, Optional, Tuple, Union
import re
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
import unicodedata
import cv2
import numpy as np
from PIL import Image
import pytesseract  # OCR for scanned PDFs
import os
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FormField:
    """Enhanced data class to store form field information"""
    name: str
    field_type: str
    value: Any
    is_selected: bool = False
    options: List[str] = field(default_factory=list)
    coordinates: Tuple[float, float, float, float] = None
    page_number: int = 0
    raw_text: str = ""

@dataclass
class TableData:
    """Enhanced data class to store table information"""
    page_number: int
    table_index: int
    headers: List[str]
    rows: List[List[str]]
    coordinates: Tuple[float, float, float, float] = None
    extraction_method: str = ""
    confidence: float = 0.0
    raw_text: str = ""

@dataclass
class TextBlock:
    """Data class for text blocks"""
    text: str
    page_number: int
    coordinates: Tuple[float, float, float, float] = None
    font_info: Dict = field(default_factory=dict)
    is_structured: bool = False

class EnhancedPDFExtractor:
    """
    Comprehensive PDF data extractor with enhanced accuracy for:
    - All text content (including Roman numerals, formulas, special characters)
    - Form fields (checkboxes, radio buttons, text fields)
    - Tables (with multiple extraction methods)
    - Structured and unstructured content
    - OCR support for scanned PDFs
    """
    
    def __init__(self, pdf_path: str, enable_ocr: bool = True):
        self.pdf_path = Path(pdf_path)
        self.enable_ocr = enable_ocr
        self.form_fields = []
        self.tables = []
        self.text_blocks = []
        self.extraction_log = []
        
    def extract_all_data(self) -> Dict[str, Any]:
        """
        Main method to extract ALL data from PDF with enhanced accuracy
        """
        try:
            logger.info(f"Starting extraction from: {self.pdf_path}")
            
            extraction_results = {
                'file_path': str(self.pdf_path),
                'extraction_methods_used': [],
                'has_form_fields': False,
                'has_tables': False,
                'has_text_content': False,
                'is_scanned_pdf': False,
                'total_pages': 0,
                'form_fields': [],
                'selected_checkboxes': [],
                'selected_radio_buttons': [],
                'filled_text_fields': [],
                'tables': [],
                'raw_material_tables': [],
                'all_text_content': [],
                'structured_text': [],
                'formulas_and_equations': [],
                'roman_numerals': [],
                'special_characters': [],
                'extraction_log': [],
                'statistics': {}
            }
            
            # Get basic PDF info
            pdf_info = self._get_pdf_info()
            extraction_results.update(pdf_info)
            
            # Extract using multiple methods for maximum coverage
            methods_results = {}
            
            # Method 1: PyMuPDF (most comprehensive)
            try:
                methods_results['pymupdf'] = self._extract_with_pymupdf()
                extraction_results['extraction_methods_used'].append('PyMuPDF')
            except Exception as e:
                logger.error(f"PyMuPDF extraction failed: {e}")
                self.extraction_log.append(f"PyMuPDF failed: {e}")
            
            # Method 2: PDFPlumber (good for tables and structured text)
            try:
                methods_results['pdfplumber'] = self._extract_with_pdfplumber()
                extraction_results['extraction_methods_used'].append('PDFPlumber')
            except Exception as e:
                logger.error(f"PDFPlumber extraction failed: {e}")
                self.extraction_log.append(f"PDFPlumber failed: {e}")
            
            # Method 3: PyPDF2 (form fields)
            try:
                methods_results['pypdf2'] = self._extract_with_pypdf2()
                extraction_results['extraction_methods_used'].append('PyPDF2')
            except Exception as e:
                logger.error(f"PyPDF2 extraction failed: {e}")
                self.extraction_log.append(f"PyPDF2 failed: {e}")
            
            # Method 4: Tabula and Camelot (tables)
            try:
                methods_results['table_extractors'] = self._extract_tables_comprehensive()
                extraction_results['extraction_methods_used'].append('Table Extractors')
            except Exception as e:
                logger.error(f"Table extraction failed: {e}")
                self.extraction_log.append(f"Table extraction failed: {e}")
            
            # Method 5: OCR if needed
            if self.enable_ocr and self._is_scanned_pdf():
                try:
                    methods_results['ocr'] = self._extract_with_ocr()
                    extraction_results['extraction_methods_used'].append('OCR')
                    extraction_results['is_scanned_pdf'] = True
                except Exception as e:
                    logger.error(f"OCR extraction failed: {e}")
                    self.extraction_log.append(f"OCR failed: {e}")
            
            # Merge and consolidate results
            extraction_results = self._consolidate_results(extraction_results, methods_results)
            
            # Post-process to find specific content types
            extraction_results = self._post_process_content(extraction_results)
            
            # Generate statistics
            extraction_results['statistics'] = self._generate_statistics(extraction_results)
            extraction_results['extraction_log'] = self.extraction_log
            
            logger.info("Extraction completed successfully")
            return extraction_results
            
        except Exception as e:
            logger.error(f"Fatal extraction error: {e}")
            return {'error': f'Failed to extract PDF data: {str(e)}', 'extraction_log': self.extraction_log}
    
    def _get_pdf_info(self) -> Dict[str, Any]:
        """Get basic PDF information"""
        try:
            doc = fitz.open(self.pdf_path)
            info = {
                'total_pages': len(doc),
                'metadata': doc.metadata,
                'is_encrypted': doc.is_encrypted,
                'has_forms': False,
                'has_images': False
            }
            
            # Check for forms and images
            for page_num in range(len(doc)):
                page = doc[page_num]
                if page.widgets():
                    info['has_forms'] = True
                if page.get_images():
                    info['has_images'] = True
            
            doc.close()
            return info
        except Exception as e:
            logger.error(f"Failed to get PDF info: {e}")
            return {'total_pages': 0, 'error': str(e)}
    
    def _extract_with_pymupdf(self) -> Dict[str, Any]:
        """Extract using PyMuPDF with enhanced text handling"""
        results = {
            'text_blocks': [],
            'form_fields': [],
            'images': [],
            'drawings': []
        }
        
        doc = fitz.open(self.pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text with formatting information
            text_dict = page.get_text("dict")
            for block in text_dict["blocks"]:
                if "lines" in block:  # Text block
                    for line in block["lines"]:
                        line_text = ""
                        font_info = {}
                        for span in line["spans"]:
                            line_text += span["text"]
                            font_info = {
                                'font': span.get('font', ''),
                                'size': span.get('size', 0),
                                'flags': span.get('flags', 0),
                                'color': span.get('color', 0)
                            }
                        
                        if line_text.strip():
                            text_block = TextBlock(
                                text=line_text,
                                page_number=page_num + 1,
                                coordinates=(block["bbox"][0], block["bbox"][1], 
                                           block["bbox"][2], block["bbox"][3]),
                                font_info=font_info
                            )
                            results['text_blocks'].append(text_block)
            
            # Extract form fields
            widgets = page.widgets()
            for widget in widgets:
                field_info = self._extract_widget_info_enhanced(widget, page_num)
                if field_info:
                    results['form_fields'].append(field_info)
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = {
                            'page': page_num + 1,
                            'index': img_index,
                            'width': pix.width,
                            'height': pix.height,
                            'xref': xref
                        }
                        results['images'].append(img_data)
                    pix = None
                except Exception as e:
                    logger.warning(f"Failed to process image on page {page_num + 1}: {e}")
        
        doc.close()
        return results
    
    def _extract_with_pdfplumber(self) -> Dict[str, Any]:
        """Extract using PDFPlumber for better table detection"""
        results = {
            'tables': [],
            'text_content': [],
            'characters': []
        }
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract all text
                text = page.extract_text()
                if text:
                    results['text_content'].append({
                        'page': page_num + 1,
                        'text': text,
                        'method': 'pdfplumber'
                    })
                
                # Extract character-level information
                chars = page.chars
                page_chars = []
                for char in chars:
                    page_chars.append({
                        'char': char.get('text', ''),
                        'x0': char.get('x0', 0),
                        'y0': char.get('y0', 0),
                        'x1': char.get('x1', 0),
                        'y1': char.get('y1', 0),
                        'fontname': char.get('fontname', ''),
                        'size': char.get('size', 0)
                    })
                
                if page_chars:
                    results['characters'].append({
                        'page': page_num + 1,
                        'characters': page_chars
                    })
                
                # Extract tables
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:
                        table_data = TableData(
                            page_number=page_num + 1,
                            table_index=table_idx,
                            headers=table[0] if table else [],
                            rows=table[1:] if len(table) > 1 else [],
                            extraction_method='pdfplumber'
                        )
                        results['tables'].append(table_data)
        
        return results
    
    def _extract_with_pypdf2(self) -> Dict[str, Any]:
        """Extract using PyPDF2 for form fields"""
        results = {
            'form_fields': [],
            'text_content': []
        }
        
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                if reader.is_encrypted:
                    logger.warning("PDF is encrypted, skipping PyPDF2 extraction")
                    return results
                
                # Extract text from all pages
                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            results['text_content'].append({
                                'page': page_num + 1,
                                'text': text,
                                'method': 'pypdf2'
                            })
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                
                # Extract form fields
                if '/AcroForm' in reader.trailer.get('/Root', {}):
                    try:
                        fields = reader.get_form_text_fields()
                        if fields:
                            for field_name, field_value in fields.items():
                                form_field = FormField(
                                    name=field_name,
                                    field_type='text',
                                    value=field_value,
                                    is_selected=bool(field_value)
                                )
                                results['form_fields'].append(form_field)
                    except Exception as e:
                        logger.warning(f"Failed to extract form fields: {e}")
        
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
        
        return results
    
    def _extract_tables_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive table extraction using multiple methods"""
        results = {
            'tabula_tables': [],
            'camelot_tables': []
        }
        
        # Tabula extraction
        try:
            tables = tabula.read_pdf(self.pdf_path, pages='all', multiple_tables=True, silent=True)
            for i, table in enumerate(tables):
                if not table.empty:
                    table_data = {
                        'extraction_method': 'tabula',
                        'table_index': i,
                        'headers': table.columns.tolist(),
                        'data': table.values.tolist(),
                        'shape': table.shape,
                        'dataframe': table.to_dict('records')
                    }
                    results['tabula_tables'].append(table_data)
        except Exception as e:
            logger.warning(f"Tabula extraction failed: {e}")
        
        # Camelot extraction
        try:
            tables = camelot.read_pdf(str(self.pdf_path), pages='all')
            for i, table in enumerate(tables):
                if table.df is not None and not table.df.empty:
                    table_data = {
                        'extraction_method': 'camelot',
                        'table_index': i,
                        'page': table.page,
                        'headers': table.df.columns.tolist(),
                        'data': table.df.values.tolist(),
                        'shape': table.df.shape,
                        'dataframe': table.df.to_dict('records'),
                        'accuracy': getattr(table, 'accuracy', 0),
                        'coordinates': getattr(table, '_bbox', None)
                    }
                    results['camelot_tables'].append(table_data)
        except Exception as e:
            logger.warning(f"Camelot extraction failed: {e}")
        
        return results
    
    def _is_scanned_pdf(self) -> bool:
        """Check if PDF is scanned (image-based)"""
        try:
            doc = fitz.open(self.pdf_path)
            total_images = 0
            total_text = 0
            
            for page_num in range(min(3, len(doc))):  # Check first 3 pages
                page = doc[page_num]
                images = page.get_images()
                text = page.get_text().strip()
                
                total_images += len(images)
                total_text += len(text)
            
            doc.close()
            
            # If lots of images but little text, likely scanned
            return total_images > 0 and total_text < 100
            
        except Exception:
            return False
    
    def _extract_with_ocr(self) -> Dict[str, Any]:
        """Extract text using OCR for scanned PDFs"""
        results = {
            'ocr_text': [],
            'ocr_confidence': []
        }
        
        try:
            doc = fitz.open(self.pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                img = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                ocr_result = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                page_text = []
                confidences = []
                
                for i in range(len(ocr_result['text'])):
                    text = ocr_result['text'][i].strip()
                    conf = int(ocr_result['conf'][i])
                    
                    if text and conf > 30:  # Only include text with decent confidence
                        page_text.append(text)
                        confidences.append(conf)
                
                if page_text:
                    results['ocr_text'].append({
                        'page': page_num + 1,
                        'text': ' '.join(page_text),
                        'average_confidence': sum(confidences) / len(confidences)
                    })
            
            doc.close()
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
        
        return results
    
    def _extract_widget_info_enhanced(self, widget, page_num: int) -> Optional[FormField]:
        """Enhanced widget information extraction"""
        try:
            field_name = widget.field_name or f"field_{page_num}_{widget.rect}"
            field_type = widget.field_type_string.lower() if widget.field_type_string else "unknown"
            field_value = widget.field_value
            
            # Enhanced value processing
            if field_value:
                # Handle special characters and encoding
                if isinstance(field_value, str):
                    field_value = unicodedata.normalize('NFKD', field_value)
            
            is_selected = False
            options = []
            
            if field_type in ['checkbox', 'radiobutton']:
                is_selected = bool(field_value)
                if hasattr(widget, 'choice_values') and widget.choice_values:
                    options = widget.choice_values
            elif field_type == 'text':
                is_selected = bool(field_value and str(field_value).strip())
            
            return FormField(
                name=field_name,
                field_type=field_type,
                value=field_value,
                is_selected=is_selected,
                options=options,
                coordinates=(widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1),
                page_number=page_num + 1
            )
            
        except Exception as e:
            logger.warning(f"Failed to extract widget info: {e}")
            return None
    
    def _consolidate_results(self, base_results: Dict, methods_results: Dict) -> Dict:
        """Consolidate results from different extraction methods"""
        
        # Combine text content
        all_text = []
        for method, results in methods_results.items():
            if isinstance(results, dict):
                # Text blocks from PyMuPDF
                if 'text_blocks' in results:
                    for block in results['text_blocks']:
                        all_text.append({
                            'page': block.page_number,
                            'text': block.text,
                            'method': 'pymupdf',
                            'coordinates': block.coordinates,
                            'font_info': block.font_info
                        })
                
                # Text content from other methods
                if 'text_content' in results:
                    all_text.extend(results['text_content'])
                
                # OCR text
                if 'ocr_text' in results:
                    all_text.extend(results['ocr_text'])
        
        base_results['all_text_content'] = all_text
        base_results['has_text_content'] = len(all_text) > 0
        
        # Combine form fields
        all_form_fields = []
        selected_checkboxes = []
        selected_radio_buttons = []
        filled_text_fields = []
        
        for method, results in methods_results.items():
            if isinstance(results, dict) and 'form_fields' in results:
                for field in results['form_fields']:
                    if isinstance(field, FormField):
                        all_form_fields.append(field.__dict__)
                        
                        if field.field_type == 'checkbox' and field.is_selected:
                            selected_checkboxes.append({
                                'name': field.name,
                                'value': field.value,
                                'page': field.page_number,
                                'coordinates': field.coordinates
                            })
                        elif field.field_type == 'radio' and field.is_selected:
                            selected_radio_buttons.append({
                                'name': field.name,
                                'selected_value': field.value,
                                'options': field.options,
                                'page': field.page_number,
                                'coordinates': field.coordinates
                            })
                        elif field.field_type == 'text' and field.value:
                            filled_text_fields.append({
                                'name': field.name,
                                'value': field.value,
                                'page': field.page_number,
                                'coordinates': field.coordinates
                            })
                    elif isinstance(field, dict):
                        all_form_fields.append(field)
        
        base_results['form_fields'] = all_form_fields
        base_results['selected_checkboxes'] = selected_checkboxes
        base_results['selected_radio_buttons'] = selected_radio_buttons
        base_results['filled_text_fields'] = filled_text_fields
        base_results['has_form_fields'] = len(all_form_fields) > 0
        
        # Combine tables
        all_tables = []
        raw_material_tables = []
        
        for method, results in methods_results.items():
            if isinstance(results, dict):
                # Tables from pdfplumber
                if 'tables' in results:
                    for table in results['tables']:
                        if isinstance(table, TableData):
                            table_dict = table.__dict__
                        else:
                            table_dict = table
                        all_tables.append(table_dict)
                
                # Tables from tabula/camelot
                if 'tabula_tables' in results:
                    all_tables.extend(results['tabula_tables'])
                if 'camelot_tables' in results:
                    all_tables.extend(results['camelot_tables'])
        
        # Find raw material tables
        for table in all_tables:
            table_text = ""
            if 'headers' in table:
                table_text += " ".join(str(h) for h in table['headers'])
            if 'data' in table:
                for row in table['data'][:3]:  # Check first few rows
                    table_text += " ".join(str(cell) for cell in row)
            
            if re.search(r'raw\s+material', table_text, re.IGNORECASE):
                raw_material_tables.append(table)
        
        base_results['tables'] = all_tables
        base_results['raw_material_tables'] = raw_material_tables
        base_results['has_tables'] = len(all_tables) > 0
        
        return base_results
    
    def _post_process_content(self, results: Dict) -> Dict:
        """Post-process to identify specific content types"""
        
        # Combine all text for analysis
        all_text = ""
        for text_item in results.get('all_text_content', []):
            all_text += text_item.get('text', '') + " "
        
        # Find Roman numerals
        roman_pattern = r'\b(?=[MDCLXVI])M{0,3}(?:C[MD]|D?C{0,3})?(?:X[CL]|L?X{0,3})?(?:I[XV]|V?I{0,3})?\b'
        roman_numerals = list(set(re.findall(roman_pattern, all_text, re.IGNORECASE)))
        results['roman_numerals'] = roman_numerals
        
        # Find formulas and equations
        formula_patterns = [
            r'[A-Za-z0-9]+\s*[+\-*/=]\s*[A-Za-z0-9]+',  # Basic equations
            r'[A-Za-z]+\d*\s*[\+\-]\s*[A-Za-z]+\d*',     # Chemical formulas
            r'\d+\.\d+\s*[A-Za-z%]+',                     # Percentages/measurements
            r'[A-Za-z]+\(\w+\)',                          # Function notation
        ]
        
        formulas = []
        for pattern in formula_patterns:
            matches = re.findall(pattern, all_text)
            formulas.extend(matches)
        
        results['formulas_and_equations'] = list(set(formulas))
        
        # Find special characters
        special_chars = set()
        for char in all_text:
            if ord(char) > 127:  # Non-ASCII characters
                special_chars.add(char)
        
        results['special_characters'] = list(special_chars)
        
        # Structure text content by type
        structured_text = []
        for text_item in results.get('all_text_content', []):
            text = text_item.get('text', '')
            
            # Classify text type
            text_type = 'general'
            if re.search(r'^\d+\.', text.strip()):
                text_type = 'numbered_list'
            elif re.search(r'^[A-Z][^.]*:$', text.strip()):
                text_type = 'heading'
            elif re.search(r'raw\s+material', text, re.IGNORECASE):
                text_type = 'raw_material'
            elif len(formulas) > 0 and any(formula in text for formula in formulas):
                text_type = 'formula'
            
            structured_item = text_item.copy()
            structured_item['content_type'] = text_type
            structured_text.append(structured_item)
        
        results['structured_text'] = structured_text
        
        return results
    
    def _generate_statistics(self, results: Dict) -> Dict:
        """Generate extraction statistics"""
        stats = {
            'total_pages_processed': results.get('total_pages', 0),
            'extraction_methods_count': len(results.get('extraction_methods_used', [])),
            'total_text_blocks': len(results.get('all_text_content', [])),
            'total_form_fields': len(results.get('form_fields', [])),
            'total_tables': len(results.get('tables', [])),
            'selected_checkboxes_count': len(results.get('selected_checkboxes', [])),
            'selected_radio_buttons_count': len(results.get('selected_radio_buttons', [])),
            'filled_text_fields_count': len(results.get('filled_text_fields', [])),
            'raw_material_tables_count': len(results.get('raw_material_tables', [])),
            'roman_numerals_found': len(results.get('roman_numerals', [])),
            'formulas_found': len(results.get('formulas_and_equations', [])),
            'special_characters_found': len(results.get('special_characters', [])),
            'is_scanned_pdf': results.get('is_scanned_pdf', False)
        }
        
        # Calculate text coverage
        total_chars = sum(len(item.get('text', '')) for item in results.get('all_text_content', []))
        stats['total_characters_extracted'] = total_chars
        
        return stats
    
    def save_results(self, results: Dict, output_path: str = None) -> str:
        """Save extraction results with enhanced formatting"""
        if output_path is None:
            output_path = self.pdf_path.stem + "_comprehensive_extraction"
        
        # Save main results as JSON
        json_path = f"{output_path}.json"
        
        # Create a clean version for JSON (remove non-serializable objects)
        clean_results = self._clean_for_json(results)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save tables as Excel if any exist
        if results.get('tables'):
            excel_path = f"{output_path}_tables.xlsx"
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                for i, table in enumerate(results['tables']):
                    try:
                        if 'dataframe' in table and table['dataframe']:
                            df = pd.DataFrame(table['dataframe'])
                        elif 'data' in table and table['data']:
                            headers = table.get('headers', [f'Col_{j}' for j in range(len(table['data'][0]))])
                            df = pd.DataFrame(table['data'], columns=headers)
                        else:
                            continue
                        
                        sheet_name = f"Table_{i+1}"
                        if len(sheet_name) > 31:  # Excel sheet name limit
                            sheet_name = sheet_name[:31]
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    except Exception as e:
                        logger.warning(f"Failed to save table {i}: {e}")
        
        # Save structured text content
        if results.get('structured_text'):
            text_path = f"{output_path}_text_content.txt"
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write("=== COMPREHENSIVE PDF TEXT EXTRACTION ===\n\n")
                f.write(f"File: {results.get('file_path', 'Unknown')}\n")
                f.write(f"Total Pages: {results.get('total_pages', 0)}\n")
                f.write(f"Extraction Methods: {', '.join(results.get('extraction_methods_used', []))}\n\n")
                
                # Write text content by page
                current_page = 0
                for text_item in results['structured_text']:
                    page = text_item.get('page', 0)
                    content_type = text_item.get('content_type', 'general')
                    text = text_item.get('text', '')
                    method = text_item.get('method', 'unknown')
                    
                    if page != current_page:
                        f.write(f"\n{'='*50}\n")
                        f.write(f"PAGE {page}\n")
                        f.write(f"{'='*50}\n\n")
                        current_page = page
                    
                    f.write(f"[{content_type.upper()}] ({method})\n")
                    f.write(f"{text}\n\n")
                
                # Write special findings
                if results.get('roman_numerals'):
                    f.write(f"\n{'='*50}\n")
                    f.write("ROMAN NUMERALS FOUND\n")
                    f.write(f"{'='*50}\n")
                    f.write(", ".join(results['roman_numerals']))
                    f.write("\n\n")
                
                if results.get('formulas_and_equations'):
                    f.write(f"\n{'='*50}\n")
                    f.write("FORMULAS AND EQUATIONS FOUND\n")
                    f.write(f"{'='*50}\n")
                    for formula in results['formulas_and_equations']:
                        f.write(f"• {formula}\n")
                    f.write("\n")
        
        logger.info(f"Results saved to: {json_path}")
        return json_path
    
    def _clean_for_json(self, obj):
        """Clean object for JSON serialization"""
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._clean_for_json(obj.__dict__)
        elif isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        else:
            return str(obj)

# Enhanced usage function
def extract_pdf_data_comprehensive(pdf_path: str, enable_ocr: bool = True, save_results: bool = True, output_prefix: str = None) -> Dict[str, Any]:
    """
    Comprehensive PDF data extraction function
    
    Args:
        pdf_path (str): Path to the PDF file
        enable_ocr (bool): Enable OCR for scanned PDFs
        save_results (bool): Whether to save results to files
        output_prefix (str): Optional prefix for output files
    
    Returns:
        Dict containing all extracted data with enhanced accuracy
    """
    extractor = EnhancedPDFExtractor(pdf_path, enable_ocr=enable_ocr)
    results = extractor.extract_all_data()
    
    if save_results and 'error' not in results:
        output_file = extractor.save_results(results, output_prefix)
        results['output_files'] = {
            'main_results': output_file,
            'tables': output_file.replace('.json', '_tables.xlsx'),
            'text_content': output_file.replace('.json', '_text_content.txt')
        }
    
    return results

def analyze_extraction_quality(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the quality and completeness of extraction
    """
    quality_report = {
        'extraction_completeness': 'Unknown',
        'data_coverage': {},
        'potential_issues': [],
        'recommendations': []
    }
    
    stats = results.get('statistics', {})
    
    # Assess completeness
    total_pages = stats.get('total_pages_processed', 0)
    text_blocks = stats.get('total_text_blocks', 0)
    methods_used = stats.get('extraction_methods_count', 0)
    
    if total_pages > 0 and text_blocks > 0 and methods_used >= 2:
        quality_report['extraction_completeness'] = 'High'
    elif text_blocks > 0 and methods_used >= 1:
        quality_report['extraction_completeness'] = 'Medium'
    else:
        quality_report['extraction_completeness'] = 'Low'
    
    # Data coverage analysis
    quality_report['data_coverage'] = {
        'has_text': stats.get('total_text_blocks', 0) > 0,
        'has_forms': stats.get('total_form_fields', 0) > 0,
        'has_tables': stats.get('total_tables', 0) > 0,
        'has_special_content': (stats.get('roman_numerals_found', 0) + 
                               stats.get('formulas_found', 0) + 
                               stats.get('special_characters_found', 0)) > 0
    }
    
    # Identify potential issues
    if stats.get('is_scanned_pdf') and not any('OCR' in method for method in results.get('extraction_methods_used', [])):
        quality_report['potential_issues'].append("Scanned PDF detected but OCR not used")
    
    if stats.get('total_characters_extracted', 0) < 100:
        quality_report['potential_issues'].append("Very little text extracted - possible encoding issues")
    
    if stats.get('total_tables', 0) == 0 and 'table' in str(results).lower():
        quality_report['potential_issues'].append("Tables mentioned but none extracted - may need manual review")
    
    # Recommendations
    if quality_report['extraction_completeness'] == 'Low':
        quality_report['recommendations'].append("Try enabling OCR if PDF is scanned")
        quality_report['recommendations'].append("Check if PDF is password protected")
        quality_report['recommendations'].append("Verify PDF is not corrupted")
    
    if not quality_report['data_coverage']['has_special_content']:
        quality_report['recommendations'].append("Review extraction for missing formulas or special characters")
    
    return quality_report

def save_extracted_data_to_json(results: Dict[str, Any], output_path: str) -> None:
    """
    Save extracted data to a JSON file with proper formatting
    
    Args:
        results (Dict[str, Any]): The extracted data
        output_path (str): Path where to save the JSON file
    """
    # Create a clean version of results for JSON serialization
    clean_results = {
        'metadata': {
            'extraction_timestamp': datetime.datetime.now().isoformat(),
            'file_path': results.get('file_path', ''),
            'total_pages': results.get('total_pages', 0),
            'extraction_methods': results.get('extraction_methods_used', []),
            'is_scanned_pdf': results.get('is_scanned_pdf', False)
        },
        'statistics': results.get('statistics', {}),
        'content': {
            'text_blocks': [
                {
                    'page': block.get('page', 0),
                    'text': block.get('text', ''),
                    'coordinates': block.get('coordinates', None),
                    'font_info': block.get('font_info', {})
                }
                for block in results.get('all_text_content', [])
            ],
            'form_fields': {
                'checkboxes': results.get('selected_checkboxes', []),
                'radio_buttons': results.get('selected_radio_buttons', []),
                'text_fields': results.get('filled_text_fields', [])
            },
            'tables': [
                {
                    'page': table.get('page', 0),
                    'extraction_method': table.get('extraction_method', 'unknown'),
                    'headers': table.get('headers', []),
                    'data': table.get('data', []),
                    'coordinates': table.get('coordinates', None)
                }
                for table in results.get('tables', [])
            ],
            'special_content': {
                'roman_numerals': results.get('roman_numerals', []),
                'formulas': results.get('formulas_and_equations', []),
                'special_characters': results.get('special_characters', [])
            }
        },
        'quality_analysis': {
            'completeness': results.get('extraction_completeness', 'Unknown'),
            'potential_issues': results.get('potential_issues', []),
            'recommendations': results.get('recommendations', [])
        },
        'extraction_log': results.get('extraction_log', [])
    }
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to JSON file with proper formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Results saved to: {output_path}")

if __name__ == "__main__":
    import sys
    import os
    from pathlib import Path
    import datetime
    import json

    # 🔧 Hardcoded input values (instead of argparse)
    # Use Path to handle file paths correctly demo_app\backend\sample_docs\EM19335_Quotation_with_material__23.05.2025.pdf
    current_dir = Path(__file__).parent
    sample_docs_dir = current_dir / 'sample_docs'
    pdf_path = str(sample_docs_dir / 'Enquiry form - Gulf Additives (Revised 11112024).pdf')
    # pdf_path = str(sample_docs_dir / 'EM19335_Quotation_with_material__23.05.2025.pdf')
    
    # Debug: Print absolute paths
    print(f"Current directory: {current_dir.absolute()}")
    print(f"Sample docs directory: {sample_docs_dir.absolute()}")
    print(f"PDF path: {Path(pdf_path).absolute()}")
    
    # Verify file exists
    if not os.path.exists(pdf_path):
        print(f"❌ Error: File not found at path: {pdf_path}")
        sys.exit(1)
        
    enable_ocr = True    # Set to False to disable OCR
    save_results = True  # Set to False to skip saving output files
    
    # Create output directory if it doesn't exist
    output_dir = current_dir / 'results'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename based on input PDF name
    pdf_name = Path(pdf_path).stem
    output_json = output_dir / f"{pdf_name}_extracted.json"
    
    try:
        # Extract data
        print(f"Starting comprehensive extraction of: {pdf_path}")
        results = extract_pdf_data_comprehensive(
            pdf_path=pdf_path,
            enable_ocr=enable_ocr,
            save_results=save_results
        )
        
        if 'error' in results:
            print(f"❌ Extraction failed: {results['error']}")
            sys.exit(1)
            
        # Save results to JSON
        save_extracted_data_to_json(results, str(output_json))
        
        # Display summary
        print("\n" + "="*60)
        print("📊 EXTRACTION SUMMARY")
        print("="*60)
        
        stats = results.get('statistics', {})
        print(f"📄 Total Pages: {stats.get('total_pages_processed', 0)}")
        print(f"🔧 Methods Used: {', '.join(results.get('extraction_methods_used', []))}")
        print(f"📝 Text Blocks: {stats.get('total_text_blocks', 0)}")
        print(f"📋 Form Fields: {stats.get('total_form_fields', 0)}")
        print(f"📊 Tables: {stats.get('total_tables', 0)}")
        print(f"🧪 Raw Material Tables: {stats.get('raw_material_tables_count', 0)}")
        print(f"🔢 Roman Numerals: {stats.get('roman_numerals_found', 0)}")
        print(f"🧮 Formulas: {stats.get('formulas_found', 0)}")
        print(f"🌟 Special Characters: {stats.get('special_characters_found', 0)}")
        
        print(f"\n✅ Extraction completed successfully!")
        print(f"📁 Results saved to: {output_json}")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

