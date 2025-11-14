#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
恋爱故事记录应用 - 数据库模型
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

# 创建SQLAlchemy实例
db = SQLAlchemy()


class Event(db.Model):
    """事件记录模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联的照片
    photos = relationship('Photo', backref='event', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'title': self.title,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'photos': [photo.to_dict() for photo in self.photos]
        }


class Album(db.Model):
    """相册模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联的照片
    photos = relationship('Photo', backref='album', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'photo_count': len(self.photos)
        }


class Photo(db.Model):
    """照片模型"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date_taken = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 外键关联
    event_id = db.Column(db.Integer, ForeignKey('event.id'), nullable=True)
    album_id = db.Column(db.Integer, ForeignKey('album.id'), nullable=True)
    
    # 多对多关系 - 照片和标签
    tags = relationship('Tag', secondary='photo_tags', back_populates='photos')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_name': self.original_name,
            'path': self.path,
            'description': self.description,
            'date_taken': self.date_taken.strftime('%Y-%m-%d') if self.date_taken else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'event_id': self.event_id,
            'album_id': self.album_id,
            'tags': [tag.name for tag in self.tags]
        }


class Tag(db.Model):
    """标签模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # 多对多关系 - 标签和照片
    photos = relationship('Photo', secondary='photo_tags', back_populates='tags')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name
        }


class Config(db.Model):
    """配置信息模型"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# 多对多关系表 - 照片和标签
photo_tags = db.Table('photo_tags',
    db.Column('photo_id', db.Integer, ForeignKey('photo.id'), primary_key=True),
    db.Column('tag_id', db.Integer, ForeignKey('tag.id'), primary_key=True)
)


def init_db():
    """初始化数据库"""
    db.create_all()
    
    # 添加默认配置
    default_configs = [
        {'key': 'first_meeting_date', 'value': '', 'description': '第一次见面日期，格式：YYYY-MM-DD'},
        {'key': 'relationship_date', 'value': '', 'description': '确定关系日期，格式：YYYY-MM-DD'},
        {'key': 'motto', 'value': '爱是永恒的', 'description': '个人格言或爱情宣言'},
        {'key': 'rules', 'value': '相互理解\n相互尊重\n相互信任', 'description': '相处守则'},
        {'key': 'values', 'value': '真诚\n包容\n成长', 'description': '共同价值观'},
        {'key': 'carousel_image_url', 'value': '', 'description': '轮播图图片URL'},
        {'key': 'carousel_title', 'value': '我们的故事', 'description': '轮播图标题'},
        {'key': 'carousel_subtitle', 'value': '珍藏每一个美好的瞬间', 'description': '轮播图副标题'}
    ]
    
    for config_data in default_configs:
        config = Config.query.filter_by(key=config_data['key']).first()
        if not config:
            config = Config(**config_data)
            db.session.add(config)
    
    db.session.commit()