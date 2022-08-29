import enum

from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils.types.color import ColorType


Base = declarative_base()


class ColorCategory(enum.Enum):
    WARM = "Топла"
    COLD = "Хладна"
    NEUTRAL = "Неутрална"
    # TODO: Add more categories


class Color(Base):
    __tablename__ = 'color'

    id = Column(Integer, primary_key=True)
    hex = Column(ColorType, nullable=False)
    name = Column(String(256), nullable=False)
    author = Column(String(256), nullable=False)
    category = Column(Enum(ColorCategory))
    comment = Column(String(2048))
