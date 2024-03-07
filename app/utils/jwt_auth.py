import jwt
import datetime
from django.conf import settings


class JwtAuth :
    def create_token(user):
        expiration_time =  settings.JWT_CONFIG['TOKEN_LIFETIME']

        print(expiration_time)

        payload = {
            'user': user,
            'exp': expiration_time
        }
        
        token = jwt.encode(payload, settings.JWT_CONFIG['SECRET_KEY'], settings.JWT_CONFIG['ALGORITHM'])
    
        return token
    

    def authenticate_token(token):
        try:
            decoded_payload = jwt.decode(token, settings.JWT_CONFIG['SECRET_KEY'], settings.JWT_CONFIG['ALGORITHM'])
            
            if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(decoded_payload['exp']):
                return { 'status' : False, 'message': "Token expired."}
            
            return { 'status' : True, 'message': "success" , 'data':decoded_payload['user']}
        
        except jwt.ExpiredSignatureError as e:
            return { 'status' : False, 'message': str(e)}
        except jwt.InvalidTokenError as e:
            return { 'status' : False, 'message': str(e)}
        