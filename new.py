from functools import wraps

from flask import request, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from Models.AccountInfo import AccountInfo
from Models.Users import User
from Serializers.UserSerializers import user_serializer
from extentions import db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def with_tenant_session_and_user(f):
    @wraps(f)
    def decorated_function(self, account_uid, *args, **kwargs):
        # 1️⃣ Get account info
        print(account_uid)
        account = db.session.query(AccountInfo).filter_by(id=account_uid).one_or_none()
        if not account:
            return {"message": "Account not found"}, 404

        # 2️⃣ Create tenant engine and session
        tenant_engine = create_engine(account.db_uri)
        TenantSession = sessionmaker(bind=tenant_engine)
        tenant_session = TenantSession()

        try:
            if not request.url.__contains__("/login"):
                verify_jwt_in_request()
                username = get_jwt_identity()
                if not username:
                    return {"message": "Invalid or expired token"}, 401

                # 4️⃣ Get user from tenant DB
                user = tenant_session.query(User).filter_by(username=username).first()

                user = user_serializer.dump(user)
                g.user = user

                print(user)
                if not user:
                    return {"message": "User not found in this tenant"}, 404

                # 5️⃣ Pass tenant_session and current user to the function
                return f(self, tenant_session=tenant_session,
                         *args, **kwargs)
            else:
                return f(self, tenant_session=tenant_session,*args, **kwargs)

        finally:
            tenant_session.close()
            tenant_engine.dispose()
    return decorated_function
