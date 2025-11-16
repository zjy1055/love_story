#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
恋爱故事记录应用 - API路由
"""

import os
import uuid
import shutil
from datetime import datetime, date

# 定义基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from backend.models import db, Event, Album, Photo, Tag, Config
from backend.utils import (
    process_uploaded_photo, allowed_file, generate_unique_filename,
    delete_photo_files, create_thumbnail, search_photos,
    ensure_upload_directory_exists, cleanup_old_backups, backup_database
)


def setup_routes(app):
    """设置所有API路由"""
    
    # 辅助函数：检查文件扩展名
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    
    # 辅助函数：生成照片URL
    def build_photo_url(photo_filename, is_thumbnail=False):
        if is_thumbnail:
            return f"/api/uploads/thumbnails/thumb_{photo_filename}"
        return f"/api/uploads/{photo_filename}"
    
    # 辅助函数：获取或创建标签
    def get_or_create_tag(tag_name):
        tag = Tag.query.filter_by(name=tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.session.add(tag)
        return tag
    
    # ===== 事件相关API =====
    
    @app.route('/api/events', methods=['GET'])
    def get_events():
        """获取事件列表，支持筛选和搜索"""
        # 获取查询参数
        filter_type = request.args.get('filter')
        search = request.args.get('search')
        limit = request.args.get('limit', type=int)
        
        # 基础查询
        query = Event.query
        
        # 筛选逻辑
        if filter_type == 'recent':
            # 最近添加的事件，按创建时间排序
            query = query.order_by(Event.created_at.desc())
        elif filter_type == 'future':
            # 未来事件，日期大于等于今天
            today = date.today()
            query = query.filter(Event.date >= today).order_by(Event.date.asc())
        else:
            # 默认按日期降序排序
            query = query.order_by(Event.date.desc())
        
        # 搜索功能
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Event.title.like(search_pattern)) |
                (Event.description.like(search_pattern))
            )
        
        # 限制返回数量
        if limit:
            events = query.limit(limit).all()
        else:
            events = query.all()
            
        return jsonify([event.to_dict() for event in events])
    
    @app.route('/api/events/<int:event_id>', methods=['GET'])
    def get_event(event_id):
        """获取单个事件详情"""
        event = Event.query.get_or_404(event_id)
        return jsonify(event.to_dict())
    
    @app.route('/api/events', methods=['POST'])
    def create_event():
        """创建新事件"""
        data = request.json
        try:
            event_date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else None
            event = Event(
                title=data['title'],
                date=event_date,
                description=data.get('description')
            )
            db.session.add(event)
            db.session.commit()
            return jsonify(event.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/events/<int:event_id>', methods=['PUT'])
    def update_event(event_id):
        """更新事件信息"""
        event = Event.query.get_or_404(event_id)
        data = request.json
        try:
            event.title = data.get('title', event.title)
            if data.get('date'):
                event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            event.description = data.get('description', event.description)
            db.session.commit()
            return jsonify(event.to_dict())
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/events/<int:event_id>', methods=['DELETE'])
    def delete_event(event_id):
        """删除事件"""
        event = Event.query.get_or_404(event_id)
        try:
            # 删除关联的照片文件
            for photo in event.photos:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            db.session.delete(event)
            db.session.commit()
            return jsonify({'message': '事件已删除'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    # ===== 照片相关API =====

    @app.route('/api/photos', methods=['GET'])
    def get_photos():
        """获取所有照片列表"""
        # 获取查询参数
        album_id = request.args.get('album_id', type=int)
        event_id = request.args.get('event_id', type=int)
        tag = request.args.get('tag')
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Photo.query
        
        # 按相册筛选
        if album_id:
            query = query.filter_by(album_id=album_id)
        
        # 按事件筛选
        if event_id:
            query = query.filter_by(event_id=event_id)
        
        # 按标签筛选
        if tag:
            query = query.join(Photo.tags).filter(Tag.name == tag)
        
        # 按日期范围筛选
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Photo.date_taken >= start)
            except ValueError:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Photo.date_taken <= end)
            except ValueError:
                pass
        
        # 搜索功能
        if search:
            # 搜索描述、原始名称和标签
            search_pattern = f"%{search}%"
            query = query.outerjoin(Photo.tags).filter(
                (Photo.description.like(search_pattern)) |
                (Photo.original_name.like(search_pattern)) |
                (Tag.name.like(search_pattern))
            ).distinct()
        
        # 按日期降序排序
        photos = query.order_by(Photo.created_at.desc()).all()
        
        # 转换为包含URL的字典列表
        result = []
        for photo in photos:
            photo_dict = photo.to_dict()
            photo_dict['url'] = build_photo_url(photo.filename)
            photo_dict['thumbnail_url'] = build_photo_url(photo.filename, is_thumbnail=True)
            
            # 添加相关的相册和事件信息
            if photo.album:
                photo_dict['album_info'] = {'id': photo.album.id, 'name': photo.album.name}
            if photo.event:
                photo_dict['event_info'] = {'id': photo.event.id, 'title': photo.event.title, 'date': photo.event.date.isoformat() if photo.event.date else None}
                
            result.append(photo_dict)
        
        return jsonify(result)
    
    @app.route('/api/photos/<int:photo_id>', methods=['GET'])
    def get_photo(photo_id):
        """获取单个照片详情"""
        photo = Photo.query.get_or_404(photo_id)
        photo_dict = photo.to_dict()
        photo_dict['url'] = build_photo_url(photo.filename)
        photo_dict['thumbnail_url'] = build_photo_url(photo.filename, is_thumbnail=True)
        
        # 添加相关的相册和事件信息
        if photo.album:
            photo_dict['album_info'] = {'id': photo.album.id, 'name': photo.album.name}
        if photo.event:
            photo_dict['event_info'] = {'id': photo.event.id, 'title': photo.event.title, 'date': photo.event.date.isoformat() if photo.event.date else None}
        
        return jsonify(photo_dict)
    
    @app.route('/api/photos', methods=['POST'])
    def upload_photo():
        """上传照片"""
        if 'file' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        try:
            # 验证文件类型
            if not allowed_file(file.filename):
                return jsonify({'error': '不支持的文件类型'}), 400
            
            # 确保上传目录存在
            upload_folder = app.config['UPLOAD_FOLDER']
            ensure_upload_directory_exists(app)
            
            # 处理上传的照片
            original_filename = secure_filename(file.filename)
            result = process_uploaded_photo(file, original_filename, upload_folder)
            
            # 创建照片记录
            photo = Photo(
                filename=result['filename'],
                original_name=result['original_name'],
                path=result['filename'],  # 存储相对路径
                description=request.form.get('description', ''),
                event_id=request.form.get('event_id', type=int),
                album_id=request.form.get('album_id', type=int)
            )
            
            # 处理日期
            if request.form.get('date_taken'):
                try:
                    photo.date_taken = datetime.strptime(request.form['date_taken'], '%Y-%m-%d').date()
                except ValueError:
                    pass
            
            # 处理标签
            tags_str = request.form.get('tags', '')
            if tags_str:
                tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                for tag_name in tags:
                    tag = get_or_create_tag(tag_name)
                    photo.tags.append(tag)
            
            db.session.add(photo)
            db.session.commit()
            
            # 返回包含URL的照片信息
            photo_dict = photo.to_dict()
            photo_dict['url'] = build_photo_url(photo.filename)
            photo_dict['thumbnail_url'] = build_photo_url(photo.filename, is_thumbnail=True)
            
            return jsonify(photo_dict), 201
            
        except Exception as e:
            db.session.rollback()
            # 如果有文件名，尝试删除已上传的文件
            if 'result' in locals() and 'filename' in result:
                delete_photo_files(result['filename'], upload_folder)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/photos/batch', methods=['POST'])
    def batch_upload_photos():
        """批量上传照片"""
        if 'files' not in request.files:
            return jsonify({'error': '没有文件上传'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': '没有选择文件'}), 400
        
        uploaded_photos = []
        errors = []
        
        try:
            # 确保上传目录存在
            upload_folder = app.config['UPLOAD_FOLDER']
            ensure_upload_directory_exists(app)
            
            for file in files:
                if file.filename == '':
                    continue
                
                # 验证文件类型
                if not allowed_file(file.filename):
                    errors.append({'filename': file.filename, 'error': '不支持的文件类型'})
                    continue
                
                try:
                    # 处理上传的照片
                    original_filename = secure_filename(file.filename)
                    result = process_uploaded_photo(file, original_filename, upload_folder)
                    
                    # 创建照片记录
                    photo = Photo(
                        filename=result['filename'],
                        original_name=result['original_name'],
                        path=result['filename'],  # 存储相对路径
                        description='',  # 批量上传时不设置描述
                        event_id=request.form.get('event_id', type=int),
                        album_id=request.form.get('album_id', type=int)
                    )
                    
                    db.session.add(photo)
                    
                    # 添加到上传成功列表
                    photo_dict = photo.to_dict()
                    photo_dict['url'] = build_photo_url(photo.filename)
                    photo_dict['thumbnail_url'] = build_photo_url(photo.filename, is_thumbnail=True)
                    uploaded_photos.append(photo_dict)
                    
                except Exception as e:
                    errors.append({'filename': file.filename, 'error': str(e)})
            
            # 提交数据库事务
            if uploaded_photos:
                db.session.commit()
            
            response = {
                'message': '批量上传完成',
                'success_count': len(uploaded_photos),
                'error_count': len(errors),
                'photos': uploaded_photos
            }
            
            if errors:
                response['errors'] = errors
                return jsonify(response), 207  # 207 Multi-Status
            
            return jsonify(response), 201
            
        except Exception as e:
            db.session.rollback()
            # 清理已上传的文件
            upload_folder = app.config['UPLOAD_FOLDER']
            for photo in uploaded_photos:
                delete_photo_files(photo['filename'], upload_folder)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/photos/search', methods=['GET'])
    def search_photos_route():
        """高级搜索照片"""
        query = request.args.get('q', '')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        tags = request.args.getlist('tag')
        album_id = request.args.get('album_id', type=int)
        event_id = request.args.get('event_id', type=int)
        
        # 处理日期范围
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '开始日期格式错误，应为YYYY-MM-DD'}), 400
        
        if date_to:
            try:
                parsed_date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '结束日期格式错误，应为YYYY-MM-DD'}), 400
        
        # 执行搜索
        try:
            # 注意：这里需要将db对象传递给search_photos函数
            photos = search_photos(
                db=db,
                query=query,
                date_from=parsed_date_from,
                date_to=parsed_date_to,
                tags=tags,
                album_id=album_id,
                event_id=event_id
            )
            
            # 转换为包含URL的字典列表
            result = []
            for photo in photos:
                photo_dict = photo.to_dict()
                photo_dict['url'] = build_photo_url(photo.filename)
                photo_dict['thumbnail_url'] = build_photo_url(photo.filename, is_thumbnail=True)
                
                # 添加相关信息
                if photo.album:
                    photo_dict['album_info'] = {'id': photo.album.id, 'name': photo.album.name}
                if photo.event:
                    photo_dict['event_info'] = {'id': photo.event.id, 'title': photo.event.title, 'date': photo.event.date.isoformat() if photo.event.date else None}
                
                result.append(photo_dict)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': '搜索失败: ' + str(e)}), 500
    
    @app.route('/api/photos/<int:photo_id>', methods=['PUT'])
    def update_photo(photo_id):
        """更新照片信息"""
        photo = Photo.query.get_or_404(photo_id)
        data = request.json
        try:
            # 更新描述
            if data.get('description') is not None:
                photo.description = data['description']
            
            # 更新日期
            if data.get('date_taken'):
                try:
                    photo.date_taken = datetime.strptime(data['date_taken'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': '无效的日期格式，请使用YYYY-MM-DD格式'}), 400
            
            # 更新关联
            if data.get('event_id') is not None:
                photo.event_id = data['event_id']
            if data.get('album_id') is not None:
                photo.album_id = data['album_id']
            
            # 更新标签
            if 'tags' in data:
                photo.tags = []
                if data['tags']:
                    for tag_name in data['tags']:
                        if tag_name and isinstance(tag_name, str):
                            tag = get_or_create_tag(tag_name.strip())
                            photo.tags.append(tag)
            
            db.session.commit()
            
            # 返回包含URL的照片信息
            photo_dict = photo.to_dict()
            photo_dict['url'] = build_photo_url(photo.filename)
            photo_dict['thumbnail_url'] = build_photo_url(photo.filename, is_thumbnail=True)
            
            return jsonify(photo_dict)
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    @app.route('/api/photos/<int:photo_id>', methods=['DELETE'])
    def delete_photo(photo_id):
        """删除照片"""
        photo = Photo.query.get_or_404(photo_id)
        filename = photo.filename
        
        try:
            # 从数据库中删除
            db.session.delete(photo)
            db.session.commit()
            
            # 删除文件（包括缩略图）
            delete_photo_files(filename, app.config['UPLOAD_FOLDER'])
            
            return jsonify({'message': '照片已删除'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/uploads/<filename>')
    def serve_photo(filename):
        """提供照片文件访问"""
        # 安全检查：确保文件名不包含路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件路径'}), 400
        
        # 检查文件是否存在
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '文件不存在'}), 404
        
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    @app.route('/api/uploads/thumbnails/<filename>')
    def serve_thumbnail(filename):
        """提供缩略图文件访问"""
        # 安全检查：确保文件名不包含路径遍历攻击
        if '..' in filename or filename.startswith('/'):
            return jsonify({'error': '无效的文件路径'}), 400
        
        # 检查缩略图是否存在
        thumb_path = os.path.join(app.config['THUMBNAILS_FOLDER'], filename)
        if not os.path.exists(thumb_path):
            # 如果缩略图不存在，尝试创建
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(original_path):
                try:
                    create_thumbnail(original_path, thumb_path)
                except Exception:
                    # 如果创建失败，返回原始图片
                    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
            else:
                return jsonify({'error': '文件不存在'}), 404
        
        return send_from_directory(app.config['THUMBNAILS_FOLDER'], filename)
    
    # ===== 相册相关API =====
    
    @app.route('/api/albums', methods=['GET'])
    def get_albums():
        """获取所有相册列表"""
        albums = Album.query.all()
        return jsonify([album.to_dict() for album in albums])
    
    @app.route('/api/albums/<int:album_id>', methods=['GET'])
    def get_album(album_id):
        """获取单个相册详情"""
        album = Album.query.get_or_404(album_id)
        return jsonify(album.to_dict())
    
    @app.route('/api/albums', methods=['POST'])
    def create_album():
        """创建新相册"""
        data = request.json
        album = Album(
            name=data['name'],
            description=data.get('description')
        )
        db.session.add(album)
        db.session.commit()
        return jsonify(album.to_dict()), 201
    
    @app.route('/api/albums/<int:album_id>', methods=['PUT'])
    def update_album(album_id):
        """更新相册信息"""
        album = Album.query.get_or_404(album_id)
        data = request.json
        album.name = data.get('name', album.name)
        album.description = data.get('description', album.description)
        db.session.commit()
        return jsonify(album.to_dict())
    
    @app.route('/api/albums/<int:album_id>', methods=['DELETE'])
    def delete_album(album_id):
        """删除相册"""
        album = Album.query.get_or_404(album_id)
        try:
            # 删除关联的照片文件
            for photo in album.photos:
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            db.session.delete(album)
            db.session.commit()
            return jsonify({'message': '相册已删除'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    # ===== 标签相关API =====
    
    @app.route('/api/tags', methods=['GET'])
    def get_tags():
        """获取所有标签列表"""
        tags = Tag.query.all()
        return jsonify([tag.to_dict() for tag in tags])
    
    # ===== 配置相关API =====
    
    @app.route('/api/configs', methods=['GET'])
    def get_configs():
        """获取所有配置信息"""
        configs = Config.query.all()
        return jsonify([config.to_dict() for config in configs])
    
    @app.route('/api/configs/<string:key>', methods=['GET'])
    def get_config(key):
        """获取单个配置信息"""
        # 首先记录请求日志
        app.logger.info(f"Request for config key: {key}")
        
        try:
            # 查询配置项
            config = Config.query.filter_by(key=key).first()
            
            # 检查配置项是否存在
            if config is None:
                app.logger.warning(f"Config key not found: {key}")
                return jsonify({'error': 'Configuration not found'}), 404
            
            # 尝试转换为字典并返回
            try:
                config_dict = config.to_dict()
                return jsonify(config_dict), 200
            except Exception as to_dict_error:
                app.logger.error(f"Error converting config {key} to dict: {str(to_dict_error)}")
                return jsonify({'error': 'Failed to process configuration data'}), 500
        except Exception as e:
            # 捕获所有其他异常
            app.logger.error(f"Unexpected error getting config {key}: {str(e)}")
            return jsonify({'error': 'An unexpected server error occurred'}), 500
    
    @app.route('/api/configs/<string:key>', methods=['PUT'])
    def update_config(key):
        """更新配置信息，如果配置不存在则创建新的配置项"""
        try:
            data = request.json
            if not data or 'value' not in data:
                return jsonify({'error': 'Invalid request data'}), 400
            
            # 获取要保存的值
            value = data['value']
            
            # 特殊处理轮播图配置项
            # 对于carousel_items，确保值是字符串格式的JSON
            if key == 'carousel_items':
                import json
                # 如果值已经是对象或数组，转换为JSON字符串
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                # 如果已经是JSON字符串，保持原样
                elif isinstance(value, str) and (
                    (value.startswith('{') and value.endswith('}')) or
                    (value.startswith('[') and value.endswith(']'))
                ):
                    # 验证是否为有效的JSON
                    try:
                        json.loads(value)
                    except json.JSONDecodeError:
                        return jsonify({'error': 'Invalid JSON format for carousel_items'}), 400
            
            # 查找配置项
            config = Config.query.filter_by(key=key).first()
            
            # 如果不存在，创建新的配置项
            if not config:
                config = Config(key=key, value=value)
                db.session.add(config)
            else:
                # 更新现有配置
                config.value = value
            
            # 保存更改
            db.session.commit()
            
            return jsonify(config.to_dict()), 200
        except Exception as e:
            app.logger.error(f"Error updating config {key}: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Internal Server Error'}), 500
    
    # ===== 数据备份与恢复API =====
    
    @app.route('/api/backup', methods=['POST'])
    def backup_data():
        """备份数据库和照片"""
        try:
            # 生成备份文件名（使用时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 获取正确的数据目录路径
            # 确保使用绝对路径
            upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
            backup_dir = os.path.abspath(os.path.join(upload_folder, '..', 'data', 'backups'))
            
            # 确保备份目录存在
            print(f"创建备份目录: {backup_dir}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # 可能的数据库位置列表
            # 优先使用用户主目录下的.love_story_app文件夹，这是应用实际使用的数据存储位置
            possible_db_paths = [
                # 1. 从环境变量获取数据目录（应用实际使用的路径）
                os.path.abspath(os.path.join(os.environ.get('LOVE_STORY_APP_DATA_DIR', os.path.join(os.path.expanduser('~'), '.love_story_app')), 'love_story.db')),
                # 2. 从用户主目录直接计算的路径
                os.path.abspath(os.path.join(os.path.expanduser('~'), '.love_story_app', 'love_story.db')),
                # 3. 从上传目录计算的路径
                os.path.abspath(os.path.join(upload_folder, '..', 'data', 'love_story.db')),
                # 4. 从BASE_DIR计算的路径
                os.path.abspath(os.path.join(BASE_DIR, 'data', 'love_story.db')),
                # 5. 当前工作目录下的data目录
                os.path.abspath(os.path.join(os.getcwd(), 'data', 'love_story.db')),
                # 6. 项目根目录下的data目录
                os.path.abspath(os.path.join(BASE_DIR, '..', 'data', 'love_story.db')),
                # 7. 直接在UPLOAD_FOLDER中查找
                os.path.abspath(os.path.join(upload_folder, 'love_story.db'))
            ]
            
            # 查找实际的数据库文件
            db_path = None
            for possible_path in possible_db_paths:
                if os.path.exists(possible_path):
                    db_path = possible_path
                    print(f"找到数据库文件: {db_path}")
                    break
            
            # 如果找不到数据库文件，创建一个空的数据库文件
            if not db_path:
                print("未找到数据库文件，将创建一个新的空数据库文件")
                # 使用第一个可能的路径作为默认位置
                default_db_path = possible_db_paths[0]
                # 确保目录存在
                os.makedirs(os.path.dirname(default_db_path), exist_ok=True)
                # 创建空文件
                with open(default_db_path, 'w') as f:
                    pass
                db_path = default_db_path
                print(f"创建了空数据库文件: {db_path}")
            
            # 使用utils中的backup_database函数来备份数据库
            print(f"使用backup_database函数备份数据库: {db_path} -> {backup_dir}")
            backup_db_path = backup_database(db_path, backup_dir)
            
            # 如果备份失败，使用fallback方式
            if not backup_db_path:
                backup_db_path = os.path.join(backup_dir, f'love_story_{timestamp}.db')
                print(f"使用fallback方式备份数据库: {db_path} -> {backup_db_path}")
                shutil.copy2(db_path, backup_db_path)
            
            # 获取备份文件信息
            backup_info = {
                'filename': os.path.basename(backup_db_path),
                'size': os.path.getsize(backup_db_path),
                'created_at': datetime.now().isoformat()
            }
            
            # 清理旧备份，保留最新的30个
            print(f"清理旧备份，保留最新的30个")
            cleanup_old_backups(backup_dir, max_backups=30)
            
            return jsonify({'message': '数据备份成功', 'backup_file': backup_info}), 200
        except Exception as e:
            print(f"备份失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backups', methods=['GET'])
    def get_backups():
        """获取备份文件列表"""
        try:
            # 获取正确的备份目录路径，与backup_data函数保持一致
            # 优先使用用户主目录下的.love_story_app文件夹，这是应用实际使用的数据存储位置
            upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
            # 优先使用用户主目录下的备份目录
            backup_dir = os.path.abspath(os.path.join(os.environ.get('LOVE_STORY_APP_DATA_DIR', os.path.join(os.path.expanduser('~'), '.love_story_app')), 'data', 'backups'))
            
            # 检查备份目录是否存在
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
                return jsonify({'backups': []}), 200
            
            # 获取所有备份文件
            backup_files = []
            for filename in os.listdir(backup_dir):
                # 同时支持两种备份文件名格式：database_backup_和love_story_
                if (filename.startswith('database_backup_') or filename.startswith('love_story_')) and filename.endswith('.db'):
                    file_path = os.path.join(backup_dir, filename)
                    backup_files.append({
                        'filename': filename,
                        'size': os.path.getsize(file_path),
                        'created_at': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                        'modified_at': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
            
            # 按修改时间降序排序（最新的在前）
            backup_files.sort(key=lambda x: x['modified_at'], reverse=True)
            
            return jsonify({'backups': backup_files}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/backup/<filename>', methods=['DELETE'])
    def delete_backup(filename):
        """删除指定的备份文件"""
        try:
            # 获取正确的备份目录路径，与get_backups函数保持一致
            backup_dir = os.path.abspath(os.path.join(os.environ.get('LOVE_STORY_APP_DATA_DIR', os.path.join(os.path.expanduser('~'), '.love_story_app')), 'data', 'backups'))
            backup_path = os.path.join(backup_dir, filename)
            
            if not os.path.exists(backup_path):
                return jsonify({'error': '备份文件不存在'}), 404
            
            # 验证文件名格式，同时支持两种备份文件名格式：database_backup_和love_story_
            if not ((filename.startswith('database_backup_') or filename.startswith('love_story_')) and filename.endswith('.db')):
                return jsonify({'error': '无效的备份文件名'}), 400
            
            # 删除备份文件
            os.remove(backup_path)
            
            return jsonify({'message': '备份文件已删除'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # 清理旧备份API已移除，系统自动最多保存100个备份
    
    @app.route('/api/restore/<filename>', methods=['POST'])
    def restore_data(filename):
        """恢复数据库"""
        try:
            # 获取正确的备份目录路径，与get_backups函数保持一致
            backup_dir = os.path.abspath(os.path.join(os.environ.get('LOVE_STORY_APP_DATA_DIR', os.path.join(os.path.expanduser('~'), '.love_story_app')), 'data', 'backups'))
            backup_path = os.path.join(backup_dir, filename)
            
            if not os.path.exists(backup_path):
                return jsonify({'error': '备份文件不存在'}), 404
            
            # 验证文件名格式，同时支持两种备份文件名格式：database_backup_和love_story_
            if not ((filename.startswith('database_backup_') or filename.startswith('love_story_')) and filename.endswith('.db')):
                return jsonify({'error': '无效的备份文件名'}), 400
            
            # 获取正确的数据库路径，与backup_data函数保持一致
            db_path = os.path.abspath(os.path.join(os.environ.get('LOVE_STORY_APP_DATA_DIR', os.path.join(os.path.expanduser('~'), '.love_story_app')), 'love_story.db'))
            
            # 关闭数据库连接后恢复
            shutil.copy2(backup_path, db_path)
            
            return jsonify({'message': '数据恢复成功'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500