import math
import csv
import sys

#global variables
moviesFile = "movies.csv"
ratingsFile = "ratings.csv"
tagsFile = "tags.csv"
moviesText = ""
moviesChunk = []
movies = []
ratingsText = ""
ratingsChunk = []
ratings = []
tagsText = ""
tagsChunk = []
tags = []
moviedb = {}
users = {}

#class that contains all info about a specific movie. class elements added to dictionary using movie id as key.
class movieProfile:
    ID = None
    name = None
    ratings = None
    neighbors = None
    genres = None
    position = None
    ratingSum = None
    def __init__(self,ID,name):
        self.ID = ID
        self.name = name
        self.genres = []
        self.ratings = {}
        self.neighbors = []
        self.ratingSum = 0
    def addRating(self,user,rating):
        self.ratings[user] = rating
    def addNeighbor(self,NID):
        self.neighbors.append(NID)
    def addGenre(self,genre):
        self.genres.append(genre)
    def getGenres(self):
        return self.genres
    def getNeighbors(self):
        return self.neighbors
    def getUserRating(self,user):
        return self.ratings.get(user,0.0)
    def getPosition(self):
        return self.position
    def setPosition(self,x,y):
        self.position = [x,y]

    def __str__(self):
        return "MovieID: " + str(self.ID) + " Title: " + str(self.name) + " Genres: " + str(self.genres) + " Neighbors: " + str(self.neighbors) + " Ratings: " + str(self.ratings)

    def __repr__(self):
        return "MovieID: " + str(self.ID) + " Title: " + str(self.name) + " Genres: " + str(self.genres) + " Neighbors: " + str(self.neighbors) + " Ratings: " + str(self.ratings)

#load files into program
print("Loading files...")
with open(moviesFile, encoding="utf8") as text:
    moviesText = csv.reader(text, dialect="excel")
    moviesText = csv.DictReader(text)
    for each in moviesText:
        thisMovie = []
        thisMovie.append(each["movieId"])
        thisMovie.append(each["title"])
        thisMovie.append(each["genres"])
        movies.append(thisMovie)
with open(ratingsFile) as text:
    ratingsText = csv.reader(text, dialect="excel")
    ratingsText = csv.DictReader(text)
    for each in ratingsText:
        thisRating = []
        thisRating.append(each["userId"])
        thisRating.append(each["movieId"])
        thisRating.append(each["rating"])
        ratings.append(thisRating)
with open(tagsFile) as text:
    tagsText = (text.read())
for each in tagsText:
    tags.append(each.split(","))

#similarity calculator (cosine)
def sim(mv1, mv2):
    dotProduct = 0.0
    square1 = 0.0
    square2 = 0.0
    #can't get the actual magnitude of 2nd vector if I don't include all elements!
    for each in mv1.ratings:
        temp1 = mv1.getUserRating(each)
        temp2 = mv2.getUserRating(each)
        dotProduct += temp1 * temp2
        square1 += temp1 * temp1
    #now fixed above issue. ratings matrix is now correct!
    for each in mv2.ratings:
        temp2 = mv2.getUserRating(each)
        square2 += temp2 * temp2
    square1 = math.sqrt(square1)
    square2 = math.sqrt(square2)
    magnitudes = (square1 * square2)
    if (magnitudes * magnitudes) > math.pow(1,-6):
        return dotProduct/magnitudes
    else: return 0.0

print("Building movie profiles...")

#add genres to movie profiles
for each in movies:
    index = int(each[0])
    movie = each[1]
    genres = each[2].split("|")
    moviedb[index] = movieProfile(index, movie)
    moviedb[index].genres = genres

#add ratings to movie profiles
for each in ratings:
    user = int(each[0])
    movie = int(each[1])
    rating = float(each[2])
    if moviedb.get(movie) is not None:
        moviedb[movie].addRating(user,rating)

#normalize ratings across movies
for each in moviedb:
    thisOne = moviedb.get(each)
    sum = 0.0
    avg = 0.0
    for rating in thisOne.ratings:
        sum += thisOne.ratings.get(rating)
    num = len(thisOne.ratings)
    if num != 0:
        avg = sum/num
    else: avg = 0
    for rating in thisOne.ratings:
        rated = thisOne.ratings.get(rating)
        thisOne.addRating(rating,(rated - avg))
        if users.get(rating,None) is None:
            users[rating] = {thisOne.ID: thisOne.ratings.get(rating)}
        else:
            users.get(rating)[thisOne.ID] = thisOne.ratings.get(rating)
