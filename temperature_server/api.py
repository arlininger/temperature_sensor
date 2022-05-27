from flask import Flask, request, Response
from flask_restful import Resource, Api, reqparse, abort, marshal, fields
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import random
import io
# import datetime
from datetime import timezone, timedelta, datetime
import time

# Initialize Flask
app = Flask(__name__)
api = Api(app)

# Mongodb client (setup below)
client = None 


# app.logger.setLevel(logging.DEBUG)
@app.before_request
def log_request_info():
    app.logger.info("Logging a request")
    app.logger.info('Headers: %s', request.headers)
    app.logger.info('Body: %s', request.get_data())


# A List of Dicts to store all of the books
books = [{
    "id": 1,
    "title": "Zero to One",
    "author": "Peter Thiel",
    "length": 195,
    "rating": 4.17
},
    {
    "id": 2,
    "title": "Atomic Habits ",
    "author": "James Clear",
    "length": 319,
    "rating": 4.35
}
]

# Schema For the Book Request JSON
bookFields = {
    "id": fields.Integer,
    "title": fields.String,
    "author": fields.String,
    "length": fields.Integer,
    "rating": fields.Float
}


# Resource: Individual Book Routes
class Book(Resource):
    def __init__(self):
        # Initialize The Flsak Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("title", type=str, location="json")
        self.reqparse.add_argument("author", type=str, location="json")
        self.reqparse.add_argument("length", type=int, location="json")
        self.reqparse.add_argument("rating", type=float, location="json")

        super(Book, self).__init__()

    # GET - Returns a single book object given a matching id
    def get(self, id):
        book = [book for book in books if book['id'] == id]

        if(len(book) == 0):
            abort(404)

        return{"book": marshal(book[0], bookFields)}

    # PUT - Given an id
    def put(self, id):
        book = [book for book in books if book['id'] == id]

        if len(book) == 0:
            abort(404)

        book = book[0]

        # Loop Through all the passed agruments
        args = self.reqparse.parse_args()
        for k, v in args.items():
            # Check if the passed value is not null
            if v is not None:
                # if not, set the element in the books dict with the 'k' object to the value provided in the request.
                book[k] = v

        return{"book": marshal(book, bookFields)}

    def delete(self, id):
        book = [book for book in books if book['id'] == id]

        if(len(book) == 0):
            abort(404)

        books.remove(book[0])

        return 201


class BookList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "title", type=str, required=True, help="The title of the book must be provided", location="json")
        self.reqparse.add_argument(
            "author", type=str, required=True, help="The author of the book must be provided", location="json")
        self.reqparse.add_argument("length", type=int, required=True,
                                   help="The length of the book (in pages)", location="json")
        self.reqparse.add_argument(
            "rating", type=float, required=True, help="The rating must be provided", location="json")

    def get(self):
        return{"books": [marshal(book, bookFields) for book in books]}

    def post(self):
        args = self.reqparse.parse_args()
        app.logger.info(args)
        book = {
            "id": books[-1]['id'] + 1 if len(books) > 0 else 1,
            "title": args["title"],
            "author": args["author"],
            "length": args["length"],
            "rating": args["rating"]
        }

        books.append(book)
        return{"book": marshal(book, bookFields)}, 201

temperatureRecords = list()
# Schema For the Book Request JSON
temperatureRecordFields = {
    "timestamp": fields.String,
    "Temperature": fields.Float,
    "Humidity": fields.Float,
    "sensor": fields.String
}

class TemperatureRecord(Resource):
    def __init__(self):
        app.logger.info("init record")
        # Initialize The Flsak Request Parser and add arguments as in an expected request
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument("timestamp", type=str, required=True, help="required", location="json")
        self.reqparse.add_argument("Temperature", type=float, required=True, help="required", location="json")
        self.reqparse.add_argument("Humidity", type=float, required=True, help="required", location="json")
        self.reqparse.add_argument("sensor", type=str, required=True, help="required", location="json")

        super(TemperatureRecord, self).__init__()

    def get(self):
        return{"records": [marshal(temperatureRecord, temperatureRecordFields) for temperatureRecord in temperatureRecords]}

    def post(self):
        args = self.reqparse.parse_args()
        app.logger.info("Arguments")
        app.logger.info(args)
        temperatureRecord = {
            "timestamp": args["timestamp"],
            "Temperature": args["Temperature"],
            "Humidity": args["Humidity"],
            "sensor": args["sensor"]
        }
        app.logger.info(temperatureRecord)
        app.logger.info(marshal(temperatureRecord, temperatureRecordFields))
        temperatureRecords.append(temperatureRecord)
        db = client.temperatures
        db.temperatures.insert_one(temperatureRecord)
        return{"records": marshal(temperatureRecord, temperatureRecordFields)}, 201

class TemperatureGraph(Resource):
    def __init__(self):
        app.logger.info("init record")
        super(TemperatureGraph, self).__init__()

    def get(self):
        fig = create_figure()
        output = io.BytesIO()
        FigureCanvas(fig).print_png(output)
        return Response(output.getvalue(), mimetype='image/png')

def create_figure():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    db = client.temperatures 
    dbTemperatureRecords = db.temperatures.find()
    onedayago = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    lastDayRecords = [x for x in dbTemperatureRecords if datetime.fromtimestamp(int(x["timestamp"]), tz=timezone.utc) > onedayago]

    timelist = [datetime.fromtimestamp(int(x["timestamp"]), tz=timezone.utc) for x in lastDayRecords]
    temp = [x["Temperature"] for x in lastDayRecords]
    humid = [x["Humidity"] for x in lastDayRecords]
    # app.logger.info(timelist)
    # app.logger.info(temp)
    # app.logger.info(humid)
    # app.logger.info(sensor)
    axis.plot(timelist,temp)
    axis.plot(timelist,humid)
    fig.xticks(rotation=45)
    return fig

api.add_resource(BookList, "/books")
api.add_resource(Book, "/books/<int:id>")
api.add_resource(TemperatureRecord, "/temperature")
api.add_resource(TemperatureGraph, "/temperatureGraph.png")

def setupDatabase():
    global client
    # import the MongoClient class
    from pymongo import MongoClient, errors

    # global variables for MongoDB host (default port is 27017)
    DOMAIN = 'database'
    PORT = 27017

    # use a try-except indentation to catch MongoClient() errors
    try:
        # try to instantiate a client instance
        client = MongoClient(
            host = [ str(DOMAIN) + ":" + str(PORT) ],
            serverSelectionTimeoutMS = 3000, # 3 second timeout
            username = "temperature-root",
            password = "sHFyBLZBd5yLhCDG2GIgvQ",
        )

        # print the version of MongoDB server if connection successful
        print ("server version:", client.server_info()["version"])

        # get the database_names from the MongoClient()
        database_names = client.list_database_names()

    except errors.ServerSelectionTimeoutError as err:
        # set the client and DB name list to 'None' and `[]` if exception
        client = None
        database_names = []

        # catch pymongo.errors.ServerSelectionTimeoutError
        print ("pymongo ERROR:", err)

    print ("\ndatabases:", database_names)

if __name__ == "__main__":
    setupDatabase()
    app.run(host="0.0.0.0", port=5000, debug=True)











