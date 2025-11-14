# 恋爱故事记录应用 - 开发文档

## 目录

1. [项目架构](#项目架构)
2. [数据库设计](#数据库设计)
3. [API接口](#api接口)
4. [前端实现](#前端实现)
5. [照片处理](#照片处理)
6. [数据备份机制](#数据备份机制)
7. [应用打包](#应用打包)
8. [开发指南](#开发指南)

## 项目架构

本项目采用前后端分离的架构：

- **后端**：基于 Flask 的 RESTful API 服务
- **前端**：纯 HTML/CSS/JavaScript 实现的单页应用
- **数据库**：SQLite 轻量级数据库
- **文件存储**：本地文件系统

### 技术栈

- **后端**：
  - Python 3.6+
  - Flask 2.0.1
  - Flask-CORS 3.0.10
  - SQLite (内置)
  - Pillow 8.3.1 (图像处理)

- **前端**：
  - HTML5
  - CSS3
  - JavaScript (ES6+)

- **构建工具**：
  - PyInstaller 4.5.1 (打包为可执行文件)

## 数据库设计

### 主要表结构

#### 1. events (事件表)

| 字段名 | 数据类型 | 描述 |
|--------|----------|------|
| id | INTEGER | 事件ID (主键) |
| title | TEXT | 事件标题 |
| date | DATE | 事件日期 |
| description | TEXT | 事件描述 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### 2. albums (相册表)

| 字段名 | 数据类型 | 描述 |
|--------|----------|------|
| id | INTEGER | 相册ID (主键) |
| name | TEXT | 相册名称 |
| created_at | TIMESTAMP | 创建时间 |

#### 3. photos (照片表)

| 字段名 | 数据类型 | 描述 |
|--------|----------|------|
| id | INTEGER | 照片ID (主键) |
| filename | TEXT | 文件名 |
| description | TEXT | 照片描述 |
| album_id | INTEGER | 所属相册ID (外键) |
| event_id | INTEGER | 关联事件ID (外键) |
| tags | TEXT | 标签 (逗号分隔) |
| upload_date | TIMESTAMP | 上传时间 |

#### 4. config (配置表)

| 字段名 | 数据类型 | 描述 |
|--------|----------|------|
| id | INTEGER | 配置ID (主键) |
| key | TEXT | 配置键 |
| value | TEXT | 配置值 |
| updated_at | TIMESTAMP | 更新时间 |

## API接口

### 基础URL

所有API接口都以 `/api/` 开头。

### 事件相关接口

#### 1. 获取所有事件

```
GET /api/events
```

**查询参数**：
- `search`: 可选，搜索关键词

**返回**：事件列表的JSON数组

#### 2. 获取单个事件

```
GET /api/events/<event_id>
```

**返回**：单个事件的JSON对象

#### 3. 创建事件

```
POST /api/events
```

**请求体**：
```json
{
  "title": "事件标题",
  "date": "YYYY-MM-DD",
  "description": "事件描述"
}
```

**返回**：创建的事件JSON对象

#### 4. 更新事件

```
PUT /api/events/<event_id>
```

**请求体**：
```json
{
  "title": "新标题",
  "date": "YYYY-MM-DD",
  "description": "新描述"
}
```

**返回**：更新后的事件JSON对象

#### 5. 删除事件

```
DELETE /api/events/<event_id>
```

**返回**：成功状态的JSON对象

### 照片相关接口

#### 1. 获取照片列表

```
GET /api/photos
```

**查询参数**：
- `search`: 可选，搜索关键词
- `album_id`: 可选，相册ID
- `event_id`: 可选，事件ID

**返回**：照片列表的JSON数组

#### 2. 获取单个照片

```
GET /api/photos/<photo_id>
```

**返回**：单个照片的JSON对象

#### 3. 上传照片

```
POST /api/photos
```

**请求体**：multipart/form-data
- `file`: 照片文件
- `description`: 照片描述
- `album_id`: 相册ID (可选)
- `event_id`: 事件ID (可选)
- `tags`: 标签 (可选，逗号分隔)

**返回**：上传的照片JSON对象

#### 4. 批量上传照片

```
POST /api/photos/batch
```

**请求体**：multipart/form-data
- `files[]`: 多张照片文件
- `album_id`: 相册ID (可选)
- `event_id`: 事件ID (可选)
- `tags`: 标签 (可选，逗号分隔)

**返回**：上传结果的JSON对象

#### 5. 更新照片

```
PUT /api/photos/<photo_id>
```

**请求体**：
```json
{
  "description": "新描述",
  "album_id": 1,
  "event_id": 2,
  "tags": "标签1,标签2"
}
```

**返回**：更新后的照片JSON对象

#### 6. 删除照片

```
DELETE /api/photos/<photo_id>
```

**返回**：成功状态的JSON对象

#### 7. 高级照片搜索

```
GET /api/photos/search
```

**查询参数**：
- `keyword`: 搜索关键词
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `album_id`: 相册ID
- `event_id`: 事件ID
- `tags`: 标签 (逗号分隔)

**返回**：搜索结果的JSON数组

### 相册相关接口

#### 1. 获取所有相册

```
GET /api/albums
```

**返回**：相册列表的JSON数组

#### 2. 创建相册

```
POST /api/albums
```

**请求体**：
```json
{
  "name": "相册名称"
}
```

**返回**：创建的相册JSON对象

### 配置相关接口

#### 1. 获取配置

```
GET /api/config
```

**返回**：配置的JSON对象

#### 2. 更新配置

```
PUT /api/config
```

**请求体**：
```json
{
  "anniversary_date": "YYYY-MM-DD",
  "anniversary_name": "纪念日名称",
  "motto": "个人格言",
  "rules": "相处守则"
}
```

**返回**：更新后的配置JSON对象

### 数据备份相关接口

#### 1. 创建备份

```
POST /api/backup
```

**返回**：备份结果的JSON对象

#### 2. 恢复数据

```
POST /api/restore
```

**请求体**：multipart/form-data
- `file`: 备份文件

**返回**：恢复结果的JSON对象

#### 3. 获取备份列表

```
GET /api/backups
```

**返回**：备份列表的JSON数组

#### 4. 删除备份

```
DELETE /api/backups/<backup_filename>
```

**返回**：删除结果的JSON对象

#### 5. 清理旧备份

```
POST /api/backups/cleanup
```

**返回**：清理结果的JSON对象

## 前端实现

前端采用单页应用设计，所有功能都在一个HTML页面中实现，通过JavaScript实现页面切换和交互。

### 主要功能模块

1. **导航系统**：在不同功能页面间切换
2. **首页模块**：显示照片轮播、倒计时和格言
3. **事件管理模块**：CRUD操作和搜索功能
4. **照片管理模块**：上传、查看、编辑和搜索照片
5. **配置模块**：设置纪念日、格言等
6. **备份恢复模块**：数据备份与恢复操作

### 核心JavaScript函数

#### 1. 页面导航

- `loadPage(pageName)`: 加载指定页面内容
- `showModal(modalId)`: 显示模态框
- `hideModal()`: 隐藏模态框

#### 2. 数据加载

- `loadEvents()`: 加载事件列表
- `loadPhotos()`: 加载照片列表
- `loadAlbums()`: 加载相册列表
- `loadConfig()`: 加载配置信息
- `loadBackupList()`: 加载备份列表

#### 3. 数据操作

- `saveEvent()`: 保存事件
- `deleteEvent()`: 删除事件
- `uploadPhoto()`: 上传照片
- `batchUploadPhotos()`: 批量上传照片
- `backupData()`: 备份数据
- `restoreData()`: 恢复数据

#### 4. 辅助功能

- `showNotification()`: 显示通知消息
- `debounce()`: 防抖函数
- `formatDate()`: 格式化日期
- `formatFileSize()`: 格式化文件大小

## 照片处理

### 上传处理流程

1. 接收上传的照片文件
2. 验证文件类型和大小
3. 生成唯一文件名
4. 创建缩略图
5. 保存文件到磁盘
6. 记录到数据库

### 缩略图生成

缩略图生成使用Pillow库：

```python
def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    with Image.open(image_path) as img:
        img.thumbnail(size)
        img.save(thumbnail_path)
```

## 数据备份机制

### 备份流程

1. 创建临时目录
2. 复制数据库文件到临时目录
3. 复制上传的照片文件到临时目录
4. 将临时目录压缩为ZIP文件
5. 保存ZIP文件到备份目录

### 恢复流程

1. 接收上传的备份文件
2. 解压到临时目录
3. 替换当前数据库文件
4. 复制照片文件到上传目录

### 自动清理

系统支持自动清理超过指定天数的旧备份：

```python
def cleanup_old_backups(days_to_keep=30):
    # 获取当前时间
    now = datetime.now()
    # 计算保留时间
    keep_time = now - timedelta(days=days_to_keep)
    # 删除过期备份
    deleted_count = 0
    for filename in os.listdir(BACKUP_FOLDER):
        file_path = os.path.join(BACKUP_FOLDER, filename)
        if os.path.isfile(file_path):
            # 检查文件修改时间
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < keep_time:
                os.remove(file_path)
                deleted_count += 1
    return deleted_count
```

## 应用打包

### 打包配置

项目使用PyInstaller进行打包，配置文件为`love_story.spec`：

- 单文件模式 (`--onefile`)
- 窗口模式 (`--windowed`)
- 包含前后端资源文件
- 自定义图标

### 打包流程

1. 运行 `build.bat` 脚本
2. 脚本会自动安装依赖并执行PyInstaller
3. 打包完成后，可执行文件位于 `dist/` 目录

## 开发指南

### 环境搭建

1. 克隆代码仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 运行开发服务器：`python main.py`

### 代码规范

- 后端使用PEP 8代码规范
- 前端使用ES6+语法
- 所有函数和类需要添加注释
- 提交代码前运行代码检查

### 调试技巧

1. 启用Flask调试模式：在开发时设置 `debug=True`
2. 使用浏览器开发者工具调试前端
3. 检查控制台输出和网络请求

### 扩展建议

1. 添加用户认证系统
2. 实现云存储支持
3. 添加社交分享功能
4. 增加数据同步到多设备的功能
5. 开发移动应用版本