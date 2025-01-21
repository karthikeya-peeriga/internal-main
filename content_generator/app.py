import os
import json
import csv
from datetime import datetime
from io import StringIO
from flask import Blueprint, request, jsonify, render_template, send_file, Response
from flask_login import login_required, current_user
import anthropic
import pandas as pd
from extensions import db

content_bp = Blueprint('content_generator', __name__, template_folder='templates')

# Ensure the uploads directory exists
UPLOAD_FOLDER = 'product_submissions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key="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"
)

@content_bp.route('/', methods=['GET'])
@login_required
def index():
    return render_template('content_generator/index.html', user=current_user)

@content_bp.route('/download_input_template')
@login_required
def download_input_template():
    # Create a string buffer to write CSV
    si = StringIO()
    cw = csv.writer(si)
    
    # Define the headers
    headers = [
        'Brand Name', 'Category', 'Sub-Category', 
        'Brief Product Description', 'EAN Number', 
        'Model Number', 'Color', 'Material', 
        'Size (If applicable)', 'Key Attribute 1', 
        'Key Attribute 2', 'Key Attribute 3', 
        'Key Attribute 4', 'Key Attribute 5', 
        'Keywords'
    ]
    
    # Write headers
    cw.writerow(headers)
    
    # Optional: Add a sample row
    sample_row = [
        'Example Brand', 'Electronics', 'Smartphones', 
        'Powerful Smartphone with Advanced Features', 
        '1234567890', 'ModelXYZ', 'Black', 'Aluminum', 
        '6.1 inch', 'High-Resolution Camera', 
        '5G Enabled', 'Long Battery Life', 
        'Water Resistant', 'Wireless Charging', 
        'smartphone,mobile,tech'
    ]
    cw.writerow(sample_row)
    
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={
            "Content-disposition": "attachment; filename=product_input_template.csv"
        }
    )

@content_bp.route('/download_file/<filename>')
@login_required
def download_file(filename):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

