import os
import re

def update_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r') as f:
        content = f.read()

    # Add {% load crispy_forms_tags %} if not present
    if '{% load crispy_forms_tags %}' not in content and '{% extends' in content:
        content = re.sub(r'({% extends .*? %})', r'\1\n{% load crispy_forms_tags %}', content)

    # Replace manual field rendering with crispy
    # Pattern: <div class="form-group.*?">.*?<label>.*?</label>.*?{{ form.(\w+) }}.*?(?:{{ form.\w+.errors }})?.*?</div>
    # Actually, the easiest way is to just replace {{ form.field }} with {{ form.field|as_crispy_field }} 
    # and remove the <label> and <div class="form-group"> wraps, but that requires complex regex.
    # Alternatively, let's just replace all {{ form }} with {{ form|crispy }} if we want strict uniformity.
    # The user said "forms in each section of this project looks unprofessional. Can you make them with professional look? also the fields inside each form should be aligned with page width and height . also it should be placed uniformly with nice look."
    # Standardizing to {{ form|crispy }} is the BEST way to ensure 100% uniformity across the entire app.
    
    # We will look for <form ...> ... </form> and replace the interior (except csrf_token) with {{ form|crispy }}.
    pass

