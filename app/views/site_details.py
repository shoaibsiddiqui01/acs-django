from rest_framework.views import APIView
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from app.auth.jwt_auth import TokenAuthentication
from django.conf import settings
from app.database.mongodb import MongoDBConnector , JSONSerialize
import json
from bson import ObjectId


db = MongoDBConnector('lexicon')

class SourceDetailsView(APIView):

    authentication_classes=[TokenAuthentication]

    @swagger_auto_schema(tags=['auth'],responses={200: 'Dashboard access granted', 401: 'Invalid token'})
    
    def get(self, request):

        try :
            
            lexicon_file_type_id = request.GET.get('lexicon_file_type_id')

            pipeline = [
                {'$match': { 
                     '_id': ObjectId(lexicon_file_type_id)
                    }
                },
            ]

            collection  = db.get_collection('file_type_lexicon')
            result = list(collection.aggregate(pipeline))

            data = JSONSerialize.get(result)

            return JsonResponse({'status': True, 'message':'success', 'data': data , 'total_records':len(data) })
        except Exception as ex:
            return JsonResponse({'status': False, 'message':  str(ex)  })
