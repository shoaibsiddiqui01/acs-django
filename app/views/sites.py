from rest_framework.views import APIView
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from app.auth.jwt_auth import TokenAuthentication
from django.conf import settings
from app.database.mongodb import MongoDBConnector , JSONSerialize
import json
from bson import ObjectId


db = MongoDBConnector('megamind')

class SitesView(APIView):

    authentication_classes=[TokenAuthentication]

    @swagger_auto_schema(tags=['auth'],responses={200: 'Dashboard access granted', 401: 'Invalid token'})
    
    def get(self, request):

        try :
            
            collections_params = request.GET.get('collections')

            json_data = json.loads(collections_params)
     

            for item in json_data:

                for cn in item['collection_names']:
                    
                    object_ids = [ObjectId(id) for id in cn['values']]
                    document  = db.get_collection(cn['name'])

                    pipeline = [
                        {'$match': { '_id': {'$in': object_ids} }},
                        {
                            '$lookup': {
                                'from': "sites",
                                'localField': "site_id",
                                'foreignField': "_id",
                                'as': "sites"
                            }
                        },
                        {
                            '$project': {
                                'sites.name' : 1,
                                'created_at' : 1,
                                'source_url' : 1,
                                'archive_file_path':1,
                                'get_archive_detail_from_article_document' :1,
                                'lexicon_file_type_id' :1,
                            }
                        },
                    ]

                    result = list(document.aggregate(pipeline))

                    cn['sites'] =JSONSerialize.get(result) 


            return JsonResponse({'status': True, 'message':'success', 'data': json_data , 'total_records':len(json_data) })
        except Exception as ex:
            return JsonResponse({'status': False, 'message':  str(ex)  })
