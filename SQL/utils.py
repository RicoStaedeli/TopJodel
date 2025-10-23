
def clean_input(x):
    return x.strip() if isinstance(x, str) else x

def validate_email(email):
    if not email or not email.count("@") == 1:
        raise ValueError("Invalid email address.")

def validate_password(password):
    if not password or not password.isalnum():
        raise ValueError("Password must be alphanumeric.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one number.")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter.")

def validate_username(username):
    if not username or not username.isalnum():
        raise ValueError("Username must be alphanumeric.")

def validate_first_name(first_name):
    if not first_name or not first_name.isalpha():
        raise ValueError("First name must be alphabetic.")

def validate_last_name(last_name):
    if not last_name or not last_name.isalpha():
        raise ValueError("Last name must be alphabetic.")