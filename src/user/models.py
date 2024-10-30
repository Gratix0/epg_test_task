from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    first_name = Column(String, nullable=False, index=True)
    last_name = Column(String, nullable=False, index=True)
    pic_url = Column(String, nullable=True)

    matches_sent = relationship("Match", foreign_keys="Match.user_id", back_populates="user")
    matches_received = relationship("Match", foreign_keys="Match.matched_user_id", back_populates="matched_user")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    matched_user_id = Column(Integer, ForeignKey("users.id"))
    is_match = Column(Boolean, default=False)  # If i`ts a match

    user = relationship("Users", foreign_keys=[user_id], back_populates="matches_sent")
    matched_user = relationship("Users", foreign_keys=[matched_user_id], back_populates="matches_received")