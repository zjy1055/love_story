#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
恋爱故事记录应用 - 主程序入口
"""

import os
import sys
from backend.app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 获取端口号，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 检查是否为打包后的应用
    if hasattr(sys, '_MEIPASS'):
        # 打包模式下使用相对路径
        static_folder = os.path.join(sys._MEIPASS, 'frontend')
        app.static_folder = static_folder
        app.static_url_path = '/static'
    
    print("恋爱故事记录应用启动中...")
    print(f"请在浏览器中访问 http://localhost:{port}")
    
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=False)