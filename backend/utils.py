import os
import uuid
import datetime
import shutil
from PIL import Image
from flask import current_app

# 从环境变量获取数据目录，默认为当前目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get('LOVE_STORY_APP_DATA_DIR', BASE_DIR)

# 照片存储路径管理函数
def ensure_upload_directory_exists(app=None):
    """
    确保上传目录存在，如果不存在则创建
    """
    if app is None:
        app = current_app
    
    # 确保uploads目录存在
    uploads_dir = app.config['UPLOAD_FOLDER']
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # 确保缩略图目录存在
    thumbnails_dir = os.path.join(uploads_dir, 'thumbnails')
    if not os.path.exists(thumbnails_dir):
        os.makedirs(thumbnails_dir)
    
    return uploads_dir

# 生成唯一的文件名
def generate_unique_filename(original_filename):
    """
    生成唯一的文件名，避免文件名冲突
    """
    # 获取文件扩展名
    file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    
    # 生成唯一ID和时间戳
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 组合新文件名
    if file_extension:
        return f"{timestamp}_{unique_id}.{file_extension}"
    else:
        return f"{timestamp}_{unique_id}"

# 验证上传的文件
def allowed_file(filename):
    """
    检查文件类型是否允许上传
    """
    # 允许的图片文件类型
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 处理上传的照片
def process_uploaded_photo(file, original_filename, upload_folder):
    """
    处理上传的照片，包括重命名、保存和生成缩略图
    """
    # 生成唯一文件名
    filename = generate_unique_filename(original_filename)
    
    # 保存原始图片路径
    file_path = os.path.join(upload_folder, filename)
    
    # 保存文件
    file.save(file_path)
    
    # 生成缩略图
    thumbnail_path = create_thumbnail(file_path, upload_folder)
    
    return {
        'filename': filename,
        'original_name': original_filename,
        'file_path': file_path,
        'thumbnail_path': thumbnail_path
    }

# 创建缩略图
def create_thumbnail(image_path, upload_folder):
    """
    为图片创建缩略图
    """
    # 缩略图大小
    thumbnail_size = (300, 200)
    
    # 缩略图保存路径
    thumbnails_dir = os.path.join(upload_folder, 'thumbnails')
    if not os.path.exists(thumbnails_dir):
        os.makedirs(thumbnails_dir)
    
    # 文件名
    filename = os.path.basename(image_path)
    thumbnail_path = os.path.join(thumbnails_dir, f"thumb_{filename}")
    
    try:
        # 打开图片
        with Image.open(image_path) as img:
            # 创建缩略图（保持宽高比）
            img.thumbnail(thumbnail_size)
            
            # 保存缩略图
            img.save(thumbnail_path)
            
            return thumbnail_path
    except Exception as e:
        # 如果缩略图创建失败，返回None
        print(f"创建缩略图失败: {e}")
        return None

# 删除照片文件
def delete_photo_files(filename, upload_folder):
    """
    删除照片及其缩略图
    """
    try:
        # 删除原始图片
        original_path = os.path.join(upload_folder, filename)
        if os.path.exists(original_path):
            os.remove(original_path)
        
        # 删除缩略图
        thumbnail_path = os.path.join(upload_folder, 'thumbnails', f"thumb_{filename}")
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
            
        return True
    except Exception as e:
        print(f"删除照片文件失败: {e}")
        return False

# 清理照片目录中的孤立文件
def cleanup_orphaned_photos(db, upload_folder):
    """
    清理数据库中不存在的照片文件
    """
    from models import Photo  # 避免循环导入
    
    try:
        # 获取数据库中已有的所有文件名
        photos = db.session.query(Photo).all()
        db_filenames = {photo.filename for photo in photos}
        
        # 遍历上传目录
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            
            # 跳过目录
            if os.path.isdir(file_path):
                continue
                
            # 如果文件不在数据库中，则删除
            if filename not in db_filenames:
                os.remove(file_path)
                print(f"已删除孤立文件: {filename}")
        
        # 同样检查缩略图目录
        thumbnails_dir = os.path.join(upload_folder, 'thumbnails')
        if os.path.exists(thumbnails_dir):
            for filename in os.listdir(thumbnails_dir):
                # 提取原始文件名（去掉thumb_前缀）
                if filename.startswith('thumb_'):
                    original_filename = filename[6:]  # 去掉"thumb_"前缀
                    
                    # 如果原始文件名不在数据库中，则删除缩略图
                    if original_filename not in db_filenames:
                        os.remove(os.path.join(thumbnails_dir, filename))
                        print(f"已删除孤立缩略图: {filename}")
        
        return True
    except Exception as e:
        print(f"清理孤立照片失败: {e}")
        return False

# 批量处理照片
def batch_process_photos(files, upload_folder):
    """
    批量处理多张照片
    """
    results = []
    errors = []
    
    for file in files:
        if not allowed_file(file.filename):
            errors.append(f"不支持的文件类型: {file.filename}")
            continue
        
        try:
            result = process_uploaded_photo(file, file.filename, upload_folder)
            results.append(result)
        except Exception as e:
            errors.append(f"处理文件失败 {file.filename}: {str(e)}")
    
    return {
        'success': results,
        'errors': errors
    }

# 生成照片访问URL
def generate_photo_url(filename, app=None):
    """
    生成照片的访问URL
    """
    if app is None:
        app = current_app
    
    # 在实际部署中，这里可能需要考虑使用CDN或其他URL生成方式
    # 此处使用相对路径
    return f"/api/uploads/{filename}"

