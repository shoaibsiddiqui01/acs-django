from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from app.utils.jwt_auth import JwtAuth  

class TokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
           raise AuthenticationFailed(detail='401',code=401)

        token = auth_header.split(' ')[1]
        if not token:
            raise AuthenticationFailed('Invalid token format')

        response = JwtAuth.authenticate_token(token)

        if response['status'] == False:
            raise AuthenticationFailed(detail='401',code=401)

        return None, None