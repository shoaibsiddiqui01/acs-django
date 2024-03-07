from rest_framework.views import APIView
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from app.auth.jwt_auth import TokenAuthentication
from django.conf import settings
from app.database.mongodb import MongoDBConnector , JSONSerialize

db = MongoDBConnector('megamind')

# {
#     '$lookup':{
#         'from': "humans",
#         'pipeline': [
#             { 
#                 '$match':{
#                     '$or':[
#                         {'name':{'$in':input}},
#                         {'cnic':{'$in':input}},
#                         {'phone':{'$in':input}},
#                         {'aka':{'$in':input}},
#                     ]
#                 }
#             }
#         ],
#         'as': "human",
#     }
# },

class TestView(APIView):

    @swagger_auto_schema(tags=['auth'],responses={200: 'Dashboard access granted', 401: 'Invalid token'})
    
    def get(self, request):

        input = [request.GET.get('name')]

        try :
            
            pipeline = [
                {
                    "$match": {
                        "$or":[
                            {'name':{'$eq':request.GET.get('name')}},
                            {'cnic':{'$eq':request.GET.get('name')}},
                            {'phone':{'$eq':request.GET.get('name')}},
                            {'aka':{'$eq':request.GET.get('name')}},
                        ]
                    }
                }
            ]


            collection = db.get_collection('humans')
            result = list(collection.aggregate(pipeline))
            
            data = JSONSerialize.get(result)

            return JsonResponse({'status': True, 'message':'success', 'data': data , 'total_records':len(result) })
        except Exception as ex:
            return JsonResponse({'status': False, 'message':  str(ex)  })
