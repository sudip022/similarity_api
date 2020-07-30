from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy
import en_core_web_sm

app = Flask(__name__)
api = Api(app)

client = MongoClient('mongodb://localhost:27017/')
db = client.similaritydb
users = db["Users"]


def UserExist(username):
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True


class Register(Resource):
    def post(self):
        posteddata = request.get_json()

        Username = posteddata["username"]
        Password = posteddata["password"]

        if UserExist(Username):
            jres = {
                "Status Code": 301,
                "Message": "hey this user name is already exist !"
            }
            return jsonify(jres)

        hashed_pw = bcrypt.hashpw(Password.encode('utf8'), bcrypt.gensalt())

        users.insert({
            "Username": Username,
            "Password": hashed_pw,
            "Tokens": 6

        })

        retjson = {
            "Status code": 200,
            "Message": "You have sucessfully register the username and password !"
        }

        return jsonify(retjson)


def verifypw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username": username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True

    else:
        return False


def countToken(username):
    tokens = users.find({
        "Username": username
    })[0]["Tokens"]
    return tokens


class Detect(Resource):
    def post(self):
        postddata = request.get_json()

        username = postddata["username"]
        password = postddata["password"]
        text1 = postddata["text1"]
        text2 = postddata["text2"]

        if not UserExist(username):
            retjson = {
                "status code": 301,
                "Message": "Username doesnot exist in our system you must register first !"
            }
            return jsonify(retjson)

        correct_pw = verifypw(username, password)

        if not correct_pw:
            retjson = {
                "Status code": 302,
                "Message": "Invalid Password !"
            }
            return jsonify(retjson)

        num_token = countToken(username)
        if num_token <= 0:
            retjson = {
                "Status code": 303,
                "Message": "You'rw out of token please refill !"
            }
            return jsonify(retjson)

        nlp = spacy.load('en_core_web_sm')
        # nlp = en_core_web_sm.load()

        text1 = nlp(text1)
        text2 = nlp(text2)

        ratio = text1.similarity(text2)

        retjson = {
            "Status code": 200,
            "Similarity": ratio,
            "Message": "Similarity score calculated sucessfully !"
        }

        current_tekens = countToken(username)

        users.update({
            "Username": username,
        }, {
            "$set": {
                "Tokens": current_tekens
            }
        })

        return jsonify(retjson)


class Refill(Resource):
    def post(self):
        posteddata = request.get_json()

        username = posteddata["username"]
        Password = posteddata["admin_pw"]
        refil_amount = posteddata["refill"]

        if not UserExist(username):
            retjson = {
                "status code": 301,
                "Message": "Invalid username !"
            }
            return jsonify(retjson)

        correct_pw = "abc123"
        if not Password == correct_pw:
            retjson = {
                "Status code": 304,
                "Message": "Invalid Admin Password !"
            }
            return jsonify(retjson)

        # current_tekens = countToken(username)
        users.update({
            "Username": username
        },
            {
            "$set": {
                "Tokens": refil_amount
            }
        }
        )
        retjson = {
            "Status code": 200,
            "Message": "Refill Sucessfully !"
        }
        return jsonify(retjson)


api.add_resource(Register, "/register")
api.add_resource(Detect, "/detect")
api.add_resource(Refill, "/refill")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    app.run(debug=True)
