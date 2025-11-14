#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清空恋爱故事记录应用数据库的工具脚本
此脚本将删除所有用户数据（事件、照片、相册、标签等），但保留默认配置
"""

import os
import sys

# 获取应用根目录
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

def ensure_data_directory():
    """确保数据目录存在并返回路径"""
    data_dir = os.path.join(os.path.expanduser("~"), ".love_story_app")
    if not os.path.exists(data_dir):
        print(f"错误：数据目录不存在: {data_dir}")
        sys.exit(1)
    return data_dir

def clear_database():
    """清空数据库中的用户数据"""
    # 设置数据目录环境变量
    data_dir = ensure_data_directory()
    os.environ["LOVE_STORY_APP_DATA_DIR"] = data_dir
    
    # 添加backend目录到Python路径
    backend_dir = os.path.join(APP_ROOT, "backend")
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    
    try:
        # 导入必要的模块
        from backend.app import create_app
        from backend.models import db, Event, Album, Photo, Tag, photo_tags
        
        # 创建Flask应用实例
        app = create_app()
        
        with app.app_context():
            print("开始清空数据库...")
            
            # 先删除关联表中的数据
            db.session.execute(photo_tags.delete())
            
            # 删除各模型数据（按外键依赖顺序）
            print("删除照片数据...")
            Photo.query.delete()
            
            print("删除事件数据...")
            Event.query.delete()
            
            print("删除相册数据...")
            Album.query.delete()
            
            print("删除标签数据...")
            Tag.query.delete()
            
            # 提交事务
            db.session.commit()
            print("数据库清空成功！")
            print("注意：默认配置已保留")
            
    except Exception as e:
        print(f"清空数据库时出错: {e}")
        sys.exit(1)

def confirm_action():
    """确认用户是否要清空数据库"""
    print("⚠️  警告：此操作将清空所有用户数据（事件、照片、相册等）")
    print("但会保留默认配置。此操作不可撤销！")
    
    # 如果有--force参数，则直接返回True
    if '--force' in sys.argv:
        print("使用--force参数，自动确认操作")
        return True
    
    return False

if __name__ == "__main__":
    if confirm_action():
        clear_database()
    else:
        print("操作已取消。如果您确定要清空数据库，请使用以下命令:")
        print("python clear_database.py --force")
        sys.exit(0)