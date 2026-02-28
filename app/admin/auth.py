from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.database import get_session
from app.core.security import authenticate_user, create_access_token, verify_token
from app.core.settings import Settings


class AdminAuth(AuthenticationBackend):

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email, password = form.get('username'), form.get('password')

        async for session in get_session():
            user = await authenticate_user(email, password, session)
            if user:
                token = create_access_token({'sub': str(user.id)})
                request.session.update({'token': token})
                return True

        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get('token')
        if not token:
            return False

        try:
            verify_token(token)
            return True
        except:
            return False


authentication_backend = AdminAuth(secret_key=Settings().JWT_SECRET_KEY)
