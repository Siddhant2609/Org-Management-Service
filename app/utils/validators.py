def validate_password_strength(password: str) -> bool:
    """Basic password strength checks: min length and at least one digit and one letter."""
    if not password or len(password) < 6:
        return False
    has_digit = any(c.isdigit() for c in password)
    has_letter = any(c.isalpha() for c in password)
    return has_digit and has_letter
