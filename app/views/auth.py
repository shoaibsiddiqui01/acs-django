from rest_framework.views import APIView
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth.models import User
from rest_framework_simplejwt.authentication import JWTAuthentication 
from rest_framework_simplejwt.exceptions import TokenError  
from app.serializers.login import LoginSerializer
from app.utils.jwt_auth import JwtAuth
from app.auth.jwt_auth import TokenAuthentication
import requests
from django.conf import settings
from app.database.mongodb import MongoDBConnector ,MongoDBEncoder , JSONSerialize


class LoginView(APIView):

    @swagger_auto_schema(tags=['auth'], request_body=LoginSerializer)
    def post(self, request):

        serializer = LoginSerializer(data=request.data)

        if (serializer.is_valid()):

            data = {
                'email':  serializer.validated_data['email'],
                'password':  serializer.validated_data['password'],
                'client_id':  3,
                'client_secret':  'R42m8SEh2Yx1XnRKMOgNyZzgk9FzKd1rU6MDcpCq',
            }

            response = requests.post(settings.CXP_API_BASEURL+'/api/v01/login', data=data)

            json_response = response.json()

            if 'success' in json_response:

                user = {
                    'user_id': json_response['success']['data']['user_id'],
                    'first_name': json_response['success']['data']['first_name'],
                    'last_name': json_response['success']['data']['last_name'],
                    'email': json_response['success']['data']['email'],
                }

                token = JwtAuth.create_token(user)

                user['token'] = token

                return JsonResponse({'status':True,'message':'success','data': user})

            else:
                return JsonResponse({'status':False,'message':'Invalid credentials'})

        else:
            return JsonResponse({'status':False,'message':'Some thing went wrong'})
        
class DashboardView(APIView):

    @swagger_auto_schema(tags=['auth'],responses={200: 'Dashboard access granted', 401: 'Invalid token'})
    def get(self, request):

        try :

            connector = MongoDBConnector('megamind')
            
            collection  = connector.get_collection('humans')
            result = list(collection.find().limit(10))

            data = JSONSerialize.get(result)

            return JsonResponse({'result': data})
        except Exception as ex:
            return JsonResponse({'status': False , 'message':  str(ex) })


class LogoutView(APIView):

    authentication_classes=[TokenAuthentication]

    @swagger_auto_schema(
        responses={200: 'Logout successful', 401: 'Invalid token'},
    )
    def post(self, request):
        try:

            # response = JwtAuth.authenticate_token(request.data['token'])
            
            return JsonResponse({'response': 'ok'})
        except TokenError as ex:
            return JsonResponse({'error': f'Invalid token: {str(ex)}'}, status=401)
