from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy

#Database
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.sql import text
#Seralization
from marshmallow_sqlalchemy.schema import auto_field
from flask_marshmallow import Marshmallow
from marshmallow import fields
from sqlalchemy.sql.expression import true


#instance of the app
app = Flask(__name__)

#config database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#prepare seraliazation
ma = Marshmallow(app)


# Auto mapping the existents tables in the SQLAlchemy for avoinding writing SQL
# technacly could  do with python library to connect SQLite, PostgreSQL or others

#create a base and connect it
metadata = MetaData()

#Passing the info of the existing database to the metadata
metadata.reflect(db.engine)

''' There are the following tables in the db: movies, stars, directors, ratings, people.
The mapping only map the tables that have primary_key(movies and people).
In order to mapping the others, follow the recomendation from documentatio:
https://docs.sqlalchemy.org/en/14/faq/ormconfiguration.html#how-do-i-map-a-table-that-has-no-primary-key
by setting up primary_keys
'''
Table("ratings", metadata, Column('movie_id', Integer, primary_key=True),
Column('votes', Integer, primary_key=True), extend_existing=True)

Table("movies", metadata, Column('id', Integer, primary_key=True), extend_existing=True)

Base = automap_base(metadata=metadata)
Base.prepare(db.engine)


# Creating classes for the tables. You could create in one line but separeted for clarity
Movies = Base.classes.movies
Ratings = Base.classes.ratings

#Creating schemas for serializaton
class MoviesSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Movies

    id = auto_field()
    title = auto_field()
    original_t = auto_field()
    year = auto_field(as_string=True)
    duration = auto_field(as_string=True)
    genre = auto_field()
    rating = fields.Str()




# Main route
@app.route('/', methods=['GET'])
def index():
    
    return render_template('index.html')

# Results route
@app.route('/results', methods=['GET','POST'])
def movie_results():
    #If form is submitted
    if request.method =='POST':
        title = request.form.get("title")

        #verify if title exists
        if not title:
            return "Cound not find title"
        
        query = text("SELECT genre FROM movies WHERE title = :s")
        movies_query = db.session.execute(query, {'s': title})
        movie_sch = MoviesSchema(many=True)
        movies = movie_sch.dump(movies_query)
    
     
        #if more than one movie with that name
        # if movies_query > 1:
        #     #todo
        #     return
        
        #Get the genres
        if not movies:
            return "Cound not find title"
            
        genre = movies[0]["genre"]
        

        #Query genres with high ratings
        print(movies[0]["genre"])
        query_rec = text("""SELECT movies.title, ratings.rating, movies.year FROM movies JOIN ratings ON movies.id = 
        ratings.movie_id WHERE genre LIKE :g AND votes > 10000 ORDER BY rating DESC LIMIT 10 """)
        movies_query = db.session.execute(query_rec, {'g': genre})
        movie_schema = MoviesSchema(many=True)
        movies_rec = movie_schema.dump(movies_query)
        
        

        return render_template("results.html", movies=movies_rec, title=title)

    #If acess without submit the form
    return redirect('/')

#this route have the propurse of being requested multiple times in the event of 'keyup'
#it will return the json format of the query. we need to use marshmallow instead of jsonfy
@app.route("/search")
def search():

    # GEt the keyup event in every get request
    #https://stackoverflow.com/questions/3325467/sqlalchemy-equivalent-to-sql-like-statement
    q = request.args.get("title")

    if q:
        #Format into a seachable sql format
        search = "%{}%".format(q)
        query = text("SELECT id, title, year FROM movies JOIN ratings ON ratings.movie_id = movies.id WHERE title LIKE :s AND votes >10000 LIMIT 20")

        movies_query = db.session.execute(query, {'s': search})

        
        #query the movies in function of search
        #movies_query = db.session.query(Movies).filter(Movies.title.like(search)).limit(10).all()
        movie_schema = MoviesSchema(many=True)
        movies = movie_schema.dump(movies_query)
        #print(movies)
    
        
    else:
        movies = []

    return jsonify(movies)


if __name__ == '__main__':
    a = db.execute('SELECT * FROM movies')
    print("test1")
    print(a)
    print("test2")