sorted(users)
ratingMatrix = []
progress = 1
size = len(moviedb.keys())
x = 0
y = 0

#the following section calculates the neighborhood sets for movies
#and builds the rating matrix which is not used after the neighborhood
#set is built. It may be possible to do this without storing the whole matrix at all.
print("Building similarity matrix:\n")
for movie1 in moviedb:
    print("working on movie " + str(progress) + " of " + str(size))
    ratingMatrix.append([])
    progress += 1
    highest = [[0,-2.0],[0,-2.0],[0,-2.0],[0,-2.0],[0,-2.0]]
    x = 0
    #nested loop solution calculates similarity by iterating over movie a and b but actually calculates
    #movie (a,a) , movie (a,b) and movie (b,a). thus, it is possible to optimize
    #by skipping calculations for (a,a) since it will always be 1 and also skipping
    #calculations for (b,a) since it will be the same as (a,b). This has been implemented.
    for movie2 in moviedb:
        score = 0.0
        if y > x:
            score = ratingMatrix[x][y]
            ratingMatrix[y].append(score)
        elif movie1 == movie2:
            score = 1.0
            ratingMatrix[y].append(score)
        else:
            score = sim(moviedb.get(movie1),moviedb.get(movie2))
            ratingMatrix[y].append(score)
            moviedb.get(movie1).setPosition(x,y)
        if movie1 != movie2:
            test = [movie2,score]
            for each in range(0,5):
                if highest[each][1] < test[1]:
                    temp = highest[each]
                    highest[each] = test
                    test = temp
            highest.sort(key=lambda l: l[1], reverse=True)
        x += 1
    moviedb.get(movie1).neighbors = highest
    y += 1

#for entry in ratingMatrix:
#    print(str(entry) + str(ratingMatrix.get(entry)))

print("Saving similarity matrix...")

#the following prints the cosine centered ratings matrix to a ~600MB csv file.
matrix = "matrix.csv"
with open(matrix, 'w') as text:
    writer = csv.writer(text, dialect="excel")
    for row in range(len(ratingMatrix)):
        writer.writerow(ratingMatrix[row])

print("Making movie recommendations...")

userrecommends = {}
x = 0
y = 0
usercounter = 1
#The below loop builds a recommendation set for each user based on the prediction of their top 5 rated movies using the neighborhood set
#of movies the user has rated.
for user in users:
    print("working on user " + str(usercounter) + " of " + str(len(users)))
    usercounter += 1
    recommendations = [[0,-2.0],[0,-2.0],[0,-2.0],[0,-2.0],[0,-2.0]]
    for movie in moviedb:
        if moviedb.get(movie).getUserRating(user) != 0.0:
            continue
        else:
            newRating = 0.0
            commonRatings = 0
            neighbors = moviedb.get(movie).neighbors
            for each in neighbors:
                if moviedb.get(each[0]).getUserRating(user) is not 0.0:
                    newRating += each[1] * moviedb.get(each[0]).getUserRating(user)
                    commonRatings += each[1]
            if(abs(commonRatings) >= 0.00001):
                newRating = newRating / commonRatings #changed to divide by sum of weights rather than number of matched movies.
                #rated score has improved, but still doesn't seem to estimate an actual simulated rating.
            else:
                newRating = 0.0
            for each in recommendations:
                if newRating > each[1]:
                    each[0] = movie
                    each[1] = newRating
                    break
            recommendations.sort(key=lambda l:l[1])
    userrecommends[user] = recommendations

print("Saving movie recommendations for all users...")

#the following prints the recommendations ot a recommendation file by user id and movie title
recfile = "output.txt"
with open(recfile, "w") as text:
    text.write("Top 5 recommendations for each user follows: \n")
    for each in userrecommends:
        text.write("user " + str(each) + " ")
        for movie in userrecommends.get(each):
           text.write(str(moviedb.get(movie[0]).ID))
           text.write(" ")
        text.write("\n")
recfile = "recommended.txt"
with open(recfile, "w") as text:
    text.write("Top 5 recommendations for each user follows: \n")
    for each in userrecommends:
        text.write("user " + str(each) + " ")
        for movie in userrecommends.get(each):
           text.write(moviedb.get(movie[0]).name)
           text.write(" ")
        text.write("\n")
print("Done!")
sys.exit()