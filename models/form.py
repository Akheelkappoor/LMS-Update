# models/form.py - FIXED FORM MODELS WITH PROPER RELATIONSHIPS

from datetime import datetime
import json
from . import db

class FormTemplate(db.Model):
    """Dynamic form template model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    form_type = db.Column(db.String(50), nullable=False)  # user, tutor, student, other
    
    # Form structure (JSON)
    form_fields = db.Column(db.Text, nullable=False)  # JSON array of field definitions
    
    # Form settings
    is_active = db.Column(db.Boolean, default=True)
    requires_approval = db.Column(db.Boolean, default=False)
    allow_multiple_submissions = db.Column(db.Boolean, default=False)
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships - FIXED
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_forms')
    fields = db.relationship('FormField', backref='form_template', cascade='all, delete-orphan')
    
    def get_fields(self):
        """Get form fields as list of dictionaries"""
        if self.form_fields:
            try:
                return json.loads(self.form_fields)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_fields(self, fields_list):
        """Set form fields from list"""
        self.form_fields = json.dumps(fields_list) if fields_list else '[]'
    
    def add_field(self, field_data):
        """Add a single field to the form"""
        fields = self.get_fields()
        fields.append(field_data)
        self.set_fields(fields)
    
    def remove_field(self, field_name):
        """Remove a field by name"""
        fields = self.get_fields()
        fields = [field for field in fields if field.get('name') != field_name]
        self.set_fields(fields)
    
    def increment_usage(self):
        """Increment usage counter"""
        self.usage_count = (self.usage_count or 0) + 1
        self.last_used = datetime.utcnow()
    
    def validate_form_data(self, submitted_data):
        """Validate submitted data against form fields"""
        fields = self.get_fields()
        errors = []
        
        for field in fields:
            field_name = field.get('name')
            field_label = field.get('label', field_name)
            is_required = field.get('required', False)
            field_type = field.get('type')
            
            # Check required fields
            if is_required and (field_name not in submitted_data or not submitted_data[field_name]):
                errors.append(f"{field_label} is required.")
                continue
            
            # Skip validation if field is empty and not required
            if field_name not in submitted_data or not submitted_data[field_name]:
                continue
            
            value = submitted_data[field_name]
            
            # Type-specific validation
            if field_type == 'email':
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, value):
                    errors.append(f"{field_label} must be a valid email address.")
            
            elif field_type == 'number':
                try:
                    float(value)
                except ValueError:
                    errors.append(f"{field_label} must be a valid number.")
            
            elif field_type == 'phone':
                if len(str(value).replace('+', '').replace('-', '').replace(' ', '')) < 10:
                    errors.append(f"{field_label} must be a valid phone number.")
            
            # Custom validation rules
            validation_rules = field.get('validation', {})
            
            if 'min_length' in validation_rules:
                if len(str(value)) < validation_rules['min_length']:
                    errors.append(f"{field_label} must be at least {validation_rules['min_length']} characters long.")
            
            if 'max_length' in validation_rules:
                if len(str(value)) > validation_rules['max_length']:
                    errors.append(f"{field_label} must be no more than {validation_rules['max_length']} characters long.")
            
            if 'min_value' in validation_rules and field_type == 'number':
                try:
                    if float(value) < validation_rules['min_value']:
                        errors.append(f"{field_label} must be at least {validation_rules['min_value']}.")
                except ValueError:
                    pass  # Already handled above
            
            if 'max_value' in validation_rules and field_type == 'number':
                try:
                    if float(value) > validation_rules['max_value']:
                        errors.append(f"{field_label} must be no more than {validation_rules['max_value']}.")
                except ValueError:
                    pass  # Already handled above
        
        return errors
    
    def __repr__(self):
        return f'<FormTemplate {self.name}>'


class FormField(db.Model):
    """Individual form field model (for complex field storage)"""
    id = db.Column(db.Integer, primary_key=True)
    form_template_id = db.Column(db.Integer, db.ForeignKey('form_template.id'), nullable=False)
    
    # Field definition
    field_name = db.Column(db.String(100), nullable=False)
    field_label = db.Column(db.String(200), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)  # text, email, number, select, etc.
    
    # Field properties (JSON)
    field_properties = db.Column(db.Text)  # JSON for options, validation, etc.
    
    # Field behavior
    is_required = db.Column(db.Boolean, default=False)
    is_readonly = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    
    # Conditional logic
    conditional_logic = db.Column(db.Text)  # JSON for show/hide rules
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_properties(self):
        """Get field properties as dictionary"""
        if self.field_properties:
            try:
                return json.loads(self.field_properties)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_properties(self, properties_dict):
        """Set field properties from dictionary"""
        self.field_properties = json.dumps(properties_dict) if properties_dict else None
    
    def get_conditional_logic(self):
        """Get conditional logic as dictionary"""
        if self.conditional_logic:
            try:
                return json.loads(self.conditional_logic)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_conditional_logic(self, logic_dict):
        """Set conditional logic from dictionary"""
        self.conditional_logic = json.dumps(logic_dict) if logic_dict else None
    
    def to_dict(self):
        """Convert field to dictionary for JSON serialization"""
        return {
            'name': self.field_name,
            'label': self.field_label,
            'type': self.field_type,
            'required': self.is_required,
            'readonly': self.is_readonly,
            'order': self.display_order,
            'properties': self.get_properties(),
            'conditional_logic': self.get_conditional_logic()
        }
    
    def __repr__(self):
        return f'<FormField {self.field_name} ({self.field_type})>'
    


def get_fields(self):
    """Get form fields as list"""
    try:
        return json.loads(self.fields) if self.fields else []
    except (json.JSONDecodeError, TypeError):
        return []

def set_fields(self, fields_list):
    """Set form fields from list"""
    self.fields = json.dumps(fields_list) if fields_list else None
