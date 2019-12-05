import pymongo

def get_mongo_client(pwd=None):
    '''
    Client Connection to MongoDB
    '''

    client = pymongo.MongoClient("mongodb://whiskyadmin:%s@whiskyreviews-shard-00-00-mvfds.mongodb.net:27017,\
        whiskyreviews-shard-00-01-mvfds.mongodb.net:27017,\
        whiskyreviews-shard-00-02-mvfds.mongodb.net:27017\
        /test?ssl=true&replicaSet=WhiskyReviews-shard-0&authSource=admin&retryWrites=true" % (pwd))

    return client


