import os
from flask_pymongo import PyMongo
from flask import Flask, jsonify
import pandas as pd
from dotenv import (
    load_dotenv, find_dotenv
)

load_dotenv(find_dotenv())

def convert_value(v):
    """torna capaz a conversão de variaveis 
    em float desde que tenha o formato (00,00)"""
    v = '.'.join(v.split(','))
    return float(v)

app = Flask(__name__)

app.config['MONGO_DBNAME'] = os.environ.get("DBNAME")
app.config['MONGO_URI'] = os.environ.get("URI")

mongo = PyMongo(app)

# TEST: localhost:5000/store
@app.route('/store/')
def all_store():
    """Returns all stores"""

    stores = mongo.db.store
    payload = []
    for s in stores.find():
        payload.append({
            "name": s['name'],
            "typestore": s['typestore'],
            "typestorename": s['typestorename']
        })
    return jsonify({"results": payload})

# TEST: localhost:5000/store/5f34642a745b8c52cf710746
@app.route('/store/<filters>')
def store_per_filter(filters):
    """Returns stories per filters
     (typestorename, typestore)"""

    stores = mongo.db.store
    # query per filter
    # Thinking on the client side he can filter by the name of the store
    results = stores.find({
        "$or": [
            {
                "name": {"$eq": filters}
            },
            {
                "typestore": {"$eq": filters}
            },
            {
                "typestorename": {"$eq": filters}
            }

        ]
    })

    payload = []

    for s in results:
        # Iterate all docs according to past filters
        payload.append({
            "name": s["name"],
            "typestore": s["typestore"],
            "typestorename": s["typestorename"]
        })

    return jsonify({"Results": payload})

# TEST: localhost:5000/products/promotions
@app.route('/products/promotions')
def products_per_promotions():
    """returns all products if contains discount"""
    products = mongo.db.products

    payload = []

    for p in products.find():
        # filtering data for discount
        if p["price"] != p["real_price"]:

            discount = convert_value(
                p["real_price"]) - convert_value(p["price"])

            payload.append({
                "ean": p['ean'],
                "category": p['category'],
                "name": p['name'],
                "price": convert_value(p['price']),
                "quantity": [],
                "discount": round(discount, 1),
                "real_price": convert_value(p['real_price']),
                "store_id": p['store_id'],
                "sale_type": p['sale_type'],
                "unit_type": [],
                "typestore": p['typestore'],
                "typestorename": p['typestorename'],
            })

        else:

            discount = 0

    return jsonify({"Results": payload})

# TEST: localhost:5000/products
@app.route('/products/')
def all_products():
    """Returns all products"""
    products = mongo.db.products

    q = products.find()

    que = products.aggregate([
        # stage 1
        {
            "$group": {
                "_id": "$category"
            }
        }
    ])

    category_qtd = []

    for i in que:
        category_qtd.append(i["_id"])

    categories_distinct = pd.Series(category_qtd).drop_duplicates().to_list()

    payload = [{
        "total_categories": len(categories_distinct),
        "total_products": q.count(),
    }]
    
    for p in q:

        # Filtering data for discount
        if p["price"] != p["real_price"]:
            discount = convert_value(
                p["real_price"]) - convert_value(p["price"])
        else:
            discount = 0

        payload.append({
            "ean": p['ean'],
            "category": p['category'],
            "name": p['name'],
            "price": p['price'],
            "quantity": [],
            "discount": round(discount, 1),
            "real_price": p['real_price'],
            "store_id": p['store_id'],
            "sale_type": p['sale_type'],
            "unit_type": [],
            "typestore": p['typestore'],
            "typestorename": p['typestorename'],
        })

    return jsonify({
        "results": payload
    })

# TEST: localhost:5000/products/7896065880106
@app.route('/products/<filters>')
def products_per_filters(filters):
    """Returns products filtered by the 'category', 
    'ean' and 'typestore' fields"""

    products = mongo.db.products

    # query of filter
    q = products.find({
        "$or": [
            {
                "category": {"$eq": filters}
            },
            {
                "ean": {"$eq": filters}
            },
            {
                "typestore": {"$eq": filters}
            },
            {
                "typestorename": {"$eq": filters}
            }
        ]
    })

    # pipeline for existing categories
    que = products.aggregate([
        # stage 1
        {
            "$match": {
                "$or": [
                    {"category": {"$eq": filters}},
                    {"ean": {"$eq": filters}},
                    {"typestore": {"$eq": filters}}
                ]
            }
        },
        # stage 2
        {
            "$group": {
                "_id": "$category"
            }
        }
    ])

    category_qtd = []

    for i in que:
        category_qtd.append(i["_id"])


    categories_distinct = pd.Series(category_qtd).drop_duplicates().to_list()

    payload = [{
        "total_categories": len(categories_distinct),
        "total_products": q.count(),
    }]

    for p in q:

        # filtering data for discount
        if p["price"] != p["real_price"]:
            discount = convert_value(
                p["real_price"]) - convert_value(p["price"])
        else:
            discount = 0

        payload.append({
            "products": {
                "ean": p['ean'],
                "category": p['category'],
                "name": p['name'],
                "price": convert_value(p['price']),
                "quantity": [],
                "discount": round(discount, 1),
                "real_price": convert_value(p['real_price']),
                "store_id": p['store_id'],
                "sale_type": p['sale_type'],
                "unit_type": [],
                "typestore": p['typestore'],
                "typestorename": p['typestorename']
            }
        })

    return jsonify({"results": payload})


if __name__ == "__main__":

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
