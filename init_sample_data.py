# -*- coding: utf-8 -*-

"""
恋爱故事记录应用 - 示例数据初始化脚本
用于生成初始的示例数据，丰富用户初次使用体验
"""

import os
import sys
from datetime import datetime, timedelta
import random

# 获取应用根目录
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# 添加backend目录到Python路径
sys.path.append(APP_ROOT)

# 导入必要的模块
from backend.app import create_app
from backend.models import db, Event, Album, Config

def generate_sample_data():
    """生成示例数据"""
    # 创建Flask应用实例
    app = create_app()
    
    with app.app_context():
        # 检查是否已有数据
        if Event.query.first() or Album.query.count() > 0:
            print("数据库中已有数据，跳过示例数据初始化")
            return
        
        print("开始生成示例数据...")
        
        # 更新默认配置
        update_default_configs()
        
        # 创建示例事件
        create_sample_events()
        
        # 创建示例相册
        create_sample_albums()
        
        print("示例数据生成完成！")

def update_default_configs():
    """更新默认配置项"""
    # 设置一些有意义的默认值
    config_updates = [
        {'key': 'first_meeting_date', 'value': (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'), 
         'description': '第一次见面日期，格式：YYYY-MM-DD'},
        {'key': 'relationship_date', 'value': (datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d'), 
         'description': '确定关系日期，格式：YYYY-MM-DD'},
        {'key': 'motto', 'value': '爱是永恒的，爱是耐心的，爱是善良的', 
         'description': '个人格言或爱情宣言'},
        {'key': 'rules', 'value': '相互理解\n相互尊重\n相互信任\n共同成长', 
         'description': '相处守则'},
        {'key': 'values', 'value': '真诚\n包容\n成长\n陪伴', 
         'description': '共同价值观'},
        {'key': 'carousel_title', 'value': '我们的美好回忆', 
         'description': '轮播图标题'},
        {'key': 'carousel_subtitle', 'value': '记录每一个值得珍藏的瞬间', 
         'description': '轮播图副标题'}
    ]
    
    for config_data in config_updates:
        config = Config.query.filter_by(key=config_data['key']).first()
        if config:
            config.value = config_data['value']
            config.description = config_data['description']
        else:
            config = Config(**config_data)
            db.session.add(config)
    
    db.session.commit()
    print("已更新默认配置项")

def create_sample_events():
    """创建示例事件"""
    # 示例事件数据
    events_data = [
        {
            'title': '第一次约会',
            'date': datetime.now() - timedelta(days=180),
            'description': '我们在咖啡店第一次正式见面，聊了整整一下午，感觉时间过得特别快。那天阳光很好，就像我们的心情一样。'
        },
        {
            'title': '一起看电影',
            'date': datetime.now() - timedelta(days=170),
            'description': '第一次一起看电影，选了一部浪漫的爱情片。电影很感人，但更让我感动的是身边有你的陪伴。'
        },
        {
            'title': '确定关系',
            'date': datetime.now() - timedelta(days=150),
            'description': '今天是特别的一天，我们正式确定了恋爱关系。在公园的长椅上，我们许下了对彼此的承诺。'
        },
        {
            'title': '第一次旅行',
            'date': datetime.now() - timedelta(days=120),
            'description': '我们一起去了海边旅行，看日出日落，捡贝壳，在沙滩上写下我们的名字。这是我最美好的回忆之一。'
        },
        {
            'title': '庆祝一百天',
            'date': datetime.now() - timedelta(days=50),
            'description': '在一起一百天了，时间过得真快！我们做了一顿烛光晚餐，交换了小礼物，许下了下一个一百天的约定。'
        }
    ]
    
    for event_data in events_data:
        event = Event(**event_data)
        db.session.add(event)
    
    db.session.commit()
    print(f"已创建 {len(events_data)} 个示例事件")

def create_sample_albums():
    """创建示例相册"""
    # 示例相册数据
    albums_data = [
        {
            'name': '初次相遇',
            'description': '记录我们第一次见面的美好时光'
        },
        {
            'name': '甜蜜约会',
            'description': '那些浪漫的约会瞬间'
        },
        {
            'name': '旅行记忆',
            'description': '我们一起走过的地方'
        },
        {
            'name': '节日庆祝',
            'description': '一起度过的特别节日'
        }
    ]
    
    for album_data in albums_data:
        album = Album(**album_data)
        db.session.add(album)
    
    db.session.commit()
    print(f"已创建 {len(albums_data)} 个示例相册")

if __name__ == '__main__':
    print("初始化示例数据...")
    generate_sample_data()
    print("示例数据初始化完成！")