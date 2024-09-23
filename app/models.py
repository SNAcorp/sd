from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Submission(Base):
    __tablename__ = 'submissions'

    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    course = Column(Integer)
    direction = Column(String)
    telegram = Column(String)
