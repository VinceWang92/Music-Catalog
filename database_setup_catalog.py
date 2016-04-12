import os
import sys
import datetime
# include sqlalchemy
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

 
Base = declarative_base()

"""User class"""
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))

"""Genre class""" 
class Genre(Base):
    __tablename__ = 'genres'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship(User)
    
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
     

"""Song class""" 
class Song(Base):
    __tablename__ = 'songs'

    name =Column(String(255), nullable = False)
    id = Column(Integer, primary_key = True)
    url = Column(String(250))
    description = Column(String(250))
    artist = Column(String(250))
    genre_id = Column(Integer,ForeignKey('genres.id'))
    genre = relationship(Genre)
    owner_id = Column(Integer,ForeignKey('users.id'))
    owner = relationship(User)
    created = Column(DateTime, default = datetime.datetime.utcnow)
 
    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'description'         : self.description,
           'id'         : self.id,
           'url'        : self.url,
           'artist'        : self.artist,
           'created'         : self.created,
       }
engine = create_engine('sqlite:///catalogwithusers.db')
Base.metadata.create_all(engine)



