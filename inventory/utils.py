from .models import Profile

def get_role(user):
    # If profile exists, use it
    if hasattr(user, "profile"):
        return user.profile.role
    return None

def is_admin(user):
    # Treat Django superuser as ADMIN, even if no Profile row exists
    return user.is_superuser or get_role(user) == "ADMIN"

def is_power(user):
    return get_role(user) == "POWER"

def is_user(user):
    return get_role(user) == "USER"
