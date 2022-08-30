import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy_utils.types.color import ColorType


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
    author = Column(String(256), nullable=False)
    hex = Column(ColorType, nullable=False)
    name = Column(String(256))
    category = Column(Enum(ColorCategory))
    drawer = Column(Integer)
    location = Column(String(256))
    datetime = Column(DateTime)
    comment = Column(String(2048))


def init():
    global engine
    engine = create_engine('sqlite:///bojata.db', echo=True, future=True)
    Base.metadata.create_all(engine)


def persist(*objs):
    with Session(engine) as session:
        session.add_all(objs)
        session.commit()
