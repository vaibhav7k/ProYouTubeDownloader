"""
Helper Utilities Module

Contains utility functions for common operations like filename sanitization.
"""

import re


def sanitize_filename(name: str) -> str:
    """
    Remove illegal characters from a string so it can be used as a valid filename.

    Args:
        name (str): The filename to sanitize

    Returns:
        str: Sanitized filename with illegal characters replaced by hyphens
    """
    return re.sub(r'[<>:"/\\|?*]', "-", name)