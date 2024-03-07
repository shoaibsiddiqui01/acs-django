from rest_framework.views import APIView
from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from app.auth.jwt_auth import TokenAuthentication
from django.conf import settings
from app.database.mongodb import MongoDBConnector , JSONSerialize
from bson import ObjectId


db = MongoDBConnector('megamind')

def get_sites_collections(_site_ids):
    id_list = _site_ids.split(',')

    object_ids = [ObjectId(id) for id in id_list]

    collection = db.get_collection('sites') 
    data = collection.find({
        '_id': {'$in': object_ids}
    })

    collection_names = []
    for document in list(data):
        collection_names.extend(document.get('collection_names', []))

    return collection_names

def get_other_results(params, rated_results, site_collections, page, page_size):

    collection_names = db.get_collection('sites').distinct('collection_names')

    if len(site_collections) > 0:
        collection_names = site_collections

    # rated_site_collections =  []

    # for rr in rated_results:
    #     for cn in collection_names:
    #         if cn in rr:
    #             is_exists = False
    #             for rsc in rated_site_collections:

    #                 if rsc['name'] == cn:
    #                     rsc['collections'].extend(rr[cn])
    #                     is_exists = True
                
    #             if not is_exists:
    #                 rated_site_collections.append({
    #                     'name':cn,
    #                     'collections':rr[cn]
    #                 })
    filtered_humans = []

    for rr in rated_results:
        filtered_humans.append(rr['_id'])


    dna_match_conditions = [{"key": {'$in':params}}]

    dna_pipeline = [
        {
            "$match": {
                '$and':dna_match_conditions
            }
        },
    ]
   
    for cn in collection_names:
        dna_pipeline.append({
            "$addFields":{
                'var_'+cn:{
                    "$cond":{
                        'if': { '$gt': ["$"+cn, None] }, 
                        "then":"$"+cn,
                        "else":["NOTHING"]
                    }
                },
            }
    })

    lookup_pipeline = []
    lookup_let = {}

    for cn in collection_names:
        
        lookup_let['dna_'+cn] = "$var_"+cn

        lookup_pipeline.append({
            "$addFields":{
                'lok_'+cn:{
                    "$cond":{
                        'if': { '$gt': ["$"+cn, None] }, 
                        "then":"$"+cn,
                        "else":["NULL"]
                    }
                },
        }})

    #     lookup_pipeline.append({
    #         "$unwind":{
    #             'path':'$'+cn,
    #             'preserveNullAndEmptyArrays': True
    #     }
    # })
        
    lookup_pipeline.append({ "$match":{'$or':[]}})

    for cn in collection_names:
        lookup_pipeline[len(lookup_pipeline) - 1]["$match"]["$or"].append({
            "$and":[
                {cn:{"$exists":True}},
                # {"$expr":{"$in":['$$dna_'+cn , '$lok_'+cn]}},
                {'$expr': {
                    '$gt': [
                        { '$size': { '$setIntersection': ['$$dna_'+cn , '$lok_'+cn] } },0
                    ]
                }},
            ] 
        })

    lookup_pipeline.append({
        '$group':{
            '_id':'$_id',
            "data": {"$first": "$$ROOT"}
        }
    })

    dna_pipeline.append({
        '$lookup':{
            'from':'humans',
            "let":lookup_let,
            'pipeline':lookup_pipeline,
            'as': 'human'
        }
    })

    dna_pipeline.append({
        "$unwind":{
            'path':'$human',
            'preserveNullAndEmptyArrays': True
        }
    })
    
    dna_pipeline.append({
        "$match":{
            '$and':[
                # {'human':{'$exists':True}},
                {'human.data._id':{'$nin':filtered_humans}},
            ]}
    })

    dna_pipeline.append({
        "$addFields":{
           "rating":4,
           "rating_label":'Other'
        }
    })
   
    
    # dna_pipeline.append({
    #    '$replaceRoot': { 
    #     'newRoot':{
    #         '$mergeObjects':[
    #             '$human.data',
    #                 {'dna_id':'$_id'},
    #                 {'human_id':'$human.data._id'},
    #                 {'key':'$key'},
    #                 {'rating':'$rating'},
    #                 {'rating_label':"$rating_label"}
    #             ]
    #         }
    #     } 
    # })

    if page and page_size:
        
        page = int(page)
        page_size = int(page_size)

        dna_pipeline.append({"$skip": (page - 1) * page_size})
        dna_pipeline.append({"$limit": page_size})

    # return dna_pipeline


    collection = db.get_collection('d_n_a')
    dna_result =  list(collection.aggregate(dna_pipeline))
    
    return dna_result


