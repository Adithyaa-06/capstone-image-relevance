from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True)
    subject = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    attributes = Column(Text, nullable=False)
    caption = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    flagged = Column(Boolean, default=False, index=True)
    flagged_reason = Column(Text, nullable=True)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    suggestions = relationship("Suggestion", back_populates="image")
    cost_logs = relationship("CostLog", back_populates="image")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    suggestions = relationship("Suggestion", back_populates="post")
    cost_logs = relationship("CostLog", back_populates="post")

class Suggestion(Base):
    __tablename__ = "suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)
    guard_decision = Column(String(50), nullable=False)
    guard_reason = Column(Text, nullable=False)
    status = Column(String(50), default="pending", index=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="suggestions")
    image = relationship("Image", back_populates="suggestions")
    
    __table_args__ = (
        Index("ix_suggestions_post_score", "post_id", "similarity_score"),
    )

class CostLog(Base):
    __tablename__ = "cost_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(255), unique=True, index=True)
    call_type = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    cost_usd = Column(Float, nullable=False)
    status = Column(String(50), default="success")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    image = relationship("Image", back_populates="cost_logs")
    post = relationship("Post", back_populates="cost_logs")

class EvalSet(Base):
    __tablename__ = "eval_set"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), unique=True, nullable=False, index=True)
    correct_image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)