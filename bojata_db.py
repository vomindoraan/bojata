import enum
from datetime import datetime

import pandas as pd
from sqlalchemy import Column, Engine, Enum, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, validates
from sqlalchemy.dialects.sqlite import DATETIME


DB_URL = 'sqlite:///data/bojata.db'

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DateTime = DATETIME(
    storage_format='%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d',
)

# Globals
engine:      Engine
initialized: bool   = False


class Base(DeclarativeBase):
    pass


class LabelsMeta(type(Base)):
    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        cls.__labels__ = {c.name: c.doc for c in cls.__table__.columns if c.doc}

    def label_of(cls, column: str | Column | Mapped, annotated=True):
        col = getattr(column, 'name', column)
        label = cls.__labels__[col]
        if label and annotated:
            label = label.upper()
            if not cls.__table__.columns[col].nullable:
                label += " ⁽*⁾"
        return label


class ColorCategory(enum.Enum):
    YELLOW      = "Žuta"
    ORANGE      = "Narandžasta"
    RED         = "Crvena"
    PINK        = "Roze"
    LIGHT_GREEN = "Svetlozelena"
    DARK_GREEN  = "Tamnozelena"
    LIGHT_BLUE  = "Svetloplava"
    DARK_BLUE   = "Tamnoplava"
    BROWN       = "Braon"
    BLACK       = "Crna"
    OTHER       = "Ostalo"


class Color(Base, metaclass=LabelsMeta):
    __tablename__ = 'color'

    id       = Column(Integer,     primary_key=True)
    author   = Column(String(50),  nullable=False,   doc="Autor")
    hex      = Column(String(7),   nullable=False,   doc="Boja")
    name     = Column(String(50),                    doc="Naziv boje")
    category = Column(Enum(ColorCategory),           doc="Kategorija boje")
    object   = Column(String(50),                    doc="Skenirani predmet / Broj kasete")
    comment  = Column(String(250),                   doc="Komentar")
    location = Column(String(72),  nullable=False,   doc="Mesto")
    datetime = Column(DateTime,    nullable=False,   doc="Datum i vreme")


    @classmethod
    def read_data(cls, column_mapping=None):
        if column_mapping is None:
            column_mapping = cls.__labels__
        columns = column_mapping.keys()
        df = pd.read_sql_table(cls.__tablename__, engine,
                               columns=columns, parse_dates=['datetime'])
        df.rename(columns=column_mapping, inplace=True)
        return df

    @classmethod
    def empty_data(cls, column_mapping=None):
        if column_mapping is None:
            column_mapping = cls.__labels__
        return pd.DataFrame(columns=column_mapping.values())

    @validates('datetime')
    def validate_datetime(self, key, value):
        return datetime.strptime(value, DATETIME_FORMAT)


def init():
    global engine
    engine = create_engine(DB_URL, echo=True)
    Base.metadata.create_all(engine)

    global initialized
    initialized = True


def persist(*objs):
    with Session(engine) as session:
        session.add_all(objs)
        session.commit()
