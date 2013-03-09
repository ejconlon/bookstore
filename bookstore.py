#!/usr/bin/env python

import json
from bottle import *

books = {}
idSource = 0

def makeBook(**kwargs):
  global idSource
  bookId = idSource
  idSource += 1
  kwargs["_href"] = "/books/"+str(bookId)
  kwargs["_model"] = "book"
  return bookId, kwargs

@error(404)
def my404(e):
  return sendError(404, "Not found") 

def sendError(code, message):
  response.content_type = 'application/json'
  response.status = code 
  return json.dumps({ "_model": "error", 'code': code, 'message': message})

@get('/books')
def listBooks():
  return {"_model": "collection", "_href": "/books", "items": books.values()}

@get('/books/<bookId:int>')
def getBook(bookId):
  if (bookId in books):
    return books[bookId]
  else:
    return sendError(404, "Book not found: "+str(bookId))

@delete('/books/<bookId:int>')
def deleteBook(bookId):
  _ = getBook(bookId)
  logBooks()
  del books[bookId]

@put('/books/<bookId:int>')
def updateBook(bookId):
  book = getBook(bookId)
  if (request.content_type != "application/json"):
    return sendError(406, "Need json content type")
  for key in request.json.keys():
    if key.startswith("_"):
      continue
    elif key not in book:
      return sendError(409, "Bad property: "+str(key))
    else:
      book[key] = request.json.get(key)
  logBooks()
  return book

@post('/books')
def createBook():
  i, b = makeBook(**request.forms)
  books[i] = b
  logBooks()
  redirect(b["href"])

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
