import os
import sys
import platform

def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return os.path.join(base_path, relative_path)

_APP_VERSION = "1.0.0"
_REMOTE_VERSION_URL = "https://api.github.com/repos/xiandaihanyucidain/ChineseDict/releases/latest"

def get_version():
    return _APP_VERSION

def get_remote_version_url():
    return _REMOTE_VERSION_URL

def get_crash_log_dir():
    if sys.platform == 'darwin':
        log_dir = os.path.expanduser('~/Library/Logs/ChineseDict/crashes')
    else:
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(appdata, 'ChineseDict', 'crashes')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def get_platform_info():
    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': sys.version,
        'python_executable': sys.executable,
        'frozen': getattr(sys, 'frozen', False),
    }

def format_definition(definition):
    parts = definition.split('/')
    formatted = []
    for i, part in enumerate(parts, 1):
        part = part.strip()
        if part:
            formatted.append(f"{i}. {part}")
    return '\n'.join(formatted)
