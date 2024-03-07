from rest_framework.views import APIView
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from app.auth.jwt_auth import TokenAuthentication
from django.conf import settings
from app.database.mongodb import MongoDBConnector , JSONSerialize

db = MongoDBConnector('megamind')

class SourceView(APIView):

    authentication_classes=[TokenAuthentication]

    @swagger_auto_schema(tags=['auth'],responses={200: 'Dashboard access granted', 401: 'Invalid token'})
    
    def get(self, request):

        try :
            
            collection  = db.get_collection('sites')
            result = list(collection.find({},['name', 'category', 'key', 'collection_names']))

            data = JSONSerialize.get(result)

            return JsonResponse({'status': True, 'message':'success', 'data': data , 'total_records':len(result) })
        except Exception as ex:
            return JsonResponse({'status': False, 'message':  str(ex)  })
