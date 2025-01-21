import os
import json
import csv
from datetime import datetime
from io import StringIO
from flask import Flask, request, jsonify, render_template, send_file, Response, Blueprint, current_app
from flask_login import login_required, current_user
import anthropic
import pandas as pd
from extensions import db
from werkzeug.utils import secure_filename
from PIL import Image
import base64

infographic_bp = Blueprint('infographics_generator', __name__, template_folder='templates/infographics_generator')
UPLOAD_FOLDER = 'product_submissions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Anthropic client
client = anthropic.Anthropic(
<<<<<<< HEAD
    api_key="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"
=======
    api_key="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"  # Use environment variable
>>>>>>> secondary
)

def generate_layout_prompt(product_type, title, features, image_filename):
    return f"""
    Create 3 different SVG layout designs for a product infographic. Each layout should:
    - Be 2000x2000 pixels
    - Include a placeholder for the product image '{image_filename}'
    - Display the title: "{title}"
    - Showcase these 3 key features with their emojis:
    {features[:3]}
    
    Product type: {product_type}
    
    Each layout should be creative and appropriate for this type of product. Include gradients, modern design elements, and ensure the product image is prominent.
    Make each layout distinctly different in terms of composition.
    
    For each layout:
    1. Use a different background style/gradient
    2. Position the product image differently
    3. Arrange the features in a unique way
    4. Use different decorative elements
    
    Return only the SVG code for all 3 layouts, separated by '---LAYOUT---'.
    Each SVG should have {{product_image_path}} as a placeholder for the image path.
    Make sure each SVG has a proper viewBox="0 0 2000 2000" attribute.
    
    Ensure the SVG layouts have:
    1. Modern gradient backgrounds
    2. Subtle shadows and depth
    3. Clear typography for features
    4. Proper scaling and positioning
    5. Clean, professional look
    """

@infographic_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # Helper function to safely get list or single value
        def safe_get_list(key, default=None):
            value = request.form.get(key, default)
            return value if isinstance(value, list) else [value] if value else default or []
        
        input_type = request.form['input_type']
        product_image = request.files.get('product_image')
        
        if product_image and product_image.filename != '':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f'img_{timestamp}_{secure_filename(product_image.filename)}'
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            product_image.save(image_path)
            
            # Open and process the image to get dimensions
            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = width / height
        else:
            return "No image uploaded", 400

        if input_type == "content_fields":
            brand_name = request.form.get('brand_name')
            category = request.form.get('category')
            sub_category = request.form.get('sub_category')
            description = request.form.get('brief_product_description')
            ean_number = request.form.get('ean_number')
            model_number = request.form.get('model_number')
            color = request.form.get('color')
            material = request.form.get('material')
            size = request.form.get('size')
            keywords = request.form.get('keywords')
            key_attributes = [
                request.form.get('key_attribute_1'),
                request.form.get('key_attribute_2'),
                request.form.get('key_attribute_3'),
                request.form.get('key_attribute_4'),
                request.form.get('key_attribute_5')
            ]
            title = f"{brand_name} - {category}"
            
            message_content = f"""
                Extract exactly 6 key selling points from the data below. Each point MUST be 5-8 words maximum. Make sure that the bullet points are on their own separate lines.
                Brand: {brand_name}
                Category: {category}
                Sub Category: {sub_category}
                Description: {description}
                EAN: {ean_number}
                Model Number: {model_number}
                Color: {color}
                Material: {material}
                Size: {size}
                Keywords: {keywords}
                Key Attributes: {','.join(filter(None, key_attributes))}
            """
        elif input_type == "specific_fields":
            title = request.form.get('title')
            description = request.form.get('description')
            bullets = request.form.get('bullets')
            message_content = f"""
                Extract exactly 6 key selling points from the data below. Each point MUST be 5-8 words maximum. Make sure that the bullet points are on their own separate lines.
                Title: {title}
                Description: {description}
                Bullets: {bullets}
            """
        else:
            return "No correct input type was passed", 400

        use_emoji = request.form.get('use_emoji')
        if use_emoji:
            message_content += f"""
                Each line MUST contain a single emoji that indicates or is related to the concept that is being presented followed by a space, before the sentence
                Example: 🔋 Ultra-fast charging in just 30 minutes
            """

        try:
            # First message to get features
            features_message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0,
                system="You are an expert product copywriter. Extract the most compelling features and express them concisely.",
                messages=[{"role": "user", "content": message_content}]
            )
            
            features = features_message.content[0].text.strip().split('\n')
            features = [f.strip() for f in features if f.strip()][:3]  # Get first 3 features
            
            # Second message to generate layouts
            layouts_message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.7,
                system="You are an expert SVG designer specializing in product infographics.",
                messages=[{
                    "role": "user", 
                    "content": generate_layout_prompt(category if input_type == "content_fields" else title,
                                                    title,
                                                    features,
                                                    image_filename)
                }]
            )
            
            # Split the layouts
            svg_layouts = layouts_message.content[0].text.strip().split('---LAYOUT---')
            svg_layouts = [layout.strip() for layout in svg_layouts if layout.strip()]
            
            # Replace the placeholder with actual image path
            svg_layouts = [layout.replace('{product_image_path}', f'/{UPLOAD_FOLDER}/{image_filename}') 
                         for layout in svg_layouts]
            
            # Save submission to database
            with current_app.app_context():
                from main_app.app import InfographicSubmission, db
                submission = InfographicSubmission(
                    user_id=current_user.id,
                    product_image=image_path,
                    input_type=input_type,
                    product_data={
                        'title': title,
                        'image_aspect_ratio': aspect_ratio,
                        'features': features,
                        'layouts': svg_layouts
                    },
                    claude_response=features
                )
                db.session.add(submission)
                db.session.commit()
            
            return render_template('infographics_generator/results.html', 
                                user=current_user,
                                key_features=features,
                                layouts=svg_layouts,
                                image_path=f'/{UPLOAD_FOLDER}/{image_filename}')

        except Exception as api_error:
            return jsonify({
                "status": "error",
                "message": str(api_error)
            }), 500

    return render_template('infographics_generator/infographic_generator.html', user=current_user)

@infographic_bp.route('/download_input_template')
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
    
    # Optional: Add a sample row to guide users
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
    
    # Prepare the response
    return Response(
        si.getvalue(),
        mimetype='text/csv',
        headers={
            "Content-disposition": "attachment; filename=product_input_template.csv"
        }
    )

@infographic_bp.route('/download_file/<filename>')
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