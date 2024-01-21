# Get the database using the method we defined in pymongo_test_insert file
from random import randint
from python_mongoDB import get_database
from db_query import get_telegram_id
from PIL import Image
import io

def insert_photo(path, bit_path, name, description, id):
    dbname = get_database()
    collection_name = dbname["photos"]
    im = Image.open(path)
    image_bytes = io.BytesIO()
    bit_image = Image.open(bit_path)
    bit_image_bytes = io.BytesIO()
    im.save(image_bytes, format='PNG')
    bit_image.save(bit_image_bytes, format='PNG')
    image = {
        'data': image_bytes.getvalue(),
        '8bit': bit_image_bytes.getvalue(),
        'name': name,
        'description': description,
        'telegram_id': id,
        'defend' : randint(0, 100),
        'attack' : randint(0, 100)
    }
    collection_name.insert_one(image).inserted_id
    print("Sucessfully uploaded")

def insert_user(name, id):
    dbname = get_database()
    collection_name = dbname["users"]
    if (get_telegram_id(name) is None):
        data = {
            'name': name,
            '_id': id
        }
        collection_name.insert_one(data)
        print("User sucessfully inserted")
        return
    print("User exist")
    
    

