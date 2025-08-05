# templatetags/custom_filters.py
import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    return os.path.basename(value)

# yourapp/templatetags/custom_filters.py
import os
from django import template

register = template.Library()

@register.filter
def file_icon(filename):
    ext = os.path.splitext(filename.lower())[1]
    if ext == ".pdf":
        return "pdf-icon.png"
    elif ext == ".txt":
        return "txt-icon.png"
    elif ext in [".doc", ".docx"]:
        return "word-icon.png"
    elif ext in [".xls", ".xlsx"]:
        return "excel-icon.png"
    elif ext in [".ppt", ".pptx"]:
        return "ppt-icon.png"
    else:
        return "file-icon.png"
