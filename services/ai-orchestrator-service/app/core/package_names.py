import re
from app.core.spec_linter import JAVA_RESERVED_WORDS


def suggested_package_prefix(value: str) -> str:
    """Make automatically suggested packages valid for numeric client codes."""
    parts=[]
    for part in value.split('.'):
        part=re.sub(r'[^A-Za-z0-9_$]', '_', part)
        if not part or part[0].isdigit() or part in JAVA_RESERVED_WORDS:
            part='client_'+part
        parts.append(part)
    return '.'.join(parts)
