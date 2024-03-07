from pymongo import MongoClient 
from django.conf import settings
from bson import ObjectId
from json import JSONEncoder
from datetime import datetime
import json


class MongoDBConnector:
    def __init__(self, DB=''):

        try:

            if DB == "":
                raise Exception("DB Not Provided")
            
            host=settings.DATABASES[DB]['HOST']
            port=settings.DATABASES[DB]['PORT']
            database_name=settings.DATABASES[DB]['DATABASE']
            username=settings.DATABASES[DB]['USERNAME']
            password=settings.DATABASES[DB]['PASSWORD']

            uri = f"mongodb://{host}:{port}/{database_name}"

            self.client = MongoClient(uri)
            self.db = self.client[database_name]

        except Exception as ex:
            raise Exception(str(ex))

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def run_aggregation_pipeline(self, collection_name, pipeline):
        collection = self.get_collection(collection_name)
        result = collection.aggregate(pipeline)
        return list(result)

class MongoDBEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (ObjectId, datetime)):
            return str(obj)
        return JSONEncoder.default(self, obj)
    
class JSONSerialize:
    def get(data):

        serialized_data = json.dumps(data, cls=MongoDBEncoder)

        data = json.loads(serialized_data)

        return data