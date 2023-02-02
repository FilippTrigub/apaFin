"""Utility functions for views"""
import re
import numbers

def sanitize_float(float_string):
    """Turn a number string into a valid float"""
    if isinstance(float_string, numbers.Number):
        return float(float_string)
    digits = re.match(r'\d+', float_string)
    if digits is None:
        return None
    return float(digits[0])
