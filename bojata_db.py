import enum

import pandas
from sqlalchemy import Column, DateTime, Enum, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session


Base = declarative_base()
engine = None


class ColorCategory(enum.Enum):
    YELLOW = "Žuta"
    ORANGE = "Narandžasta"
    RED = "Crvena"
    PINK = "Roze"
    LIGHT_GREEN = "Svetlozelena"
    DARK_GREEN = "Tamnozelena"
    LIGHT_BLUE = "Svetloplava"
    DARK_BLUE = "Tamnoplava"
    BROWN = "Braon"
    BLACK = "Crna"
    OTHER = "Ostalo"


class Color(Base):
    __tablename__ = 'color'

    id = Column(Integer, primary_key=True)
    author = Column(String(50), nullable=False)
    hex = Column(String(7), nullable=False)
    name = Column(String(50))
    category = Column(Enum(ColorCategory))
    drawer = Column(Integer)
    comment = Column(String(250))
    location = Column(String(72))
    datetime = Column(String(20), nullable=False)

    @classmethod
    def read_data(cls):
        return pandas.read_sql_table(cls.__tablename__, engine,
                                     parse_dates=['datetime'])


def init():
    global engine
    engine = create_engine('sqlite:///bojata.db', echo=True)
    Base.metadata.create_all(engine)


def persist(*objs):
    with Session(engine) as session:
        session.add_all(objs)
        session.commit()
