from pathlib import Path

DEF_EXT = "lst"

def ensure_ext(file_name: str) -> str:
    if not file_name:
        return None
    fn = file_name.strip()
    if not fn:
        return None
    if Path(fn).suffix:
        return fn
    if fn.endswith('.'):
        return fn + DEF_EXT
    return fn + '.' + DEF_EXT
