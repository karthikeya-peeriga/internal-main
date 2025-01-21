import os
import json
from datetime import datetime
from io import StringIO
from flask import Flask, request, jsonify, render_template, send_file, Response, Blueprint, current_app
from flask_login import login_required, current_user
import anthropic
import pandas as pd
from extensions import db
from werkzeug.utils import secure_filename

infographic_bp = Blueprint('infographics_generator', __name__, template_folder='templates/infographics_generator')
UPLOAD_FOLDER = 'product_submissions'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key="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"  # Use environment variable
)

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
          image_path = os.path.join(UPLOAD_FOLDER, f'img_{timestamp}_{secure_filename(product_image.filename)}')
          product_image.save(image_path)
        else:
          image_path = None;

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
          key_attribute_1 = request.form.get('key_attribute_1')
          key_attribute_2 = request.form.get('key_attribute_2')
          key_attribute_3 = request.form.get('key_attribute_3')
          key_attribute_4 = request.form.get('key_attribute_4')
          key_attribute_5 = request.form.get('key_attribute_5')
          
          
          key_attributes = [key_attribute_1,key_attribute_2,key_attribute_3,key_attribute_4,key_attribute_5]

          product_data = {
            "brand_name": brand_name,
            "category": category,
            "sub_category": sub_category,
            "description": description,
            "ean_number": ean_number,
            "model_number": model_number,
            "color": color,
            "material": material,
            "size": size,
            "keywords": keywords,
            "key_attributes": key_attributes
            }
          message_content = f"""
            Extract 6 Key selling points from the data below:
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
            Key Attributes: {','.join(key_attributes)}
            """
        elif input_type == "specific_fields":
          title = request.form.get('title')
          description = request.form.get('description')
          bullets = request.form.get('bullets')
          product_data = {
                 "title": title,
                 "description": description,
                 "bullets": bullets
              }
          message_content = f"""
             Extract 6 Key selling points from the data below:
              Title: {title}
              Description: {description}
              Bullets: {bullets}
          """
        else:
            return "No correct input type was passed"

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
          
          response_text = str(message.content[0].text)
          # Extract sections
          sections = response_text.split("\n")
          key_features = []

          for section in sections:
                section = section.strip()
                if section and len(key_features) < 6:
                     key_features.append(section)

          if len(key_features) > 6:
             key_features = key_features[:6]
          
          with current_app.app_context():
                from main_app.app import InfographicSubmission, db
                submission = InfographicSubmission(user_id = current_user.id, product_image=image_path, input_type=input_type, product_data=product_data, claude_response=key_features )
                db.session.add(submission)
                db.session.commit()
          return render_template('infographics_generator/results.html', user=current_user, key_features = key_features)

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
    
@infographic_bp.route('/history')
@login_required
def history():
      return render_template('infographics_generator/history.html', user=current_user)


@infographic_bp.route('/history/inputs')
@login_required
def history_inputs():
   with current_app.app_context():
       from main_app.app import InfographicSubmission, db
       submissions = db.session.query(InfographicSubmission).filter_by(user_id=current_user.id).all()
       return render_template('infographics_generator/history_inputs.html', submissions=submissions, user=current_user)

@infographic_bp.route('/history/outputs')
@login_required
def history_outputs():
    with current_app.app_context():
        from main_app.app import InfographicSubmission, db
        submissions = db.session.query(InfographicSubmission).filter_by(user_id=current_user.id).all()
        return render_template('infographics_generator/history_outputs.html', submissions=submissions, user=current_user)