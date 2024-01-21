# Get the database using the method we defined in pymongo_test_insert file
from bson import ObjectId
from python_mongoDB import get_database
dbname = get_database()
 
# Retrieve a collection named "user_1_items" from database
collection = dbname["photos"]

def view_cats(telegram_id):
    all_records = collection.find({"telegram_id": telegram_id})
    return all_records

def get_cat(cat_id):
    # Convert the provided cat_id (presumably a string) to ObjectId
    cat_id_object = ObjectId(cat_id)

    # Query the collection using the ObjectId
    cat = collection.find_one({"_id": cat_id_object})
    
    return cat

def get_telegram_id(username):
    namedb = dbname["users"]
    record = list(namedb.find({"name": username}))
    if(len(record) == 0):
        return None
    return record[0]['_id']
    