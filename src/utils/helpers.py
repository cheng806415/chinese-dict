import os
import sys

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.join(base_path, relative_path)

def get_version():
    return "1.0.0"

def format_definition(definition):
    parts = definition.split('/')
    formatted = []
    for i, part in enumerate(parts, 1):
        part = part.strip()
        if part:
            formatted.append(f"{i}. {part}")
    return '\n'.join(formatted)
