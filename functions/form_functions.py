# functions/form_functions.py - COMPLETE IMPLEMENTATION

from models import db, FormTemplate, FormField, User
from flask_login import current_user
from datetime import datetime
import json
from sqlalchemy import func

def create_form_template(form_data):
    """Create a new form template"""
    try:
        # Validate required fields
        if not form_data.get('name'):
            return None, "Form name is required."
        
        if not form_data.get('form_type'):
            return None, "Form type is required."
        
        # Check if form name already exists
        existing = FormTemplate.query.filter_by(name=form_data['name']).first()
        if existing:
            return None, "Form with this name already exists."
        
        # Create form template
        form_template = FormTemplate(
            name=form_data['name'],
            description=form_data.get('description', ''),
            form_type=form_data['form_type'],
            requires_approval=form_data.get('requires_approval', False),
            allow_multiple_submissions=form_data.get('allow_multiple_submissions', False),
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        # Set form fields
        fields = form_data.get('fields', [])
        if isinstance(fields, str):
            fields = json.loads(fields)
        
        form_template.set_fields(fields)
        
        db.session.add(form_template)
        db.session.commit()
        
        return form_template, "Form template created successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Form creation failed: {str(e)}"

def update_form_template(template_id, form_data):
    """Update existing form template"""
    try:
        template = FormTemplate.query.get(template_id)
        if not template:
            return False, "Form template not found."
        
        # Update basic fields
        if 'name' in form_data:
            # Check for name conflicts
            existing = FormTemplate.query.filter(
                FormTemplate.name == form_data['name'],
                FormTemplate.id != template_id
            ).first()
            if existing:
                return False, "Form with this name already exists."
            template.name = form_data['name']
        
        if 'description' in form_data:
            template.description = form_data['description']
        
        if 'form_type' in form_data:
            template.form_type = form_data['form_type']
        
        if 'requires_approval' in form_data:
            template.requires_approval = bool(form_data['requires_approval'])
        
        if 'allow_multiple_submissions' in form_data:
            template.allow_multiple_submissions = bool(form_data['allow_multiple_submissions'])
        
        if 'is_active' in form_data:
            template.is_active = bool(form_data['is_active'])
        
        # Update form fields if provided
        if 'fields' in form_data:
            fields = form_data['fields']
            if isinstance(fields, str):
                fields = json.loads(fields)
            template.set_fields(fields)
        
        template.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True, "Form template updated successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Form update failed: {str(e)}"

def delete_form_template(template_id):
    """Delete form template (soft delete)"""
    try:
        template = FormTemplate.query.get(template_id)
        if not template:
            return False, "Form template not found."
        
        # Soft delete by setting is_active to False
        template.is_active = False
        template.updated_at = datetime.utcnow()
        
        db.session.commit()
        return True, "Form template deleted successfully."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Form deletion failed: {str(e)}"

def duplicate_form_template(template_id, new_name):
    """Duplicate an existing form template"""
    try:
        original = FormTemplate.query.get(template_id)
        if not original:
            return None, "Original form template not found."
        
        # Check if new name already exists
        existing = FormTemplate.query.filter_by(name=new_name).first()
        if existing:
            return None, "Form with this name already exists."
        
        # Create duplicate
        duplicate = FormTemplate(
            name=new_name,
            description=f"Copy of {original.description}" if original.description else "",
            form_type=original.form_type,
            form_fields=original.form_fields,
            requires_approval=original.requires_approval,
            allow_multiple_submissions=original.allow_multiple_submissions,
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(duplicate)
        db.session.commit()
        
        return duplicate, "Form template duplicated successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Form duplication failed: {str(e)}"

def generate_form_html(template_id):
    """Generate HTML for form template"""
    try:
        template = FormTemplate.query.get(template_id)
        if not template:
            return "", "Form template not found."
        
        if not template.is_active:
            return "", "Form template is inactive."
        
        fields = template.get_fields()
        if not fields:
            return "", "Form has no fields defined."
        
        html_parts = [
            '<div class="dynamic-form-container">',
            f'<form class="dynamic-form" data-form-id="{template.id}">',
            f'<div class="form-header">',
            f'<h3 class="form-title">{template.name}</h3>'
        ]
        
        if template.description:
            html_parts.append(f'<p class="form-description">{template.description}</p>')
        
        html_parts.append('</div>')
        html_parts.append('<div class="form-body">')
        
        for idx, field in enumerate(fields):
            field_html = generate_field_html(field, idx)
            html_parts.append(field_html)
        
        html_parts.extend([
            '</div>',
            '<div class="form-footer">',
            '<button type="submit" class="btn btn-primary">',
            '<i class="fas fa-paper-plane"></i> Submit Form',
            '</button>',
            '<button type="reset" class="btn btn-secondary">',
            '<i class="fas fa-undo"></i> Reset',
            '</button>',
            '</div>',
            '</form>',
            '</div>'
        ])
        
        return '\n'.join(html_parts), "Form HTML generated successfully."
        
    except Exception as e:
        return "", f"Form generation failed: {str(e)}"

def generate_field_html(field, index):
    """Generate HTML for individual field"""
    field_name = field.get('name', f'field_{index}')
    field_label = field.get('label', field_name.replace('_', ' ').title())
    field_type = field.get('type', 'text')
    is_required = field.get('required', False)
    placeholder = field.get('placeholder', '')
    default_value = field.get('default_value', '')
    field_id = f"{field_name}_{index}"
    
    required_attr = 'required' if is_required else ''
    required_star = '<span class="required text-danger">*</span>' if is_required else ''
    
    html = [f'<div class="form-group mb-3" data-field-type="{field_type}">']
    html.append(f'<label for="{field_id}" class="form-label">{field_label}{required_star}</label>')
    
    if field_type == 'text':
        html.append(f'<input type="text" id="{field_id}" name="{field_name}" class="form-control" placeholder="{placeholder}" value="{default_value}" {required_attr}>')
    
    elif field_type == 'email':
        html.append(f'<input type="email" id="{field_id}" name="{field_name}" class="form-control" placeholder="{placeholder}" value="{default_value}" {required_attr}>')
    
    elif field_type == 'password':
        html.append(f'<input type="password" id="{field_id}" name="{field_name}" class="form-control" placeholder="{placeholder}" {required_attr}>')
    
    elif field_type == 'number':
        min_val = field.get('min_value', '')
        max_val = field.get('max_value', '')
        step = field.get('step', '1')
        html.append(f'<input type="number" id="{field_id}" name="{field_name}" class="form-control" placeholder="{placeholder}" value="{default_value}" min="{min_val}" max="{max_val}" step="{step}" {required_attr}>')
    
    elif field_type == 'phone':
        html.append(f'<input type="tel" id="{field_id}" name="{field_name}" class="form-control" placeholder="{placeholder}" value="{default_value}" pattern="[0-9+\\-\\s]+" {required_attr}>')
    
    elif field_type == 'textarea':
        rows = field.get('rows', 3)
        html.append(f'<textarea id="{field_id}" name="{field_name}" class="form-control" rows="{rows}" placeholder="{placeholder}" {required_attr}>{default_value}</textarea>')
    
    elif field_type == 'select':
        options = field.get('options', [])
        html.append(f'<select id="{field_id}" name="{field_name}" class="form-control" {required_attr}>')
        html.append('<option value="">-- Select an option --</option>')
        for option in options:
            selected = 'selected' if option == default_value else ''
            html.append(f'<option value="{option}" {selected}>{option}</option>')
        html.append('</select>')
    
    elif field_type == 'radio':
        options = field.get('options', [])
        for i, option in enumerate(options):
            checked = 'checked' if option == default_value else ''
            option_id = f"{field_id}_{i}"
            html.append(f'<div class="form-check">')
            html.append(f'<input class="form-check-input" type="radio" id="{option_id}" name="{field_name}" value="{option}" {checked} {required_attr}>')
            html.append(f'<label class="form-check-label" for="{option_id}">{option}</label>')
            html.append('</div>')
    
    elif field_type == 'checkbox':
        options = field.get('options', [])
        default_values = default_value.split(',') if default_value else []
        for i, option in enumerate(options):
            checked = 'checked' if option in default_values else ''
            option_id = f"{field_id}_{i}"
            html.append(f'<div class="form-check">')
            html.append(f'<input class="form-check-input" type="checkbox" id="{option_id}" name="{field_name}[]" value="{option}" {checked}>')
            html.append(f'<label class="form-check-label" for="{option_id}">{option}</label>')
            html.append('</div>')
    
    elif field_type == 'file':
        accept = field.get('accept', '')
        multiple = 'multiple' if field.get('multiple', False) else ''
        html.append(f'<input type="file" id="{field_id}" name="{field_name}" class="form-control" accept="{accept}" {multiple} {required_attr}>')
    
    elif field_type == 'date':
        html.append(f'<input type="date" id="{field_id}" name="{field_name}" class="form-control" value="{default_value}" {required_attr}>')
    
    elif field_type == 'time':
        html.append(f'<input type="time" id="{field_id}" name="{field_name}" class="form-control" value="{default_value}" {required_attr}>')
    
    elif field_type == 'datetime-local':
        html.append(f'<input type="datetime-local" id="{field_id}" name="{field_name}" class="form-control" value="{default_value}" {required_attr}>')
    
    elif field_type == 'url':
        html.append(f'<input type="url" id="{field_id}" name="{field_name}" class="form-control" placeholder="{placeholder}" value="{default_value}" {required_attr}>')
    
    elif field_type == 'color':
        html.append(f'<input type="color" id="{field_id}" name="{field_name}" class="form-control form-control-color" value="{default_value or "#000000"}" {required_attr}>')
    
    # Add help text if provided
    if field.get('help_text'):
        html.append(f'<small class="form-text text-muted">{field["help_text"]}</small>')
    
    html.append('</div>')
    return '\n'.join(html)

def validate_form_data(template_id, submitted_data):
    """Validate submitted form data against template"""
    try:
        template = FormTemplate.query.get(template_id)
        if not template:
            return False, "Form template not found."
        
        fields = template.get_fields()
        errors = []
        validated_data = {}
        
        for field in fields:
            field_name = field.get('name')
            field_label = field.get('label', field_name)
            field_type = field.get('type')
            is_required = field.get('required', False)
            
            # Get submitted value
            value = submitted_data.get(field_name)
            
            # Handle checkbox arrays
            if field_type == 'checkbox' and f"{field_name}[]" in submitted_data:
                value = submitted_data.getlist(f"{field_name}[]")
            
            # Check required fields
            if is_required and (value is None or value == '' or (isinstance(value, list) and not value)):
                errors.append(f"{field_label} is required.")
                continue
            
            # Skip validation if field is empty and not required
            if value is None or value == '':
                validated_data[field_name] = None
                continue
            
            # Type-specific validation
            if field_type == 'email':
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(value)):
                    errors.append(f"{field_label} must be a valid email address.")
                    continue
            
            elif field_type == 'number':
                try:
                    numeric_value = float(value)
                    
                    # Check min/max values
                    if 'min_value' in field and numeric_value < field['min_value']:
                        errors.append(f"{field_label} must be at least {field['min_value']}.")
                        continue
                    
                    if 'max_value' in field and numeric_value > field['max_value']:
                        errors.append(f"{field_label} must be no more than {field['max_value']}.")
                        continue
                    
                    validated_data[field_name] = numeric_value
                    continue
                    
                except ValueError:
                    errors.append(f"{field_label} must be a valid number.")
                    continue
            
            elif field_type == 'phone':
                import re
                # Remove spaces, dashes, parentheses for validation
                clean_phone = re.sub(r'[\s\-\(\)]', '', str(value))
                if not re.match(r'^[\+]?[0-9]{10,15}$', clean_phone):
                    errors.append(f"{field_label} must be a valid phone number.")
                    continue
            
            elif field_type == 'url':
                import re
                url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
                if not re.match(url_pattern, str(value)):
                    errors.append(f"{field_label} must be a valid URL.")
                    continue
            
            # Length validation
            if isinstance(value, str):
                if 'min_length' in field and len(value) < field['min_length']:
                    errors.append(f"{field_label} must be at least {field['min_length']} characters long.")
                    continue
                
                if 'max_length' in field and len(value) > field['max_length']:
                    errors.append(f"{field_label} must be no more than {field['max_length']} characters long.")
                    continue
            
            # Store validated value
            validated_data[field_name] = value
        
        if errors:
            return False, {"errors": errors, "data": validated_data}
        
        return True, {"data": validated_data}
        
    except Exception as e:
        return False, f"Validation failed: {str(e)}"

def get_form_templates_by_type(form_type):
    """Get all form templates of a specific type"""
    return FormTemplate.query.filter_by(form_type=form_type, is_active=True).order_by(FormTemplate.name).all()

def search_form_templates(search_term):
    """Search form templates by name or description"""
    search_pattern = f"%{search_term}%"
    return FormTemplate.query.filter(
        db.or_(
            FormTemplate.name.ilike(search_pattern),
            FormTemplate.description.ilike(search_pattern)
        ),
        FormTemplate.is_active == True
    ).order_by(FormTemplate.name).all()

def get_form_usage_statistics():
    """Get form usage statistics"""
    try:
        total_forms = FormTemplate.query.filter_by(is_active=True).count()
        total_usage = db.session.query(func.sum(FormTemplate.usage_count)).scalar() or 0
        
        # Most used forms
        most_used = FormTemplate.query.filter_by(is_active=True).order_by(
            FormTemplate.usage_count.desc()
        ).limit(5).all()
        
        # Recently created forms
        recent_forms = FormTemplate.query.filter_by(is_active=True).order_by(
            FormTemplate.created_at.desc()
        ).limit(5).all()
        
        # Usage by type
        usage_by_type = db.session.query(
            FormTemplate.form_type,
            func.count(FormTemplate.id).label('count'),
            func.sum(FormTemplate.usage_count).label('total_usage')
        ).filter_by(is_active=True).group_by(FormTemplate.form_type).all()
        
        return {
            'total_forms': total_forms,
            'total_usage': total_usage,
            'most_used': most_used,
            'recent_forms': recent_forms,
            'usage_by_type': [
                {
                    'type': row.form_type,
                    'count': row.count,
                    'total_usage': row.total_usage or 0
                }
                for row in usage_by_type
            ]
        }
        
    except Exception as e:
        return {
            'total_forms': 0,
            'total_usage': 0,
            'most_used': [],
            'recent_forms': [],
            'usage_by_type': []
        }

def export_form_data(template_id, format='json'):
    """Export form template data"""
    try:
        template = FormTemplate.query.get(template_id)
        if not template:
            return None, "Form template not found."
        
        form_data = {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'form_type': template.form_type,
            'fields': template.get_fields(),
            'requires_approval': template.requires_approval,
            'allow_multiple_submissions': template.allow_multiple_submissions,
            'usage_count': template.usage_count,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        }
        
        if format == 'json':
            import json
            return json.dumps(form_data, indent=2), "Form exported as JSON."
        
        elif format == 'csv':
            # For CSV, export just the field definitions
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Field Name', 'Label', 'Type', 'Required', 'Options'])
            
            # Write field data
            for field in form_data['fields']:
                writer.writerow([
                    field.get('name', ''),
                    field.get('label', ''),
                    field.get('type', ''),
                    field.get('required', False),
                    ', '.join(field.get('options', []))
                ])
            
            return output.getvalue(), "Form exported as CSV."
        
        else:
            return None, "Unsupported export format."
            
    except Exception as e:
        return None, f"Export failed: {str(e)}"

def import_form_template(import_data, format='json'):
    """Import form template from data"""
    try:
        if format == 'json':
            if isinstance(import_data, str):
                data = json.loads(import_data)
            else:
                data = import_data
        else:
            return None, "Unsupported import format."
        
        # Check if form name already exists
        existing = FormTemplate.query.filter_by(name=data['name']).first()
        if existing:
            return None, f"Form with name '{data['name']}' already exists."
        
        # Create new form template
        template = FormTemplate(
            name=data['name'],
            description=data.get('description', ''),
            form_type=data.get('form_type', 'other'),
            requires_approval=data.get('requires_approval', False),
            allow_multiple_submissions=data.get('allow_multiple_submissions', False),
            created_by=current_user.id if current_user.is_authenticated else None
        )
        
        # Set fields
        if 'fields' in data:
            template.set_fields(data['fields'])
        
        db.session.add(template)
        db.session.commit()
        
        return template, "Form template imported successfully."
        
    except Exception as e:
        db.session.rollback()
        return None, f"Import failed: {str(e)}"