# Keep the rest of your routes the same as in your original content_generator/app.py...
@content_bp.route('/download_claude_csv')
@login_required
def download_claude_csv():
    # Get the filename passed in the query parameter
    responses_filename = request.args.get('filename')
    
    if not responses_filename:
        return jsonify({"error": "No filename provided"}), 400
    
    # Full path to the responses file
    filepath = os.path.join(UPLOAD_FOLDER, responses_filename)
    
    try:
        # Read the JSON file
        with open(filepath, 'r') as f:
            claude_responses = json.load(f)
        
        # Create a CSV string in memory
        output = []
        
        # Prepare CSV headers
        headers = [
            'Category', 'Sub Category', 'Brand Name', 'Model Number', 
            'Title', 'Description', 'Bullet 1', 'Bullet 2', 'Bullet 3', 
            'Bullet 4', 'Bullet 5'
        ]
        
        # Process each response
        for response in claude_responses:
            # Ensure we have a valid claude_output
            if not isinstance(response.get('claude_output'), dict):
                continue
            
            # Prepare bullets (pad with empty strings if fewer than 5)
            bullets = response['claude_output'].get('bullets', []) + [''] * 5
            bullets = bullets[:5]  # Ensure only 5 bullets
            
            # Create a row
            row = [
                response['product']['category'],
                response['product']['sub_category'],
                response['product']['brand_name'],
                response['product']['model_number'],
                response['claude_output'].get('title', ''),
                response['claude_output'].get('description', ''),
                *bullets  # Unpack the first 5 bullets
            ]
            
            output.append(row)
        
        # Create a string buffer to write CSV
        si = StringIO()
        cw = csv.writer(si)
        
        # Write headers and rows
        cw.writerow(headers)
        cw.writerows(output)
        
        # Prepare the response
        return Response(
            si.getvalue(),
            mimetype='text/csv',
            headers={
                "Content-disposition": f"attachment; filename={responses_filename.replace('.json', '.csv')}"
            }
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@content_bp.route('/bulk_upload', methods=['POST'])
@login_required
def bulk_upload():
    try:
        # Check if file is present
        if 'csvFile' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['csvFile']
        
        # Check if filename is empty
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Read the CSV file
        # Use pandas to read the CSV file for more robust parsing
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = [
            'Brand Name', 'Category', 'Brief Product Description', 
            'Model Number', 'Color', 'Material'
        ]
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                "error": f"Missing required columns: {', '.join(missing_columns)}"
            }), 400
        
        # Simulate form-like data for submit_products route
        form_data = {
            'brand_name[]': df['Brand Name'].tolist(),
            'category[]': df['Category'].tolist(),
            'sub_category[]': df.get('Sub-Category', [''] * len(df)).tolist(),
            'brief_product_description[]': df['Brief Product Description'].tolist(),
            'ean_number[]': df.get('EAN Number', [''] * len(df)).tolist(),
            'model_number[]': df['Model Number'].tolist(),
            'color[]': df['Color'].tolist(),
            'material[]': df['Material'].tolist(),
            'size[]': df.get('Size (If applicable)', [''] * len(df)).tolist(),
            'keywords[]': df.get('Keywords', [''] * len(df)).tolist()
        }

        # Add key attributes dynamically
        for i in range(1, 6):
            col_name = f'Key Attribute {i}'
            if col_name in df.columns:
                form_data[f'key_attribute_{i}[]'] = df[col_name].tolist()
            else:
                form_data[f'key_attribute_{i}[]'] = [''] * len(df)

        # Call submit_products with simulate data
        return submit_products(form_data)

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@content_bp.route('/submit_products', methods=['POST'])
@login_required
def submit_products(form_data=None):
    try:
        # Use the passed form_data if available, otherwise use request.form
        form = form_data if form_data is not None else request.form

        # Helper function to safely get list or single value
        def safe_get_list(key, default=None):
            value = form.get(key, default)
            return value if isinstance(value, list) else [value] if value else default or []

        # Get form data
        brand_names = safe_get_list('brand_name[]')
        categories = safe_get_list('category[]')
        sub_categories = safe_get_list('sub_category[]')
        descriptions = safe_get_list('brief_product_description[]')
        ean_numbers = safe_get_list('ean_number[]')
        model_numbers = safe_get_list('model_number[]')
        colors = safe_get_list('color[]')
        materials = safe_get_list('material[]')
        sizes = safe_get_list('size[]')
        keywords = safe_get_list('keywords[]')

        # Prepare product list and Claude API responses
        products = []
        claude_responses = []

        for i in range(len(brand_names)):
            # Prepare key attributes
            key_attributes = []
            for j in range(1, 6):
                attr_key = f'key_attribute_{j}[]'
                attr_value = safe_get_list(attr_key)[i] if i < len(safe_get_list(attr_key)) else ''
                if attr_value:
                    key_attributes.append(attr_value)

            # Construct product dictionary
            product = {
                "brand_name": brand_names[i],
                "category": categories[i],
                "sub_category": sub_categories[i],
                "description": descriptions[i],
                "ean_number": ean_numbers[i],
                "model_number": model_numbers[i],
                "color": colors[i],
                "material": materials[i],
                "size": sizes[i],
                "keywords": keywords[i].split(',') if keywords[i] else [],
                "key_attributes": key_attributes
            }
            products.append(product)

            # Prepare Claude API call content
            message_content = f''' 
        Create an Amazon Detailed Page content for the product below, using the following structured format:

        |||Title: [Detailed SEO-Optimized Product Title Goes Here]|||
        |||Description: [Comprehensive Product Description]|||
        |||Bullets: [Bullet1 =|= Bullet2 =|= Bullet3 =|= Bullet4 =|= Bullet5]|||

        Product Details:
        Product Name: {descriptions[i]}
        Brand: {brand_names[i]}
        Category: {categories[i]}
        Sub-Category: {sub_categories[i]}
        Model Number: {model_numbers[i]}
        Color: {colors[i]}
        Material: {materials[i]}
        Size: {sizes[i]}
        Key Features:
        1. {key_attributes[0] if len(key_attributes) > 0 else 'No details'}
        2. {key_attributes[1] if len(key_attributes) > 1 else 'No details'}
        3. {key_attributes[2] if len(key_attributes) > 2 else 'No details'}
        4. {key_attributes[3] if len(key_attributes) > 3 else 'No details'}
        5. {key_attributes[4] if len(key_attributes) > 4 else 'No details'}

        Keywords: {keywords[i]}

        Create a compelling, SEO-optimized product listing that highlights unique features and benefits.
        '''

            # Make Claude API call
            try:
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0,
                    system=(
                        "You are an expert Amazon and Ecommerce product listing copy writer and content generator. "
                        "You have expert knowledge on consumer behaviour and understand how the copy and content flow and storytelling "
                        "affect Indian consumer behavior. Your objective is to ensure better shopping experiences by providing accurate, "
                        "tailor-made details for each product type, increasing conversion rates, and boosting organic visibility using SEO."
                    ),
                    messages=[
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ]
                )

                # Parse the response
                response_text = str(message.content[0].text)

                # Extract sections
                sections = response_text.split("|||")
                parsed_response = {
                    "title": "",
                    "description": "",
                    "bullets": []
                }

                for section in sections:
                    if section.startswith("Title:"):
                        parsed_response["title"] = section.replace("Title:", "").strip()
                    elif section.startswith("Description:"):
                        parsed_response["description"] = section.replace("Description:", "").strip()
                    elif section.startswith("Bullets:"):
                        parsed_response["bullets"] = [
                            bullet.strip() for bullet in 
                            section.replace("Bullets:", "").strip().split("=|=")
                        ]

                claude_responses.append({
                    "product": product,
                    "claude_output": parsed_response
                })

            except Exception as api_error:
                claude_responses.append({
                    "product": product,
                    "claude_output": {"error": str(api_error)}
                })

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        products_filename = f'products_{timestamp}.json'
        responses_filename = f'claude_responses_{timestamp}.json'

        # Write product data to JSON file
        products_filepath = os.path.join(UPLOAD_FOLDER, products_filename)
        with open(products_filepath, 'w') as f:
            json.dump(products, f, indent=4)

        # Write Claude responses to JSON file
        responses_filepath = os.path.join(UPLOAD_FOLDER, responses_filename)
        with open(responses_filepath, 'w') as f:
            json.dump(claude_responses, f, indent=4)

        # Render results page with Claude API responses and filenames
        return render_template('content_generator/results.html', 
                               responses=claude_responses, 
                               products_filename=products_filename,
                               responses_filename=responses_filename, 
                               user=current_user)

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500
