from google.generativeai.types import HarmCategory, HarmBlockThreshold, content_types
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gemini_config = {
    "temperature": 1.5,
    "top_p": 0.98,
    "top_k": 20,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
gemini_api_key = os.getenv('GEMINI_API_KEY')

# Extraction prompt for manufacturing documents
# EXTRACTION_PROMPT = """
# You are an expert data extraction assistant specialized in processing manufacturing industry quotation and enquiry forms from PDF documents.
# the document contains tables, different types of checkboxes, radio buttons, input fields, and text fields. make sure to understand and extract the data from the document.

# Please extract the following information from this PDF document:

# FIELD DEFINITIONS:
# {field_definitions}

# INSTRUCTIONS:
# - Analyze the PDF content carefully
# - Extract data for each field as defined
# - Return the result as a JSON object with field names as keys
# - If a field cannot be found or is unclear, set its value to null
# - Ensure the JSON is properly formatted and valid
# - For numerical values, extract only numbers without currency symbols or units unless specified
# - For dates, use ISO format (YYYY-MM-DD) when possible
# - For text fields, extract exact text as it appears in the document
# - For a field if the values are a list of checkboxes or radio buttons, carefully extract the value which is checked or selected. do not extract the values if the checkbox is not checked or the radio button is not selected.

# This is a manufacturing industry document (quotation/enquiry form). 
# Pay special attention to:
# 1. Part numbers and specifications
# 2. Quantities and units of measurement
# 3. Pricing information
# 4. Delivery dates and terms
# 5. Supplier/customer information
# 6. Technical specifications
# 7. Material specifications
# 8. Manufacturing processes mentioned
# 9. checkboxes and radio buttons (if the checkbox is checked, set the value to true, if the checkbox is not checked, set the value to false)
# 10. input fields
# 11. tables
# 12. text fields
# 13. date fields
# 14. number fields
# 15. email fields
# 16. phone number fields

# Please return only the JSON object with the extracted data:
# """

EXTRACTION_PROMPT = """
# Manufacturing Form Data Extraction Assistant
 
You are an expert data extraction assistant specialized in processing manufacturing industry quotation and enquiry forms from PDF documents. The document contains tables, checkboxes, radio buttons, input fields, text fields, and filled-in data.
 
## FIELD DEFINITIONS:
{field_definitions}

## EXTRACTION RULES:
 
### 1. SELECTION IDENTIFICATION:
**SELECTED/CHECKED (Extract these):**
- ☑ (checked box)
- ⬛ (filled/black box)
- ✓ (check mark)
- ✗ (cross mark)
- ● (filled radio button)
- ⚫ (filled circle)
- Any filled, darkened, or marked box/circle
- Hand-written marks in boxes
 
**NOT SELECTED (Ignore these):**
- ☐ (empty checkbox)
- ○ (empty radio button)
- ◯ (empty circle)
- Blank squares or circles
- No markings
 
### 2. INPUT FIELD IDENTIFICATION:
**FILLED FIELDS (Extract these):**
- Numbers written in blanks: "Min 25 % Max 55 %"
- Text in underlined spaces: "Website: Gulf Additives.com"
- Values in form fields: "440 Voltage 50 Hz"
- Table data with entries
- Any handwritten or typed content in input areas
 
**EMPTY FIELDS (Ignore these):**
- Blank underlines: "______"
- Empty table cells
- No filled content
1. **Find the "Applicaon details" section**
2. **Look for exact field labels** (including typos):
   - "End Applicaon details:"
   - "End product usage:"
   - "End product form:"
   - "End product tesng method:" (note: "tesng" typo)
   - "Bench mark available:"
   - "Lab trial required:"
   - "Willing to send sample along with MSDS to specified locaon:"
   - "If yes, please specify locaon for the lab trial:"
 
### 5. EXTRACTION LOGIC:
- **Single checkbox/radio checked:** Return the option as string
- **Multiple checkboxes checked:** Return array of options
- **Filled input fields:** Extract the actual values/text
- **Table data:** Extract as structured data
- **No checkboxes checked:** Return null
- **Empty input fields:** Return null
- **Field not found:** Return null
 
### 4. COMMON ISSUES TO AVOID:
- Don't extract from empty checkboxes ☐
- Don't assume defaults
- Don't extract option labels unless actually selected
- Check for typos in field names (like "tesng" instead of "testing")
 
## STEP-BY-STEP PROCESS:
 
1. **Locate Application details section**
2. **For each field, find the exact label**
3. **Check which checkboxes are marked**
4. **Extract only marked options**
5. **Return null if nothing is marked**
 
## OUTPUT FORMAT:
 
Return ONLY valid JSON:
 
```json
{
  "industrial_application": null,
  "end_product_usage": null,
  "end_product_form": null,
  "bench_mark": null,
  "end_product_test_method": null,
  "lab_trial": null,
  "willing_to_send_sample": null,
  "lab_trial_location": null
}
```
 
## EXAMPLES:
 
**Example 1 - Checkbox selection:**
If you see: "☐ ASTM ⬛ ISO ☐ Will be provided before contract"
Output: `"end_product_test_method": ["ISO"]`
 
**Example 2 - Radio button:**
If you see: "3 Phase, 1 neutral: ● Yes ○ No"
Output: `"three_phase_neutral": "Yes"`
 
**Example 3 - Filled input fields:**
If you see: "Relative humidity at site: Min 25 % Max 55 %"
Output: `"humidity_min": "25", "humidity_max": "55"`
 
**Example 4 - Website field:**
If you see: "Website: Gulf Additives.com"
Output: `"website": "Gulf Additives.com"`
 
**Example 5 - Table data:**
If table shows:
| Sl | Raw material Name | Bulk density | Physical form | Feed rate % |
|----|------------------|--------------|---------------|-------------|
| 1  | LLDPE           | 0.590        | Powder        | 37.65       |
| 2  | CA5             | 0.32         | Powder        | 0.5         |
 

 
## CRITICAL REMINDERS:
 
- **Only extract from marked/selected boxes and buttons**
- **Look for filled boxes ⬛, filled circles ●, check marks ☑**
- **Extract filled input fields, table data, and written content**
- **Empty boxes ☐, empty circles ○, and blank fields = null values**
- **Look for exact field labels including typos**
- **Return valid JSON only**
- **No explanations, just JSON output**
-**There are multiple options that can be selected should show**
 
**VISUAL INDICATORS TO EXTRACT:**
- ⬛ ● ☑ ✓ ✗ ⚫ = SELECTED (extract)
- ☐ ○ ◯ = NOT SELECTED (ignore)
- When multiple options display any of the selected indicators (⬛ ● ☑ ✓ ✗ ⚫), extract all such options. These indicators signify that multiple selections can be made.

"""
def upload_to_gemini(path, mime_type=None):
    """Upload file to Gemini and return file object"""
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        logger.info(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        logger.error(f"Error uploading file to Gemini: {str(e)}")
        raise Exception(f"Failed to upload file to Gemini: {str(e)}")

def wait_for_files_active(files):
    """Wait for uploaded files to be processed and active"""
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")

def format_field_definitions(field_definitions):
    """Format field definitions for the prompt"""
    field_def_text = "\n".join([
        f"Field Name: {field.get('name', '')}\n"
        f"Description: {field.get('description', 'No description provided')}\n"
        for field in field_definitions
    ])
    return field_def_text

def extract_json_from_response(response_text):
    """Extract JSON from Gemini response text"""
    try:
        # Clean response text to extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.rfind("```")
            response_text = response_text[json_start:json_end].strip()
        
        # Remove any leading/trailing text that's not JSON
        if response_text.startswith('{') and response_text.endswith('}'):
            return json.loads(response_text)
        else:
            # Try to find JSON object in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx != 0:
                json_text = response_text[start_idx:end_idx]
                return json.loads(json_text)
            else:
                raise ValueError("No valid JSON found in response")
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Response text: {response_text}")
        raise e

def process_single_pdf(file_path, field_definitions):

    try:
        # Configure Gemini API
        genai.configure(api_key=gemini_api_key)
        
        # Upload PDF to Gemini
        files = [upload_to_gemini(file_path, mime_type="application/pdf")]
        wait_for_files_active(files)
        
        # Initialize model and chat session
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            generation_config=gemini_config,
            system_instruction="You are a helpful assistant specialized in data extraction from PDF documents"
        )
        
        # Start chat session with the uploaded file
        chat_session = model.start_chat(history=[{"role": "user", "parts": [files[0]]}])
        
        # Format field definitions for the prompt
        field_def_text = format_field_definitions(field_definitions)
        
        # Create extraction prompt
        extraction_prompt = EXTRACTION_PROMPT.format(field_definitions=field_def_text)
        print(extraction_prompt)
        
        # Send extraction request
        extraction_response = chat_session.send_message(extraction_prompt)
        
        # Extract JSON data from response
        extraction_json_data = extract_json_from_response(extraction_response.text)
        
        logger.info(f"Successfully processed PDF: {file_path}")
        return {
            'status': 'success',
            'data': extraction_json_data,
            'file_path': file_path
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        print(e)
        # Return empty data with field names in case of error
        empty_data = {field.get('name', ''): None for field in field_definitions}
        return {
            'status': 'error',
            'data': empty_data,
            'file_path': file_path,
            'error': str(e)
        }

# Legacy function for backward compatibility
def process_pdf(file_path):
    """Legacy function - use process_single_pdf instead"""
    logger.warning("process_pdf is deprecated, use process_single_pdf instead")
    return process_single_pdf(file_path, [])

def extract_fields(model, chat_session):
    """Legacy function - use process_single_pdf instead"""
    logger.warning("extract_fields is deprecated, use process_single_pdf instead")
    return {}