# 生成缩略图URL
def generate_thumbnail_url(filename, app=None):
    """
    生成缩略图的访问URL
    """
    if app is None:
        app = current_app
    
    return f"/api/uploads/thumbnails/thumb_{filename}"

# 验证照片访问权限
def validate_photo_access(user_id, photo_path, app=None):
    """
    验证用户是否有权限访问照片（此处为简化版本，实际应用可能需要更复杂的权限验证）
    """
    # 在单机应用中，假设所有照片都可以访问
    # 在多用户环境中，这里需要根据用户ID和照片所有权进行验证
    return True

# 检查上传文件夹大小
def check_upload_folder_size(upload_folder):
    """
    检查上传文件夹的大小
    """
    total_size = 0
    
    for dirpath, dirnames, filenames in os.walk(upload_folder):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
    
    return total_size

# 格式化文件大小显示
def format_file_size(size_in_bytes):
    """
    将字节大小格式化为人类可读的格式
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    
    return f"{size_in_bytes:.2f} TB"

# 数据库备份函数
def backup_database(db_path, backup_dir):
    """
    备份数据库文件
    """
    # 确保备份目录存在
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 生成备份文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"database_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # 复制数据库文件
        shutil.copy2(db_path, backup_path)
        return backup_path
    except Exception as e:
        print(f"数据库备份失败: {e}")
        return None

# 恢复数据库函数
def restore_database(backup_path, db_path):
    """
    从备份文件恢复数据库
    """
    # 检查备份文件是否存在
    if not os.path.exists(backup_path):
        return False, "备份文件不存在"
    
    try:
        # 复制备份文件到数据库位置
        shutil.copy2(backup_path, db_path)
        return True, "数据库恢复成功"
    except Exception as e:
        print(f"数据库恢复失败: {e}")
        return False, f"恢复失败: {str(e)}"

# 清理旧备份文件
def cleanup_old_backups(backup_dir, max_backups=100):
    """
    清理旧的备份文件，保留最新的max_backups个
    返回删除的文件数量
    """
    if not os.path.exists(backup_dir):
        return 0
    
    # 获取所有备份文件（匹配love_story_开头的备份）
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('love_story_') and f.endswith('.db')]
    
    # 如果没有找到新命名规则的备份，尝试使用旧命名规则
    if not backup_files:
        backup_files = [f for f in os.listdir(backup_dir) if f.startswith('database_backup_') and f.endswith('.db')]
    
    # 按修改时间排序（最新的在前）
    backup_files.sort(key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
    
    # 记录删除的文件数量
    deleted_count = 0
    
    # 删除超出数量限制的旧备份
    for file_to_delete in backup_files[max_backups:]:
        try:
            os.remove(os.path.join(backup_dir, file_to_delete))
            deleted_count += 1
            print(f"已删除旧备份: {file_to_delete}")
        except Exception as e:
            print(f"删除备份 {file_to_delete} 失败: {e}")
    
    return deleted_count

# 解析标签字符串
def parse_tags(tag_string):
    """
    解析标签字符串，返回标签列表
    支持用逗号、空格或分号分隔的标签
    """
    if not tag_string:
        return []
    
    # 分割标签（支持多种分隔符）
    tags = []
    for separator in [',', ';', '\n']:
        if separator in tag_string:
            tags = tag_string.split(separator)
            break
    
    # 如果没有找到分隔符，则按空格分割
    if not tags:
        tags = tag_string.split()
    
    # 清理每个标签并移除空标签
    cleaned_tags = [tag.strip() for tag in tags if tag.strip()]
    
    # 去重
    return list(set(cleaned_tags))

# 搜索照片
def search_photos(db, query='', date_from=None, date_to=None, tags=None, album_id=None, event_id=None):
    """
    搜索照片
    
    参数:
    - db: 数据库会话对象
    - query: 搜索关键词
    - date_from: 开始日期
    - date_to: 结束日期
    - tags: 标签列表
    - album_id: 相册ID
    - event_id: 事件ID
    """
    from models import Photo, Tag  # 避免循环导入
    
    # 构建基础查询
    q = db.session.query(Photo)
    
    # 按相册筛选
    if album_id:
        q = q.filter(Photo.album_id == album_id)
    
    # 按事件筛选
    if event_id:
        q = q.filter(Photo.event_id == event_id)
    
    # 按日期范围筛选
    if date_from:
        q = q.filter(Photo.date_taken >= date_from)
    
    if date_to:
        q = q.filter(Photo.date_taken <= date_to)
    
    # 按标签筛选
    if tags and isinstance(tags, list) and tags:
        # 确保只有非空标签被使用
        valid_tags = [tag.strip() for tag in tags if tag and tag.strip()]
        if valid_tags:
            # 使用JOIN和IN条件筛选带有指定标签的照片
            q = q.join(Photo.tags).filter(Tag.name.in_(valid_tags)).distinct()
    
    # 按关键词搜索（在描述和原始名称中搜索）
    if query:
        # 确保字符串类型并去除首尾空格
        search_pattern = f"%{str(query).strip()}%"
        q = q.filter(
            (Photo.description.like(search_pattern)) |
            (Photo.original_name.like(search_pattern)) |
            (Photo.filename.like(search_pattern))  # 增加对filename的搜索
        )
    
    # 按日期降序排序（最新的在前）
    q = q.order_by(Photo.date_taken.desc())
    
    return q.all()