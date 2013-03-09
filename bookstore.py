#!/usr/bin/env python

import json
from datetime import datetime
import random
import string
import copy
from bottle import *

books = {}
tokens = set(["hack"])
idSource = 0

def jsonNow():
  return datetime.now().isoformat()

def makeLink(rel, href, method, consumes=None, produces=None):
  link = {"rel": rel, "href": href, "method": method}
  if consumes is not None:
    link["consumes"] = consumes
  if produces is not None:
    link["produces"] = produces
  return link

def makeBook(**kwargs):
  global idSource
  bookId = idSource
  idSource += 1
  kwargs["_model"] = "book"
  kwargs["_modified"] = jsonNow()
  return bookId, kwargs

def addBookLinks(bookId, book):
  book = copy.deepcopy(book)
  links = []
  links.append(makeLink("self", "/books/"+str(bookId), "GET", produces="book"))
  links.append(makeLink("update", "/books/"+str(bookId), "PUT", consumes="book", produces="book"))
  links.append(makeLink("delete", "/books/"+str(bookId), "DELETE"))
  book["_links"] = links
  return book

@error(404)
def my404(e):
  return sendError(404, "Not found") 
@error(405)
def my405(e):
  return sendError(405, "Method not allowed") 

def sendError(code, message):
  response.content_type = 'application/json'
  response.status = code 
  return json.dumps({ "_model": "error", 'code': code, 'message': message})

def getToken(request):
  if 'X-Bookstore-Token' in request.headers:
    return request.headers['X-Bookstore-Token']
  else:
    return None

@get('/')
def getRoot():
  token = getToken(request)
  if token in tokens:
    return {"_links": [makeLink("books", "/books", "GET", produces="collection")]}
  else:
    return {"_links": [makeLink("login", "/login", "POST", consumes="credentials")]}

@post('/login')
def login():
  if type(request.json) == dict and \
       request.json['username'] == "foo" and \
       request.json['password'] == "bar":
    token = "".join(random.choice(string.ascii_lowercase) for i in xrange(4))
    tokens.add(token)
    response.headers['X-Bookstore-Token'] = token
    response.headers['Location'] = '/'
    response.status = 303
    response.content_type = "application/json"
  else:
    return sendError(401, "Unauthorized: POST with username and password.")

def makeColl(bookKeys, href):
  items = [makeLink("item", "/books/"+str(i), "GET", produces="book") for i in bookKeys]
  coll = {"_model": "collection", "items": items}
  links = []
  links.append(makeLink("self", href, "GET", produces="collection"))
  for otherRel, otherHref in [('unsorted', '/books'), ('newest', '/books?newest'), ('oldest', '/books?oldest')]:
    if href != otherHref:
      links.append(makeLink(otherRel, otherHref, "GET", produces="collection"))
  coll["_links"] = links
  return coll

@get('/books')
def listBooks():
  sortBooks = lambda books: [x for (x, y) in sorted(books.iteritems(), key=lambda (k, v): v["_modified"])]
  if 'newest' in request.GET:
    return makeColl(reversed(sortBooks(books)), '/books?newest')
  elif 'oldest' in request.GET:
    return makeColl(sortBooks(books), '/books?oldest')
  else:
    return makeColl(books.keys(), '/books')

@get('/books/<bookId:int>')
def getBook(bookId):
  if (bookId in books):
    return addBookLinks(bookId, books[bookId])
  else:
    return sendError(404, "Book not found: "+str(bookId))

@delete('/books/<bookId:int>')
def deleteBook(bookId):
  if (bookId not in books):
    return sendError(404, "Book not found: "+str(bookId))
  del books[bookId]
  logBooks()

@put('/books/<bookId:int>')
def updateBook(bookId):
  if (bookId not in books):
    return sendError(404, "Book not found: "+str(bookId))
  if (request.content_type != "application/json"):
    return sendError(406, "Need json content type")
  book = books[bookId]
  for key in request.json.keys():
    if key.startswith("_"):
      continue
    else:
      book[key] = request.json.get(key)
  book["_modified"] = jsonNow()
  logBooks()
  return addBookLinks(bookId, book)

@post('/books')
def createBook():
  i, b = makeBook(**request.forms)
  books[i] = b
  logBooks()
  redirect("/books/"+str(i))

def logBooks():
  print "Books: ", books

def initBooks():
  temp = [makeBook(title="Moby Dick", author="Herman Melville"),
          makeBook(title="Wide Sargasso Sea", author="Jean Rhys")]
  for i, b in temp:
    books[i] = b
  logBooks()

def main():
  initBooks()
  run(host='localhost', port=8080, debug=True)

if __name__ == "__main__":
  main()
