from functools import wraps
from flask import g, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from Models.Users import User
from Serializers.UserSerializers import user_serializer
from new import get_current_tenant_session  # your function to get tenant DB session

def tenant_user_required(func):
    """
    Decorator to:
    1. Verify JWT token
    2. Get tenant DB session
    3. Populate g.user with tenant user data
    4. Pass tenant_session as first argument to the view function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Skip auth for preflight or login/uploads
        if request.method == 'OPTIONS' or request.url.endswith('/login') or 'uploads' in request.url:
            return func(*args, **kwargs)

        # Verify JWT
        try:
            verify_jwt_in_request()
            identity = get_jwt_identity()
            if not identity:
                return {"msg": "Token is invalid or expired"}, 401
        except Exception:
            return {"msg": "Token is invalid or expired"}, 401

        # Get tenant session
        tenant_session = get_current_tenant_session()

        # Fetch user from tenant DB
        user = tenant_session.query(User).filter_by(username=identity).first()
        if not user:
            return {"msg": "User not found in tenant database"}, 401

        g.user = user_serializer.dump(user)

        return func(tenant_session, *args, **kwargs)

    return wrapper
