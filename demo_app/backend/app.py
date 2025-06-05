from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime
import pandas as pd
from io import BytesIO
from pdf_process import process_single_pdf

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
SCHEMAS_FOLDER = 'schemas'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'pdf'}

# Create necessary directories
for folder in [UPLOAD_FOLDER, SCHEMAS_FOLDER, RESULTS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'PDF Processing API is running'})

@app.route('/api/upload', methods=['POST'])
def upload_files():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if not file or not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        session_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        unique_filename = f"{session_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        uploaded_file = {
            'original_name': filename,
            'stored_name': unique_filename,
            'size': os.path.getsize(filepath)
        }
        
        return jsonify({
            'session_id': session_id,
            'file': uploaded_file,
            'message': 'File uploaded successfully'
        })
    
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/schemas', methods=['GET'])
def get_schemas():
    try:
        schemas = []
        if os.path.exists(SCHEMAS_FOLDER):
            for filename in os.listdir(SCHEMAS_FOLDER):
                if filename.endswith('.json'):
                    with open(os.path.join(SCHEMAS_FOLDER, filename), 'r') as f:
                        schema = json.load(f)
                        schemas.append(schema)
        
        return jsonify({'schemas': schemas})
    
    except Exception as e:
        return jsonify({'error': f'Failed to fetch schemas: {str(e)}'}), 500

@app.route('/api/schemas', methods=['POST'])
def create_schema():
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'fields' not in data:
            return jsonify({'error': 'Schema name and fields are required'}), 400
        
        schema_id = str(uuid.uuid4())
        schema = {
            'id': schema_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'fields': data['fields'],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        schema_file = os.path.join(SCHEMAS_FOLDER, f'{schema_id}.json')
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        return jsonify({'schema': schema, 'message': 'Schema created successfully'})
    
    except Exception as e:
        return jsonify({'error': f'Failed to create schema: {str(e)}'}), 500

@app.route('/api/schemas/<schema_id>', methods=['PUT'])
def update_schema(schema_id):
    try:
        data = request.get_json()
        schema_file = os.path.join(SCHEMAS_FOLDER, f'{schema_id}.json')
        
        if not os.path.exists(schema_file):
            return jsonify({'error': 'Schema not found'}), 404
        
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        
        schema.update({
            'name': data.get('name', schema['name']),
            'description': data.get('description', schema['description']),
            'fields': data.get('fields', schema['fields']),
            'updated_at': datetime.now().isoformat()
        })
        
        with open(schema_file, 'w') as f:
            json.dump(schema, f, indent=2)
        
        return jsonify({'schema': schema, 'message': 'Schema updated successfully'})
    
    except Exception as e:
        return jsonify({'error': f'Failed to update schema: {str(e)}'}), 500

@app.route('/api/schemas/<schema_id>', methods=['DELETE'])
def delete_schema(schema_id):
    try:
        schema_file = os.path.join(SCHEMAS_FOLDER, f'{schema_id}.json')
        
        if not os.path.exists(schema_file):
            return jsonify({'error': 'Schema not found'}), 404
        
        os.remove(schema_file)
        return jsonify({'message': 'Schema deleted successfully'})
    
    except Exception as e:
        return jsonify({'error': f'Failed to delete schema: {str(e)}'}), 500

@app.route('/api/process', methods=['POST'])
def process_pdfs():
    try:
        data = request.get_json()
        
        if not data or 'session_id' not in data or 'schema_id' not in data:
            return jsonify({'error': 'Session ID and Schema ID are required'}), 400
        
        session_id = data['session_id']
        schema_id = data['schema_id']
        
        # Load schema
        schema_file = os.path.join(SCHEMAS_FOLDER, f'{schema_id}.json')
        if not os.path.exists(schema_file):
            return jsonify({'error': 'Schema not found'}), 404
        
        with open(schema_file, 'r') as f:
            schema = json.load(f)
        
        # Get uploaded file (single file processing)
        uploaded_file = None
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(session_id):
                uploaded_file = os.path.join(UPLOAD_FOLDER, filename)
                break
        
        if not uploaded_file:
            return jsonify({'error': 'No file found for this session'}), 404
        
        # Process the single PDF using the new single PDF processor
        result = process_single_pdf(uploaded_file, schema['fields'])
        filename = os.path.basename(result['file_path']).replace(f'{session_id}_', '')
        
        results = [{
            'filename': filename,
            'data': result['data'],
            'status': result['status'],
            'error': result.get('error')
        }]
        
        # Save results
        result_id = str(uuid.uuid4())
        result_data = {
            'id': result_id,
            'session_id': session_id,
            'schema_id': schema_id,
            'schema_name': schema['name'],
            'results': results,
            'processed_at': datetime.now().isoformat()
        }
        
        result_file = os.path.join(RESULTS_FOLDER, f'{result_id}.json')
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        return jsonify({
            'result_id': result_id,
            'results': results,
            'message': 'PDF processed successfully'
        })
    
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/export/<result_id>', methods=['GET'])
def export_results(result_id):
    try:
        result_file = os.path.join(RESULTS_FOLDER, f'{result_id}.json')
        
        if not os.path.exists(result_file):
            return jsonify({'error': 'Results not found'}), 404
        
        with open(result_file, 'r') as f:
            result_data = json.load(f)
        
        # Create DataFrame
        rows = []
        for result in result_data['results']:
            if result['status'] == 'success':
                row = {'filename': result['filename']}
                row.update(result['data'])
                rows.append(row)
        
        if not rows:
            return jsonify({'error': 'No successful results to export'}), 400
        
        df = pd.DataFrame(rows)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Extracted Data')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'extracted_data_{result_id}.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/api/reset/<session_id>', methods=['DELETE'])
def reset_session(session_id):
    try:
        # Remove uploaded file
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(session_id):
                os.remove(os.path.join(UPLOAD_FOLDER, filename))
        
        # Remove results
        for filename in os.listdir(RESULTS_FOLDER):
            if filename.endswith('.json'):
                with open(os.path.join(RESULTS_FOLDER, filename), 'r') as f:
                    result_data = json.load(f)
                    if result_data.get('session_id') == session_id:
                        os.remove(os.path.join(RESULTS_FOLDER, filename))
        
        return jsonify({'message': 'Session reset successfully'})
    
    except Exception as e:
        return jsonify({'error': f'Reset failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 