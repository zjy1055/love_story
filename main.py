import os
import sys
import threading
import time
import webbrowser
from subprocess import Popen
import shutil
from datetime import datetime

# 获取应用根目录
APP_ROOT = os.path.dirname(os.path.abspath(__file__))

# 判断是否在PyInstaller打包后的环境中
# _MEIPASS是PyInstaller创建的临时目录，用于存放应用资源
if hasattr(sys, '_MEIPASS'):
    # 在打包后的环境中，使用临时目录作为资源路径
    # cSpell:ignore MEIPASS  (PyInstaller临时目录属性)
    RESOURCES_PATH = sys._MEIPASS
else:
    # 在开发环境中，使用应用根目录作为资源路径
    RESOURCES_PATH = APP_ROOT

# 确保数据目录存在
def ensure_data_directory():
    data_dir = os.path.join(os.path.expanduser("~"), ".love_story_app")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

# 复制必要的文件到用户数据目录
def copy_required_files(data_dir):
    # 尝试复制数据库文件（如果存在）
    db_src = os.path.join(RESOURCES_PATH, "backend", "love_story.db")
    db_dst = os.path.join(data_dir, "love_story.db")
    if os.path.exists(db_src) and not os.path.exists(db_dst):
        try:
            shutil.copy2(db_src, db_dst)
            print(f"已从 {db_src} 复制数据库文件到 {db_dst}")
        except Exception as e:
            print(f"复制数据库文件时出错: {str(e)}")
    elif not os.path.exists(db_src):
        print(f"源数据库文件不存在: {db_src}，将在首次启动时创建新数据库")
    
    # 确保上传目录存在
    upload_dir = os.path.join(data_dir, "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # 确保备份目录存在
    backup_dir = os.path.join(data_dir, "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

# 初始化示例数据
def initialize_sample_data():
    # 检查是否已经初始化过示例数据
    data_dir = ensure_data_directory()
    db_path = os.path.join(data_dir, "love_story.db")
    init_flag_path = os.path.join(data_dir, ".sample_data_initialized")
    
    # 如果数据库文件存在但初始化标记不存在，运行初始化脚本
    if os.path.exists(db_path) and not os.path.exists(init_flag_path):
        print("正在初始化示例数据...")
        try:
            # 导入并运行初始化函数
            from init_sample_data import generate_sample_data
            generate_sample_data()
            # 创建初始化标记文件
            with open(init_flag_path, 'w') as f:
                f.write(datetime.now().isoformat())
            print("示例数据初始化完成")
        except Exception as e:
            print(f"初始化示例数据时出错: {str(e)}")

# 启动Flask服务器
def start_server():
    # 设置环境变量
    data_dir = ensure_data_directory()
    os.environ["LOVE_STORY_APP_DATA_DIR"] = data_dir
    
    # 确保backend目录在Python路径中
    backend_dir = os.path.join(RESOURCES_PATH, "backend")
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)
    
    # 初始化示例数据
    initialize_sample_data()
    
    # 正确导入Flask应用
    from backend.app import create_app
    app = create_app()
    app.run(host='localhost', port=5000, debug=False)

# 打开浏览器
def open_browser():
    # 等待服务器启动
    time.sleep(2)
    webbrowser.open('http://localhost:5000/')

# 主函数
def main():
    # 准备数据目录
    data_dir = ensure_data_directory()
    copy_required_files(data_dir)
    
    print("正在启动恋爱故事记录应用...")
    print(f"数据将存储在: {data_dir}")
    
    # 启动服务器线程
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # 打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.start()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("正在关闭应用...")
        sys.exit(0)

if __name__ == "__main__":
    main()