def combined_search(
        _cnic=None,
        _phone=None, 
        _name=None, 
        _father_name=None, 
        _husband_name=None, 
        _address=None, 
        _aka=None, 
        _date_of_birth=None, 
        _site_ids=None,
        _page=None, 
        _page_size=None
    ):

    site_collections = []

    if _site_ids:
        site_collections =  get_sites_collections(_site_ids=_site_ids)


    match_conditions = []

    if _cnic or _phone:
        star_match = {"$or": [{"cnic": _cnic}, {"phone": _phone}]}
        match_conditions.append(star_match)

    elif _name:

        conflict_check = []

        if _father_name:
            conflict_check.append({"father_name": {"$in": [None, _father_name]}})

        if _husband_name:
            conflict_check.append({"husband_name": {"$in": [None, _husband_name]}})
        
        if _address:
            conflict_check.append({"address_lower": {"$in": [None, _address]}})
        
        if _aka:
            conflict_check.append({"aka": {"$in": [None, _aka]}})
        
        if _date_of_birth:
            conflict_check.append({"date_of_birth": {"$in": [None, _date_of_birth]}})


        point_match_conditions = [
            {"name": _name},
            {
                "$or": [
                    {"father_name": {"$ne": None, "$eq": _father_name}},
                    {"husband_name": {"$ne": None, "$eq": _husband_name}},
                    {"address_lower": {"$ne": None, "$eq": _address}},
                    {"aka": {"$ne": None, "$eq": _aka}},
                    {"date_of_birth": {"$ne": None, "$eq": _date_of_birth}},
                ]
            }
        ]

        if len(conflict_check) > 0:
            point_match_conditions.append({ "$and" : conflict_check })

        point_match = {
            "$and" : point_match_conditions
        }

        match_conditions.append(point_match)

    
  

    match_obj = {
        "$or": match_conditions 
    }

    if len(site_collections) > 0:
        
        match_obj = {
            "$and": [
                {"$or": match_conditions}
            ] 
        }

        match_obj['$and'].append({"$or" : []})

        for collection_name in site_collections:
            match_obj['$and'][1]['$or'].append({ collection_name : { "$exists": True } })

    pipeline = [
        {"$match": match_obj},
        {
            "$addFields": {
                "is_match_father_name":{
                    "$cond":{
                        "if":{
                            "$eq":["$father_name",_father_name]
                        },
                        "then":1,
                        "else":0
                    }
                },
                "is_match_husband_name":{
                    "$cond":{
                        "if":{
                            "$eq":["$husband_name",_husband_name]
                        },
                        "then":1,
                        "else":0
                    }
                },
                "is_match_address":{
                    "$cond":{
                        "if":{
                            "$eq":["$address_lower",_address]
                        },
                        "then":1,
                        "else":0
                    }
                },
                "is_match_aka":{
                    "$cond":{
                        "if":{
                            "$eq":["$aka",_aka]
                        },
                        "then":1,
                        "else":0
                    }
                },
                "is_match_date_of_birth":{
                    "$cond":{
                        "if":{
                            "$eq":["$date_of_birth",_date_of_birth]
                        },
                        "then":1,
                        "else":0
                    }
                },
            },
        },
        {
            "$addFields": {
                "match_sum": {
                    "$add": [
                        { "$ifNull": ["$is_match_father_name", 0] },
                        { "$ifNull": ["$is_match_husband_name", 0] },
                        { "$ifNull": ["$is_match_address", 0] },
                        { "$ifNull": ["$is_match_aka", 0] },
                        { "$ifNull": ["$is_match_date_of_birth", 0] }
                    ]
                },
            }
        },
        {
            "$addFields":{
                "rating": {
                    "$cond": {
                        "if": {
                            "$or": [
                                { "$eq": ["$cnic", _cnic] },
                                { "$eq": ["$phone", _phone] }
                            ]
                        },
                        "then": 1,
                        "else": {
                        "$cond": {
                                "if": {
                                    "$and":[
                                       {"$eq": ["$name", _name]},
                                       {"$gte": ["$match_sum", 2]} 
                                    ]
                                },
                                "then": 2,
                                "else": {
                                    "$cond": {
                                        "if": {
                                            "$and":[
                                                {"$eq": ["$name", _name]},
                                                {"$gte": ["$match_sum", 1]} 
                                            ]
                                        },
                                        "then": 3,
                                        "else": 4
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "$addFields":{
                "rating_label": {
                    '$switch':{
                        'branches':[
                            {'case' : {'$eq': ['$rating',1]}, 'then':'Star Rating'},
                            {'case' : {'$eq': ['$rating',2]}, 'then':'3 Points'},
                            {'case' : {'$eq': ['$rating',3]}, 'then':'2 Points'},
                        ],
                        'default': "Unrated"
                    }
                }
            }
        },
        {
            '$sort' : { 'rating' : 1}
        }
    ]

    # if _page and _page_size:
        
    #     _page = int(_page)
    #     _page_size = int(_page_size)

    #     pipeline.append({"$skip": (_page - 1) * _page_size})
    #     pipeline.append({"$limit": _page_size})

    collection = db.get_collection('humans')
    rated_results = list(collection.aggregate(pipeline))

    other_params = [_name, _cnic, _phone, _aka]
    other_results = get_other_results(other_params, rated_results, site_collections, _page, _page_size)

    final_results = []
    final_results.extend(rated_results)
    final_results.extend(other_results)

    return final_results

class SearchView(APIView):

    authentication_classes=[TokenAuthentication]

    @swagger_auto_schema(tags=['auth'],responses={200: 'Dashboard access granted', 401: 'Invalid token'})
    
    def get(self, request):

        try :

            _name= request.GET.get('name' , "")
            _father_name= request.GET.get('father_name' , "")
            _husband_name= request.GET.get('husband_name' , "")
            _cnic= request.GET.get('cnic' , "")
            _phone= request.GET.get('phone' , "")
            _address= request.GET.get('address' , "")
            _aka= request.GET.get('aka' , "")
            _date_of_birth = request.GET.get('date_of_birth' , "")
            
            _site_ids = request.GET.get('site_ids' , "")
            _page = request.GET.get('page' , "")
            _page_size = request.GET.get('page_size' , "")

            result = combined_search(
                _cnic = _cnic,
                _phone = _phone,
                _name = _name,
                _father_name = _father_name,
                _husband_name = _husband_name,
                _address = _address,
                _aka = _aka,
                _date_of_birth = _date_of_birth,
                _site_ids = _site_ids,
                _page = _page,
                _page_size= _page_size,
            )

            data = JSONSerialize.get(result)

            return JsonResponse({'status': True, 'message':'success', 'data': data , 'total_records':len(result) })
        except Exception as ex:
            return JsonResponse({'status': False, 'message':  str(ex)  })
