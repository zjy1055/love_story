#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
恋爱故事记录应用 - Flask后端主应用
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from backend.models import db, init_db
from backend.routes import setup_routes
import re


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__, static_folder='../frontend', static_url_path='/')
    
    # 配置应用
    basedir = os.path.abspath(os.path.dirname(__file__))
    # 从环境变量获取数据目录，默认为原始路径
    data_dir = os.environ.get('LOVE_STORY_APP_DATA_DIR', os.path.join(basedir, '..', 'data'))
    uploads_dir = os.environ.get('LOVE_STORY_APP_UPLOADS_DIR', os.path.join(data_dir, 'uploads'))
    thumbnails_dir = os.path.join(uploads_dir, 'thumbnails')
    
    # 确保数据目录和上传目录存在
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(thumbnails_dir, exist_ok=True)
    
    # 设置应用配置
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "love_story.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = uploads_dir
    app.config['THUMBNAILS_FOLDER'] = thumbnails_dir
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
    
    # 允许的图片扩展名
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 初始化数据库
    db.init_app(app)
    with app.app_context():
        init_db()
    
    # 启用CORS
    CORS(app)
    
    # 设置路由
    setup_routes(app)
    
    # 上传文件的静态文件服务
    @app.route('/api/uploads/<path:filename>')
    def serve_uploads(filename):
        # 安全检查：确保请求的文件位于上传目录内
        safe_path = os.path.normpath(filename)
        if '..' in safe_path:
            return jsonify({'error': 'Invalid filename'}), 400
        
        try:
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        except Exception as e:
            return jsonify({'error': 'File not found'}), 404
    
    # 缩略图服务
    @app.route('/api/uploads/thumbnails/<path:filename>')
    def serve_thumbnails(filename):
        # 安全检查
        safe_path = os.path.normpath(filename)
        if '..' in safe_path:
            return jsonify({'error': 'Invalid filename'}), 400
        
        try:
            return send_from_directory(app.config['THUMBNAILS_FOLDER'], filename)
        except Exception as e:
            return jsonify({'error': 'Thumbnail not found'}), 404
    
    # 健康检查端点
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'app': 'Love Story App'})
    
    # 静态文件路由
    @app.route('/')
    def serve_index():
        return send_from_directory(app.static_folder, 'index.html')
    
    # 处理根路径下的图片请求，支持直接访问上传的图片文件
    @app.route('/<string:filename>')
    def serve_root_images(filename):
        # 检查文件名是否为图片格式
        if re.match(r'^\w+\.(jpg|jpeg|png|gif|webp)$', filename):
            # 检查文件是否存在于上传目录
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
            # 如果文件不存在，返回404而不是500错误
            return jsonify({'error': 'Image not found'}), 404
        # 如果不是图片，继续到下一个路由处理
        return serve_any(filename)

    # 处理所有其他路由，用于前端SPA
    @app.route('/<path:path>')
    def serve_any(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    # 413处理（文件过大）
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large', 'max_size': '16MB'}), 413
    
    # 异常处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        # 记录错误
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
    
    return app