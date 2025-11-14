// 全局变量
let currentPage = 'home';
let currentPhotos = [];
let currentPhotoIndex = 0;

// DOM 加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    // 初始化导航
    initNavigation();
    
    // 初始化模态框
    initModals();
    
    // 初始化事件监听
    initEventListeners();
    
    // 加载首页数据
    loadHomePageData();
});

// 初始化导航
function initNavigation() {
    // 页面导航
    document.querySelectorAll('.menu-item, .mobile-menu-item').forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-target');
            navigateTo(target);
            
            // 关闭移动端菜单
            document.querySelector('.mobile-menu').classList.remove('open');
        });
    });
    
    // 移动端菜单切换
    document.querySelector('.navbar-toggle').addEventListener('click', function() {
        document.querySelector('.mobile-menu').classList.toggle('open');
    });
    
    document.querySelector('.mobile-menu-close').addEventListener('click', function() {
        document.querySelector('.mobile-menu').classList.remove('open');
    });
}

// 页面导航函数
function navigateTo(pageId) {
    // 隐藏当前页面
    document.getElementById(currentPage).classList.remove('active');
    document.querySelector(`[data-target="${currentPage}"]`).classList.remove('active');
    
    // 显示目标页面
    document.getElementById(pageId).classList.add('active');
    document.querySelector(`[data-target="${pageId}"]`).classList.add('active');
    
    // 更新当前页面
    currentPage = pageId;
    
    // 根据页面加载对应数据
    switch(pageId) {
        case 'home':
            loadHomePageData();
            break;
        case 'events':
            loadEvents();
            break;
        case 'photos':
            loadPhotos();
            loadAlbums();
            break;
        case 'config':
            loadConfig();
            // 加载备份列表
            loadBackupList();
            break;
    }
}

// 初始化模态框
function initModals() {
    // 获取所有模态框
    const modals = document.querySelectorAll('.modal');
    
    // 添加关闭事件
    document.querySelectorAll('.modal-close, .modal-cancel').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.classList.remove('active');
            resetModalForms();
        });
    });
    
    // 点击模态框外部关闭
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('active');
                resetModalForms();
            }
        });
    });
    
    // 阻止事件冒泡
    document.querySelectorAll('.modal-content').forEach(content => {
        content.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
}

// 重置模态框表单
function resetModalForms() {
    // 重置事件表单
    document.getElementById('event-id').value = '';
    document.getElementById('event-title').value = '';
    document.getElementById('event-date').value = '';
    document.getElementById('event-description').value = '';
    document.getElementById('event-modal-title').textContent = '添加事件';
    
    // 重置照片表单
    document.getElementById('photo-file').value = '';
    document.getElementById('photo-description').value = '';
    document.getElementById('photo-date').value = '';
    document.getElementById('photo-album').value = '';
    document.getElementById('photo-event').value = '';
    document.getElementById('photo-tags').value = '';
    
    // 重置相册表单
    document.getElementById('album-name').value = '';
    document.getElementById('album-description').value = '';
}

// 初始化事件监听器
function initEventListeners() {
    // 事件页面按钮
    document.getElementById('add-event-btn').addEventListener('click', function() {
        document.getElementById('event-modal').classList.add('active');
    });
    
    document.getElementById('save-event').addEventListener('click', saveEvent);
    
    // 照片页面按钮
    document.getElementById('upload-photo-btn').addEventListener('click', function() {
        document.getElementById('photo-modal').classList.add('active');
        loadEventsForDropdown();
        loadAlbumsForDropdown();
    });
    
    document.getElementById('upload-photo').addEventListener('click', uploadPhoto);
    
    // 相册按钮
    document.getElementById('create-album-btn').addEventListener('click', function() {
        document.getElementById('album-modal').classList.add('active');
    });
    
    document.getElementById('create-album').addEventListener('click', createAlbum);
    
    // 设置页面按钮
    document.getElementById('save-settings').addEventListener('click', saveSettings);
    document.getElementById('backup-btn').addEventListener('click', backupData);
    document.getElementById('restore-btn').addEventListener('click', function() {
        document.getElementById('restore-file').click();
    });
    
    document.getElementById('restore-file').addEventListener('change', restoreData);
    
    // 添加清理旧备份按钮的事件监听器
    // 清理旧备份功能已移除，系统自动最多保存100个备份
    
    // 事件搜索和筛选
    document.getElementById('event-search').addEventListener('input', debounce(loadEvents, 300));
    document.getElementById('event-filter').addEventListener('change', loadEvents);
    
    // 照片查看器导航
    document.getElementById('prev-photo').addEventListener('click', showPreviousPhoto);
    document.getElementById('next-photo').addEventListener('click', showNextPhoto);
    document.getElementById('delete-photo').addEventListener('click', deleteCurrentPhoto);
    
    // 照片搜索
    const quickSearchInput = document.getElementById('photo-quick-search');
    if (quickSearchInput) {
        quickSearchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                const activeAlbum = document.querySelector('.album-btn.active')?.getAttribute('data-album') || 'all';
                loadPhotos(activeAlbum, this.value.trim());
            }
        });
    }
    
    // 设置批量上传和照片搜索功能
    setupBatchUpload();
    setupPhotoSearch();
    
    // 轮播图图片上传功能
    const uploadButton = document.getElementById('upload-carousel-image');
    const fileInput = document.getElementById('carousel_image_file');
    const urlInput = document.getElementById('carousel_image_url');
    
    if (uploadButton && fileInput && urlInput) {
        uploadButton.addEventListener('click', function() {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const formData = new FormData();
                formData.append('file', file);
                
                showLoader();
                
                // 上传图片
                fetch('/api/photos', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) throw new Error('上传失败');
                    return response.json();
                })
                .then(data => {
                    // 更新URL输入框
                    urlInput.value = data.url;
                    showNotification('图片上传成功', 'success');
                })
                .catch(error => {
                    showNotification('图片上传失败: ' + error.message, 'error');
                })
                .finally(() => {
                    hideLoader();
                    // 重置文件输入
                    this.value = '';
                });
            }
        });
    }
}

// 加载首页数据
// 全局轮播图数据和状态
let carouselItems = [];
let currentSlideIndex = 0;
let carouselInterval;

function loadHomePageData() {
    // 加载配置信息
    fetch('/api/configs')
        .then(response => response.json())
        .then(configs => {
            // 创建配置映射
            const configMap = {};
            configs.forEach(config => {
                configMap[config.key] = config.value;
            });
            
            // 更新爱情宣言等内容
            document.getElementById('motto').textContent = configMap.motto || '爱是永恒的';
            document.getElementById('values').textContent = configMap.values || '真诚\n包容\n成长';
            document.getElementById('rules').textContent = configMap.rules || '相互理解\n相互尊重\n相互信任';
            
            // 初始化轮播图数据
            carouselItems = [];
            
            try {
                // 尝试从JSON格式的carousel_items配置中加载多张轮播图
                if (configMap.carousel_items && configMap.carousel_items.trim()) {
                    carouselItems = JSON.parse(configMap.carousel_items);
                }
            } catch (e) {
                console.error('解析轮播图数据失败:', e);
                // 如果解析失败，尝试使用旧格式的单个轮播图配置
                if (configMap.carousel_image_url) {
                    carouselItems.push({
                        id: Date.now().toString(),
                        image_url: configMap.carousel_image_url,
                        title: configMap.carousel_title || '我们的故事',
                        subtitle: configMap.carousel_subtitle || '珍藏每一个美好的瞬间'
                    });
                }
            }
            
            // 如果没有轮播图数据，创建默认轮播图
            if (carouselItems.length === 0) {
                carouselItems.push({
                    id: Date.now().toString(),
                    image_url: 'https://picsum.photos/1200/600?random=1',
                    title: '我们的故事',
                    subtitle: '珍藏每一个美好的瞬间'
                });
            }
            
            // 渲染轮播图
            renderCarousel();
            
            // 初始化轮播图控制
            initCarouselControls();
            
            // 计算倒计时
            if (configMap.relationship_date) {
                updateCountdown('relationship', configMap.relationship_date);
            }
            
            if (configMap.first_meeting_date) {
                updateCountdown('meeting', configMap.first_meeting_date);
            }
        })
        .catch(error => showNotification('加载配置失败', 'error'));
    
    // 加载最近事件
    fetch('/api/events?limit=3')
        .then(response => response.json())
        .then(events => {
            const eventsGrid = document.getElementById('recent-events-grid');
            eventsGrid.innerHTML = '';
            
            if (events.length === 0) {
                eventsGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-calendar-alt"></i>
                        <p>还没有记录任何事件</p>
                    </div>
                `;
                return;
            }
            
            events.slice(0, 3).forEach(event => {
                const eventDate = new Date(event.date);
                const eventCard = document.createElement('div');
                eventCard.className = 'event-card';
                eventCard.innerHTML = `
                    <div class="event-card-date">
                        ${eventDate.getMonth() + 1}月${eventDate.getDate()}日
                    </div>
                    <div class="event-card-content">
                        <h4 class="event-card-title">${event.title}</h4>
                        <p class="event-card-description">${event.description || ''}</p>
                    </div>
                `;
                
                // 添加点击事件
                eventCard.addEventListener('click', function() {
                    navigateTo('events');
                    // 可以添加滚动到该事件的逻辑
                });
                
                eventsGrid.appendChild(eventCard);
            });
        })
        .catch(error => showNotification('加载事件失败', 'error'));
    
    // 加载精选照片 - 优化版
    fetch('/api/photos?limit=6')
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应异常');
            }
            return response.json();
        })
        .then(photos => {
            const photosGrid = document.getElementById('featured-photos-grid');
            
            // 清除现有内容
            photosGrid.innerHTML = '';
            
            // 处理无照片情况
            if (!photos || photos.length === 0) {
                photosGrid.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-image"></i>
                        <p>还没有上传任何照片</p>
                        <button class="btn btn-primary" onclick="navigateTo('photos')">
                            去上传照片
                        </button>
                    </div>
                `;
                return;
            }
            
            // 优化照片显示逻辑
            const displayPhotos = photos.slice(0, 6);
            displayPhotos.forEach(photo => {
                const photoCard = document.createElement('div');
                photoCard.className = 'photo-card fade-in';
                
                // 构建照片卡片内容
                const imagePath = photo.path || `/api/uploads/${photo.filename}`;
                const imageAlt = photo.description || photo.original_name || '照片';
                const photoDate = photo.date ? formatDate(photo.date) : '';
                
                photoCard.innerHTML = `
                    <div class="photo-thumbnail">
                        <img src="${imagePath}" alt="${imageAlt}" loading="lazy">
                        <div class="photo-overlay">
                            <span class="photo-description">${photo.description || ''}</span>
                            ${photoDate ? `<span class="photo-date">${photoDate}</span>` : ''}
                        </div>
                    </div>
                `;
                
                // 添加点击事件查看大图
                photoCard.addEventListener('click', function() {
                    openPhotoViewer(displayPhotos, displayPhotos.indexOf(photo));
                });
                
                // 优化添加顺序，支持懒加载
                setTimeout(() => {
                    photosGrid.appendChild(photoCard);
                }, displayPhotos.indexOf(photo) * 100); // 轻微延迟创建动画效果
            });
        })
        .catch(error => {
            console.error('加载照片失败:', error);
            const photosGrid = document.getElementById('featured-photos-grid');
            photosGrid.innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>加载照片失败</p>
                    <button class="btn btn-secondary" onclick="loadHomePageData()">
                        重试
                    </button>
                </div>
            `;
        });
}

// 更新倒计时
function updateCountdown(type, dateStr) {
    const targetDate = new Date(dateStr);
    const now = new Date();
    const diffTime = Math.abs(now - targetDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    document.getElementById(`${type}-days`).textContent = diffDays;
    document.getElementById(`${type}-date`).textContent = dateStr;
}

// 加载事件列表
function loadEvents() {
    const searchTerm = document.getElementById('event-search').value;
    const filterType = document.getElementById('event-filter').value;
    
    let url = '/api/events';
    
    // 根据筛选条件构建URL
    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (filterType !== 'all') params.append('filter', filterType);
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    fetch(url)
        .then(response => response.json())
        .then(events => {
            const eventsContainer = document.getElementById('events-container');
            eventsContainer.innerHTML = '';
            
            if (events.length === 0) {
                eventsContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-calendar-alt"></i>
                        <p>没有找到匹配的事件</p>
                        <button class="btn-primary" onclick="document.getElementById('add-event-btn').click()">
                            添加新事件
                        </button>
                    </div>
                `;
                return;
            }
            
            // 按日期排序（最新的在前）
            events.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            events.forEach(event => {
                const eventDate = new Date(event.date);
                const eventItem = document.createElement('div');
                eventItem.className = 'event-item';
                eventItem.dataset.id = event.id;
                eventItem.innerHTML = `
                    <div class="event-date">
                        <div class="event-date-day">${eventDate.getDate()}</div>
                        <div class="event-date-month">${eventDate.getFullYear()}.${eventDate.getMonth() + 1}</div>
                    </div>
                    <div class="event-details">
                        <div class="event-header">
                            <h3 class="event-title">${event.title}</h3>
                            <div class="event-actions">
                                <button class="event-action-btn edit-btn" title="编辑">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="event-action-btn delete-btn" title="删除">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                        <p class="event-description">${event.description || '暂无描述'}</p>
                    </div>
                `;
                
                // 添加编辑事件
                eventItem.querySelector('.edit-btn').addEventListener('click', function() {
                    editEvent(event);
                });
                
                // 添加删除事件
                eventItem.querySelector('.delete-btn').addEventListener('click', function() {
                    deleteEvent(event.id);
                });
                
                eventsContainer.appendChild(eventItem);
            });
        })
        .catch(error => showNotification('加载事件失败', 'error'));
}

// 保存事件
function saveEvent() {
    const id = document.getElementById('event-id').value;
    const title = document.getElementById('event-title').value.trim();
    const date = document.getElementById('event-date').value;
    const description = document.getElementById('event-description').value.trim();
    
    // 验证表单
    if (!title) {
        showNotification('请输入事件标题', 'warning');
        return;
    }
    
    if (!date) {
        showNotification('请选择事件日期', 'warning');
        return;
    }
    
    // 准备数据
    const eventData = { title, date, description };
    
    // 确定请求方法和URL
    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/events/${id}` : '/api/events';
    
    // 发送请求
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(eventData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('保存失败');
        }
        return response.json();
    })
    .then(() => {
        // 关闭模态框
        document.getElementById('event-modal').classList.remove('active');
        
        // 显示成功消息
        showNotification(id ? '事件更新成功' : '事件创建成功', 'success');
        
        // 重新加载事件列表
        if (currentPage === 'events') {
            loadEvents();
        } else if (currentPage === 'home') {
            loadHomePageData();
        }
    })
    .catch(error => showNotification('保存失败', 'error'));
}

// 编辑事件
function editEvent(event) {
    document.getElementById('event-id').value = event.id;
    document.getElementById('event-title').value = event.title;
    document.getElementById('event-date').value = event.date;
    document.getElementById('event-description').value = event.description || '';
    document.getElementById('event-modal-title').textContent = '编辑事件';
    
    document.getElementById('event-modal').classList.add('active');
}

// 删除事件
function deleteEvent(eventId) {
    if (confirm('确定要删除这个事件吗？相关的照片也会被删除。')) {
        fetch(`/api/events/${eventId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('删除失败');
            }
            return response.json();
        })
        .then(() => {
            showNotification('事件删除成功', 'success');
            
            // 重新加载事件列表
            if (currentPage === 'events') {
                loadEvents();
            } else if (currentPage === 'home') {
                loadHomePageData();
            }
        })
        .catch(error => showNotification('删除失败', 'error'));
    }
}

// 加载照片
function loadPhotos(albumId = 'all', searchQuery = '') {
    let url = '/api/photos';
    const params = new URLSearchParams();
    
    if (albumId !== 'all') {
        params.append('album_id', albumId);
    }
    
    if (searchQuery) {
        params.append('search', searchQuery);
    }
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    showLoader();
    fetch(url)
        .then(response => response.json())
        .then(photos => {
            hideLoader();
            currentPhotos = photos;
            
            const photosContainer = document.getElementById('photos-container');
            photosContainer.innerHTML = '';
            
            if (photos.length === 0) {
                photosContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-image"></i>
                        <p>没有找到照片</p>
                        <button class="btn-primary" onclick="document.getElementById('upload-photo-btn').click()">
                            上传照片
                        </button>
                    </div>
                `;
                return;
            }
            
            photos.forEach(photo => {
                const photoCard = document.createElement('div');
                photoCard.className = 'photo-card';
                
                // 使用缩略图URL
                const thumbnailUrl = photo.thumbnail_url || `/api/uploads/thumbnails/${photo.filename}`;
                
                photoCard.innerHTML = `
                    <img src="${thumbnailUrl}" alt="${photo.original_name}">
                    <div class="photo-overlay">
                        <div class="photo-name">${photo.original_name}</div>
                    </div>
                `;
                
                // 添加点击事件查看大图
                photoCard.addEventListener('click', function() {
                    openPhotoViewer(photos, photos.indexOf(photo));
                });
                
                photosContainer.appendChild(photoCard);
            });
        })
        .catch(error => {
            hideLoader();
            showNotification('加载照片失败', 'error');
        });
}

// 打开照片查看器
function openPhotoViewer(photos, index) {
    currentPhotos = photos;
    currentPhotoIndex = index;
    
    const photo = photos[index];
    document.getElementById('current-photo-name').textContent = photo.original_name;
    
    // 使用照片完整URL
    const photoUrl = photo.url || `/api/uploads/${photo.filename}`;
    document.getElementById('large-photo').src = photoUrl;
    document.getElementById('photo-viewer-description').textContent = photo.description || '暂无描述';
    
    // 更新相关信息显示
    let relatedInfo = document.getElementById('photo-related-info');
    if (!relatedInfo) {
        // 如果不存在，创建相关信息元素
        relatedInfo = document.createElement('div');
        relatedInfo.id = 'photo-related-info';
        relatedInfo.className = 'photo-related-info';
        const descriptionElement = document.getElementById('photo-viewer-description');
        descriptionElement.parentNode.insertBefore(relatedInfo, descriptionElement.nextSibling);
    }
    
    relatedInfo.innerHTML = '';
    if (photo.album_info) {
        relatedInfo.innerHTML += `<p>相册: ${photo.album_info.name}</p>`;
    }
    if (photo.event_info) {
        relatedInfo.innerHTML += `<p>事件: ${photo.event_info.title}</p>`;
    }
    
    document.getElementById('photo-viewer').classList.add('active');
}

// 显示上一张照片
function showPreviousPhoto() {
    if (currentPhotos.length > 0) {
        currentPhotoIndex = (currentPhotoIndex - 1 + currentPhotos.length) % currentPhotos.length;
        const photo = currentPhotos[currentPhotoIndex];
        
        document.getElementById('current-photo-name').textContent = photo.original_name;
        document.getElementById('large-photo').src = `/api/uploads/${photo.filename}`;
        document.getElementById('photo-viewer-description').textContent = photo.description || '暂无描述';
    }
}

// 显示下一张照片
function showNextPhoto() {
    if (currentPhotos.length > 0) {
        currentPhotoIndex = (currentPhotoIndex + 1) % currentPhotos.length;
        const photo = currentPhotos[currentPhotoIndex];
        
        document.getElementById('current-photo-name').textContent = photo.original_name;
        document.getElementById('large-photo').src = `/api/uploads/${photo.filename}`;
        document.getElementById('photo-viewer-description').textContent = photo.description || '暂无描述';
    }
}

// 删除当前照片
function deleteCurrentPhoto() {
    if (currentPhotos.length > 0) {
        const photo = currentPhotos[currentPhotoIndex];
        
        if (confirm('确定要删除这张照片吗？')) {
            fetch(`/api/photos/${photo.id}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('删除失败');
                }
                return response.json();
            })
            .then(() => {
                // 关闭照片查看器
                document.getElementById('photo-viewer').classList.remove('active');
                
                // 显示成功消息
                showNotification('照片删除成功', 'success');
                
                // 重新加载照片
                const activeAlbum = document.querySelector('.album-btn.active').getAttribute('data-album');
                loadPhotos(activeAlbum);
            })
            .catch(error => showNotification('删除失败', 'error'));
        }
    }
}

// 上传照片
function uploadPhoto() {
    const fileInput = document.getElementById('photo-file');
    const description = document.getElementById('photo-description').value.trim();
    const dateTaken = document.getElementById('photo-date').value;
    const albumId = document.getElementById('photo-album').value;
    const eventId = document.getElementById('photo-event').value;
    const tags = document.getElementById('photo-tags').value.trim();
    
    // 验证文件
    if (!fileInput.files || fileInput.files.length === 0) {
        showNotification('请选择要上传的照片', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    
    // 检查文件类型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        showNotification('不支持的文件类型，请上传图片文件', 'warning');
        return;
    }
    
    // 检查文件大小（16MB）
    if (file.size > 16 * 1024 * 1024) {
        showNotification('文件太大，请上传小于16MB的照片', 'warning');
        return;
    }
    
    // 准备FormData
    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', description);
    if (dateTaken) formData.append('date_taken', dateTaken);
    if (albumId) formData.append('album_id', albumId);
    if (eventId) formData.append('event_id', eventId);
    if (tags) formData.append('tags', tags);
    
    showLoader();
    
    // 发送请求
    fetch('/api/photos', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || '上传失败');
            });
        }
        return response.json();
    })
    .then(() => {
        hideLoader();
        // 关闭模态框
        document.getElementById('photo-modal').classList.remove('active');
        
        // 显示成功消息
        showNotification('照片上传成功', 'success');
        
        // 重新加载照片
        const activeAlbum = document.querySelector('.album-btn.active')?.getAttribute('data-album') || 'all';
        loadPhotos(activeAlbum);
    })
    .catch(error => {
        hideLoader();
        showNotification(`上传失败: ${error.message}`, 'error');
    });
}

// 批量上传照片
function setupBatchUpload() {
    // 检查页面是否有批量上传模态框
    const batchUploadBtn = document.getElementById('batch-upload-btn');
    if (batchUploadBtn) {
        batchUploadBtn.addEventListener('click', function() {
            // 加载相册和事件选项
            loadAlbumsForDropdown('batch-photo-album');
            loadEventsForDropdown('batch-photo-event');
            
            // 显示批量上传模态框
            document.getElementById('batch-upload-modal').classList.add('active');
        });
    }
    
    const batchUploadForm = document.getElementById('batch-upload-form');
    if (batchUploadForm) {
        batchUploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const files = document.getElementById('batch-photo-files').files;
            const albumId = document.getElementById('batch-photo-album').value;
            const eventId = document.getElementById('batch-photo-event').value;
            
            if (files.length === 0) {
                showNotification('请选择要上传的照片', 'error');
                return;
            }
            
            // 添加所有文件到FormData
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            // 添加其他表单数据
            if (albumId) formData.append('album_id', albumId);
            if (eventId) formData.append('event_id', eventId);
            
            showLoader();
            
            fetch('/api/photos/batch', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                hideLoader();
                
                if (data.success_count > 0) {
                    showNotification(`成功上传 ${data.success_count} 张照片`, 'success');
                    // 重新加载照片列表
                    const activeAlbum = document.querySelector('.album-btn.active')?.getAttribute('data-album') || 'all';
                    loadPhotos(activeAlbum);
                    // 重置表单
                    batchUploadForm.reset();
                    // 关闭模态框
                    document.getElementById('batch-upload-modal').classList.remove('active');
                }
                
                if (data.error_count > 0) {
                    let errorMessage = `有 ${data.error_count} 张照片上传失败`;
                    if (data.errors) {
                        errorMessage += ':\n' + data.errors.map(e => `${e.filename}: ${e.error}`).join('\n');
                    }
                    showNotification(errorMessage, 'error');
                }
            })
            .catch(error => {
                hideLoader();
                showNotification('批量上传失败', 'error');
            });
        });
    }
}

// 高级搜索照片
function setupPhotoSearch() {
    // 检查页面是否有搜索按钮和相关元素
    const searchBtn = document.getElementById('photo-search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            // 显示搜索模态框
            document.getElementById('photo-search-modal').classList.add('active');
            
            // 加载相册和事件选项
            loadAlbumsForDropdown('search-photo-album');
            loadEventsForDropdown('search-photo-event');
            loadTagsForSearch();
        });
    }
    
    const searchForm = document.getElementById('photo-search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = document.getElementById('search-photo-query').value.trim();
            const dateFrom = document.getElementById('search-photo-date-from').value;
            const dateTo = document.getElementById('search-photo-date-to').value;
            const albumId = document.getElementById('search-photo-album').value;
            const eventId = document.getElementById('search-photo-event').value;
            
            // 构建搜索URL
            let url = '/api/photos/search?';
            const params = new URLSearchParams();
            
            if (query) params.append('q', query);
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            if (albumId) params.append('album_id', albumId);
            if (eventId) params.append('event_id', eventId);
            
            // 获取选中的标签
            const selectedTags = Array.from(document.querySelectorAll('#search-photo-tags input:checked'))
                .map(tag => tag.value);
            selectedTags.forEach(tag => params.append('tag', tag));
            
            url += params.toString();
            
            showLoader();
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    hideLoader();
                    // 关闭搜索模态框
                    document.getElementById('photo-search-modal').classList.remove('active');
                    
                    currentPhotos = data;
                    
                    const photosContainer = document.getElementById('photos-container');
                    photosContainer.innerHTML = '';
                    
                    if (data.length === 0) {
                        photosContainer.innerHTML = `
                            <div class="empty-state">
                                <i class="fas fa-search"></i>
                                <p>没有找到符合条件的照片</p>
                            </div>
                        `;
                        return;
                    }
                    
                    data.forEach(photo => {
                        const photoCard = document.createElement('div');
                        photoCard.className = 'photo-card';
                        
                        // 使用缩略图URL
                        const thumbnailUrl = photo.thumbnail_url || `/api/uploads/thumbnails/${photo.filename}`;
                        
                        photoCard.innerHTML = `
                            <img src="${thumbnailUrl}" alt="${photo.original_name}">
                            <div class="photo-overlay">
                                <div class="photo-name">${photo.original_name}</div>
                            </div>
                        `;
                        
                        // 添加点击事件查看大图
                        photoCard.addEventListener('click', function() {
                            openPhotoViewer(data, data.indexOf(photo));
                        });
                        
                        photosContainer.appendChild(photoCard);
                    });
                })
                .catch(error => {
                    hideLoader();
                    showNotification('搜索失败', 'error');
                });
        });
    }
}

// 加载标签用于搜索
function loadTagsForSearch() {
    const tagsContainer = document.getElementById('search-photo-tags');
    if (!tagsContainer) return;
    
    tagsContainer.innerHTML = '<label>标签 (多选):</label><div class="tags-container"></div>';
    const tagsList = tagsContainer.querySelector('.tags-container');
    
    fetch('/api/tags')
        .then(response => response.json())
        .then(tags => {
            tags.forEach(tag => {
                const tagElement = document.createElement('div');
                tagElement.className = 'tag-item';
                tagElement.innerHTML = `
                    <input type="checkbox" id="search-tag-${tag.id}" name="tag" value="${tag.id}">
                    <label for="search-tag-${tag.id}">${tag.name}</label>
                `;
                tagsList.appendChild(tagElement);
            });
        })
        .catch(error => console.error('加载标签失败:', error));
}

// 加载相册
function loadAlbums() {
    fetch('/api/albums')
        .then(response => response.json())
        .then(albums => {
            const albumsList = document.getElementById('albums-list');
            albumsList.innerHTML = '';
            
            albums.forEach(album => {
                const albumBtn = document.createElement('button');
                albumBtn.className = 'album-btn';
                albumBtn.textContent = `${album.name} (${album.photo_count})`;
                albumBtn.setAttribute('data-album', album.id);
                
                albumBtn.addEventListener('click', function() {
                    // 移除所有活动状态
                    document.querySelectorAll('.album-btn').forEach(btn => {
                        btn.classList.remove('active');
                    });
                    
                    // 添加当前活动状态
                    this.classList.add('active');
                    
                    // 加载对应相册的照片
                    loadPhotos(album.id);
                });
                
                albumsList.appendChild(albumBtn);
            });
        })
        .catch(error => console.error('加载相册失败:', error));
}

// 为下拉框加载相册
function loadAlbumsForDropdown(selectId = 'photo-album') {
    const albumSelect = document.getElementById(selectId);
    if (!albumSelect) return;
    
    // 清空现有选项（保留第一个）
    const firstOption = albumSelect.firstElementChild;
    albumSelect.innerHTML = '';
    albumSelect.appendChild(firstOption);
    
    fetch('/api/albums')
        .then(response => response.json())
        .then(albums => {
            albums.forEach(album => {
                const option = document.createElement('option');
                option.value = album.id;
                option.textContent = album.name;
                albumSelect.appendChild(option);
            });
        })
        .catch(error => console.error('加载相册失败:', error));
}

// 为下拉框加载事件
function loadEventsForDropdown(selectId = 'photo-event') {
    const eventSelect = document.getElementById(selectId);
    if (!eventSelect) return;
    
    // 清空现有选项（保留第一个）
    const firstOption = eventSelect.firstElementChild;
    eventSelect.innerHTML = '';
    eventSelect.appendChild(firstOption);
    
    fetch('/api/events')
        .then(response => response.json())
        .then(events => {
            events.forEach(event => {
                const option = document.createElement('option');
                option.value = event.id;
                option.textContent = `${event.title} (${event.date})`;
                eventSelect.appendChild(option);
            });
        })
        .catch(error => console.error('加载事件失败:', error));
}

// 创建相册
function createAlbum() {
    const name = document.getElementById('album-name').value.trim();
    const description = document.getElementById('album-description').value.trim();
    
    if (!name) {
        showNotification('请输入相册名称', 'warning');
        return;
    }
    
    fetch('/api/albums', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, description })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('创建失败');
        }
        return response.json();
    })
    .then(() => {
        // 关闭模态框
        document.getElementById('album-modal').classList.remove('active');
        
        // 显示成功消息
        showNotification('相册创建成功', 'success');
        
        // 重新加载相册列表
        loadAlbums();
        loadAlbumsForDropdown();
    })
    .catch(error => showNotification('创建失败', 'error'));
}

// 加载配置
function loadConfig() {
    fetch('/api/configs')
        .then(response => response.json())
        .then(configs => {
            // 创建配置映射
            const configMap = {};
            configs.forEach(config => {
                configMap[config.key] = config.value;
            });
            
            // 填充基本表单
            document.getElementById('relationship_date').value = configMap.relationship_date || '';
            document.getElementById('first_meeting_date').value = configMap.first_meeting_date || '';
            document.getElementById('motto_input').value = configMap.motto || '';
            document.getElementById('values_input').value = configMap.values || '';
            document.getElementById('rules_input').value = configMap.rules || '';
            
            // 加载轮播图数据
            carouselItems = [];
            try {
                // 尝试从JSON格式的carousel_items配置中加载多张轮播图
                if (configMap.carousel_items && configMap.carousel_items.trim()) {
                    carouselItems = JSON.parse(configMap.carousel_items);
                } else if (configMap.carousel_image_url) {
                    // 如果没有carousel_items但有单个轮播图配置，转换为新格式
                    carouselItems.push({
                        id: Date.now().toString(),
                        image_url: configMap.carousel_image_url,
                        title: configMap.carousel_title || '我们的故事',
                        subtitle: configMap.carousel_subtitle || '珍藏每一个美好的瞬间'
                    });
                }
            } catch (e) {
                console.error('解析轮播图数据失败:', e);
            }
            
            // 渲染轮播图管理界面
            renderCarouselItemsList();
        })
        .catch(error => showNotification('加载配置失败', 'error'));
}

// 保存配置
function saveSettings() {
    const relationshipDate = document.getElementById('relationship_date').value;
    const firstMeetingDate = document.getElementById('first_meeting_date').value;
    const motto = document.getElementById('motto_input').value.trim();
    const values = document.getElementById('values_input').value.trim();
    const rules = document.getElementById('rules_input').value.trim();
    
    // 将轮播图数据转换为JSON字符串
    const carouselItemsJson = JSON.stringify(carouselItems);
    
    // 配置项列表
    const configsToUpdate = [
        { key: 'relationship_date', value: relationshipDate },
        { key: 'first_meeting_date', value: firstMeetingDate },
        { key: 'motto', value: motto },
        { key: 'values', value: values },
        { key: 'rules', value: rules },
        { key: 'carousel_items', value: carouselItemsJson }
    ];
    
    // 保存所有配置项
    const savePromises = configsToUpdate.map(config => 
        fetch(`/api/configs/${config.key}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ value: config.value })
        })
    );
    
    Promise.all(savePromises)
        .then(responses => {
            const allOk = responses.every(response => response.ok);
            if (!allOk) {
                throw new Error('保存失败');
            }
            return Promise.all(responses.map(r => r.json()));
        })
        .then(() => {
            showNotification('设置保存成功', 'success');
            
            // 如果当前是首页，刷新数据
            if (currentPage === 'home') {
                loadHomePageData();
            }
        })
        .catch(error => showNotification('保存失败', 'error'));
}

// 渲染轮播图
function renderCarousel() {
    const slidesContainer = document.querySelector('.carousel-slides');
    const indicatorsContainer = document.querySelector('.carousel-indicators');
    
    // 清空容器
    slidesContainer.innerHTML = '';
    indicatorsContainer.innerHTML = '';
    
    // 如果没有轮播图，添加默认轮播图
    if (carouselItems.length === 0) {
        carouselItems.push({
            id: Date.now().toString(),
            image_url: 'https://picsum.photos/1200/600?random=1',
            title: '我们的故事',
            subtitle: '珍藏每一个美好的瞬间'
        });
    }
    
    // 创建轮播图幻灯片
    carouselItems.forEach((item, index) => {
        const slide = document.createElement('div');
        slide.className = `carousel-slide ${index === 0 ? 'active' : ''}`;
        slide.dataset.index = index;
        
        // 创建图片
        const img = document.createElement('img');
        img.className = 'carousel-image';
        
        // 处理图片URL
        let imageUrl = item.image_url || 'https://picsum.photos/1200/600?random=1';
        if (imageUrl.match(/^[a-zA-Z]:\\/) || imageUrl.includes('\\')) {
            // 本地文件路径，使用随机图片
            img.src = 'https://picsum.photos/1200/600?random=' + (index + 1);
        } else {
            img.src = imageUrl;
        }
        img.alt = item.title || '轮播图片';
        
        // 创建覆盖层
        const overlay = document.createElement('div');
        overlay.className = 'carousel-overlay';
        
        // 添加标题和副标题
        const title = document.createElement('h2');
        title.textContent = item.title || '我们的故事';
        
        const subtitle = document.createElement('p');
        subtitle.textContent = item.subtitle || '珍藏每一个美好的瞬间';
        
        // 组装
        overlay.appendChild(title);
        overlay.appendChild(subtitle);
        slide.appendChild(img);
        slide.appendChild(overlay);
        slidesContainer.appendChild(slide);
        
        // 创建指示器
        const indicator = document.createElement('button');
        indicator.className = `carousel-indicator ${index === 0 ? 'active' : ''}`;
        indicator.dataset.index = index;
        indicator.addEventListener('click', () => {
            goToSlide(index);
        });
        indicatorsContainer.appendChild(indicator);
    });
    
    // 重置当前索引
    currentSlideIndex = 0;
    
    // 启动轮播
    startCarousel();
}

// 初始化轮播图控制
function initCarouselControls() {
    // 初始化指示器点击事件
    const indicators = document.querySelectorAll('.carousel-indicator');
    indicators.forEach((indicator, index) => {
        indicator.removeEventListener('click', function() { goToSlide(index); });
        indicator.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            goToSlide(index);
        });
    });
}

// 显示前一张
function showPreviousSlide() {
    currentSlideIndex = (currentSlideIndex - 1 + carouselItems.length) % carouselItems.length;
    updateCarousel();
}

// 显示后一张
function showNextSlide() {
    currentSlideIndex = (currentSlideIndex + 1) % carouselItems.length;
    updateCarousel();
}

// 跳转到指定幻灯片
function goToSlide(index) {
    currentSlideIndex = index;
    updateCarousel();
}

// 更新轮播图显示
function updateCarousel() {
    const slides = document.querySelectorAll('.carousel-slide');
    const indicators = document.querySelectorAll('.carousel-indicator');
    
    slides.forEach((slide, index) => {
        if (index === currentSlideIndex) {
            slide.classList.add('active');
        } else {
            slide.classList.remove('active');
        }
    });
    
    indicators.forEach((indicator, index) => {
        if (index === currentSlideIndex) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    });
}

// 启动轮播
function startCarousel() {
    // 清除现有定时器
    if (carouselInterval) {
        clearInterval(carouselInterval);
    }
    
    // 设置自动轮播，每5秒切换一次
    carouselInterval = setInterval(showNextSlide, 5000);
}

// 停止轮播
function stopCarousel() {
    if (carouselInterval) {
        clearInterval(carouselInterval);
        carouselInterval = null;
    }
}

// 渲染轮播图管理列表
function renderCarouselItemsList() {
    const container = document.getElementById('carousel-items-list');
    container.innerHTML = '';
    
    if (carouselItems.length === 0) {
        container.innerHTML = '<p>暂无轮播图，请点击下方按钮添加</p>';
    } else {
        carouselItems.forEach((item, index) => {
            const itemElement = document.createElement('div');
            itemElement.className = 'carousel-item';
            
            // 创建预览图
            const previewContainer = document.createElement('div');
            previewContainer.className = 'carousel-item-preview';
            
            const previewImg = document.createElement('img');
            let imageUrl = item.image_url || 'https://picsum.photos/100/60?random=1';
            if (imageUrl.match(/^[a-zA-Z]:\\/) || imageUrl.includes('\\')) {
                previewImg.src = 'https://picsum.photos/100/60?random=' + (index + 1);
            } else {
                previewImg.src = imageUrl;
            }
            previewImg.alt = item.title || '预览';
            previewImg.className = 'carousel-preview-image';
            
            previewContainer.appendChild(previewImg);
            
            // 创建内容区域
            const contentContainer = document.createElement('div');
            contentContainer.className = 'carousel-item-content';
            
            const title = document.createElement('div');
            title.className = 'carousel-item-title';
            title.textContent = item.title || '未命名轮播图';
            
            const subtitle = document.createElement('div');
            subtitle.className = 'carousel-item-subtitle';
            subtitle.textContent = item.subtitle || '无副标题';
            
            contentContainer.appendChild(title);
            contentContainer.appendChild(subtitle);
            
            // 创建操作按钮
            const actionsContainer = document.createElement('div');
            actionsContainer.className = 'carousel-item-actions';
            
            const editButton = document.createElement('button');
            editButton.className = 'btn-secondary btn-small';
            editButton.innerHTML = '<i class="fas fa-edit"></i>';
            editButton.title = '编辑';
            editButton.addEventListener('click', (e) => {
                e.stopPropagation();
                editCarouselItem(index);
            });
            
            const deleteButton = document.createElement('button');
            deleteButton.className = 'btn-danger btn-small';
            deleteButton.innerHTML = '<i class="fas fa-trash"></i>';
            deleteButton.title = '删除';
            deleteButton.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteCarouselItem(index);
            });
            
            actionsContainer.appendChild(editButton);
            actionsContainer.appendChild(deleteButton);
            
            // 组装
            itemElement.appendChild(previewContainer);
            itemElement.appendChild(contentContainer);
            itemElement.appendChild(actionsContainer);
            
            // 点击整个项目编辑
            itemElement.addEventListener('click', () => {
                editCarouselItem(index);
            });
            
            container.appendChild(itemElement);
        });
    }
    
    // 单独调用绑定添加轮播图按钮事件的函数
    bindAddCarouselButtonEvent();
}

// 绑定添加轮播图按钮事件
function bindAddCarouselButtonEvent() {
    const addButton = document.getElementById('add-carousel-item');
    if (addButton) {
        // 移除所有事件监听器
        const newButton = addButton.cloneNode(true);
        addButton.parentNode.replaceChild(newButton, addButton);
        
        // 添加新的事件监听器
        newButton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            addCarouselItem();
        });
    }
}

// 添加新轮播图
function addCarouselItem() {
    const newItem = {
        id: Date.now().toString(),
        image_url: '',
        title: '新轮播图',
        subtitle: '请编辑此轮播图的标题和副标题'
    };
    
    carouselItems.push(newItem);
    renderCarouselItemsList();
    
    // 自动进入编辑模式
    editCarouselItem(carouselItems.length - 1);
}

// 编辑轮播图
function editCarouselItem(index) {
    const item = carouselItems[index];
    
    // 创建编辑模态框
    const modal = document.createElement('div');
    modal.className = 'modal active';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    
    const modalHeader = document.createElement('div');
    modalHeader.className = 'modal-header';
    
    const modalTitle = document.createElement('h3');
    modalTitle.textContent = '编辑轮播图';
    
    const closeButton = document.createElement('button');
    closeButton.className = 'modal-close';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', () => {
        // 如果是新添加的轮播图且没有修改过，从数组中移除
        if (item.image_url === '' && item.title === '新轮播图' && item.subtitle === '请编辑此轮播图的标题和副标题') {
            carouselItems.splice(index, 1);
            renderCarouselItemsList();
        }
        document.body.removeChild(modal);
    });
    
    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);
    
    const modalBody = document.createElement('div');
    modalBody.className = 'modal-body';
    
    // 图片URL输入
    const imageUrlGroup = document.createElement('div');
    imageUrlGroup.className = 'form-group';
    
    const imageUrlLabel = document.createElement('label');
    imageUrlLabel.textContent = '图片URL';
    
    const imageUrlInput = document.createElement('input');
    imageUrlInput.type = 'text';
    imageUrlInput.className = 'form-control';
    imageUrlInput.value = item.image_url || '';
    imageUrlInput.placeholder = '输入图片URL';
    
    imageUrlGroup.appendChild(imageUrlLabel);
    imageUrlGroup.appendChild(imageUrlInput);
    
    // 标题输入
    const titleGroup = document.createElement('div');
    titleGroup.className = 'form-group';
    
    const titleLabel = document.createElement('label');
    titleLabel.textContent = '标题';
    
    const titleInput = document.createElement('input');
    titleInput.type = 'text';
    titleInput.className = 'form-control';
    titleInput.value = item.title || '';
    titleInput.placeholder = '输入轮播图标题';
    
    titleGroup.appendChild(titleLabel);
    titleGroup.appendChild(titleInput);
    
    // 副标题输入
    const subtitleGroup = document.createElement('div');
    subtitleGroup.className = 'form-group';
    
    const subtitleLabel = document.createElement('label');
    subtitleLabel.textContent = '副标题';
    
    const subtitleInput = document.createElement('input');
    subtitleInput.type = 'text';
    subtitleInput.className = 'form-control';
    subtitleInput.value = item.subtitle || '';
    subtitleInput.placeholder = '输入轮播图副标题';
    
    subtitleGroup.appendChild(subtitleLabel);
    subtitleGroup.appendChild(subtitleInput);
    
    modalBody.appendChild(imageUrlGroup);
    modalBody.appendChild(titleGroup);
    modalBody.appendChild(subtitleGroup);
    
    const modalFooter = document.createElement('div');
    modalFooter.className = 'modal-footer';
    
    const cancelButton = document.createElement('button');
    cancelButton.className = 'btn-secondary';
    cancelButton.textContent = '取消';
    cancelButton.addEventListener('click', () => {
        // 如果是新添加的轮播图且没有修改过，从数组中移除
        if (item.image_url === '' && item.title === '新轮播图' && item.subtitle === '请编辑此轮播图的标题和副标题') {
            carouselItems.splice(index, 1);
            renderCarouselItemsList();
        }
        document.body.removeChild(modal);
    });
    
    const saveButton = document.createElement('button');
    saveButton.className = 'btn-primary';
    saveButton.textContent = '保存';
    saveButton.addEventListener('click', () => {
        // 更新轮播图数据
        carouselItems[index] = {
            ...item,
            image_url: imageUrlInput.value.trim(),
            title: titleInput.value.trim(),
            subtitle: subtitleInput.value.trim()
        };
        
        // 重新渲染列表
        renderCarouselItemsList();
        
        // 关闭模态框
        document.body.removeChild(modal);
    });
    
    modalFooter.appendChild(cancelButton);
    modalFooter.appendChild(saveButton);
    
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    
    modal.appendChild(modalContent);
    
    // 添加到页面
    document.body.appendChild(modal);
}

// 删除轮播图
function deleteCarouselItem(index) {
    if (carouselItems.length <= 1) {
        showNotification('至少需要保留一张轮播图', 'warning');
        return;
    }
    
    if (confirm('确定要删除这张轮播图吗？')) {
        carouselItems.splice(index, 1);
        renderCarouselItemsList();
        showNotification('轮播图删除成功', 'success');
    }
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 加载备份列表
function loadBackupList() {
    fetch('/api/backups')
        .then(response => {
            if (!response.ok) {
                throw new Error('加载备份列表失败');
            }
            return response.json();
        })
        .then(data => {
            const backupListContainer = document.getElementById('backup-list-container');
            
            if (data.backups.length === 0) {
                backupListContainer.innerHTML = '<p>暂无备份文件</p>';
                return;
            }
            
            let html = '<table style="width: 100%; border-collapse: collapse;">';
            html += '<tr style="border-bottom: 1px solid #ddd;">' +
                    '<th style="text-align: left; padding: 8px;">文件名</th>' +
                    '<th style="text-align: left; padding: 8px;">大小</th>' +
                    '<th style="text-align: left; padding: 8px;">创建时间</th>' +
                    '<th style="text-align: right; padding: 8px;">操作</th>' +
                    '</tr>';
            
            data.backups.forEach(backup => {
                const date = new Date(backup.created_at);
                const formattedDate = date.toLocaleString('zh-CN');
                
                html += '<tr style="border-bottom: 1px solid #eee;">' +
                        `<td style="padding: 8px;">${backup.filename}</td>` +
                        `<td style="padding: 8px;">${formatFileSize(backup.size)}</td>` +
                        `<td style="padding: 8px;">${formattedDate}</td>` +
                        `<td style="text-align: right; padding: 8px;">` +
                        `<button class="btn-secondary btn-sm" onclick="restoreFromBackup('${backup.filename}')">恢复</button>` +
                        `<button class="btn-danger btn-sm" style="margin-left: 5px;" onclick="deleteBackup('${backup.filename}')">删除</button>` +
                        `</td>` +
                        '</tr>';
            });
            
            html += '</table>';
            backupListContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('加载备份列表失败:', error);
            document.getElementById('backup-list-container').innerHTML = '<p style="color: red;">加载备份列表失败</p>';
        });
}

// 备份数据
function backupData() {
    fetch('/api/backup', { 
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('备份失败');
        }
        return response.json();
    })
    .then(data => {
        showNotification(`数据备份成功，文件：${data.backup_file.filename}`, 'success');
        // 重新加载备份列表
        if (currentPage === 'config') {
            loadBackupList();
        }
    })
    .catch(error => showNotification('备份失败', 'error'));
}

// 从备份列表恢复数据
function restoreFromBackup(filename) {
    if (confirm(`确定要从备份文件 ${filename} 恢复数据吗？当前数据将被覆盖。`)) {
        fetch(`/api/restore/${filename}`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || '恢复失败'); });
            }
            return response.json();
        })
        .then(() => {
            showNotification('数据恢复成功', 'success');
            
            // 重新加载所有关键数据，确保轮播图数据被正确加载
            loadHomePageData(); // 加载轮播图数据和首页内容
            
            // 根据当前页面加载相应数据
            switch(currentPage) {
                case 'home':
                    // 已加载首页数据
                    break;
                case 'events':
                    loadEvents();
                    break;
                case 'photos':
                    loadPhotos();
                    loadAlbums();
                    break;
                case 'config':
                    loadConfig(); // 重新加载配置，包括轮播图设置
                    loadBackupList();
                    break;
            }
        })
        .catch(error => showNotification(`恢复失败: ${error.message}`, 'error'));
    }
}

// 恢复数据（从本地上传）
function restoreData(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 检查文件扩展名
    if (!file.name.endsWith('.db')) {
        showNotification('请选择正确的数据库备份文件（.db格式）', 'warning');
        return;
    }
    
    // 这里可以实现文件上传功能，目前简化为直接使用文件名
    // 注意：在实际应用中，应该先上传文件到服务器，然后再恢复
    restoreFromBackup(file.name);
    
    // 重置文件输入
    event.target.value = '';
}

// 删除备份
function deleteBackup(filename) {
    if (confirm(`确定要删除备份文件 ${filename} 吗？此操作无法撤销。`)) {
        fetch(`/api/backup/${filename}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || '删除失败'); });
            }
            return response.json();
        })
        .then(() => {
            showNotification('备份文件已成功删除', 'success');
            // 重新加载备份列表
            loadBackupList();
        })
        .catch(error => showNotification(`删除失败: ${error.message}`, 'error'));
    }
}

// 清理旧备份功能已移除，系统自动最多保存100个备份


// 显示通知
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const notificationMessage = document.getElementById('notification-message');
    
    // 设置消息和类型
    notificationMessage.textContent = message;
    
    // 移除所有类型类
    notification.classList.remove('success', 'error', 'warning');
    
    // 添加类型类
    notification.classList.add(type);
    
    // 显示通知
    notification.classList.add('show');
    
    // 3秒后隐藏
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// 显示加载动画
function showLoader() {
    // 创建加载动画元素（如果不存在）
    let loader = document.getElementById('page-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'page-loader';
        loader.className = 'page-loader';
        loader.innerHTML = `
            <div class="loader-spinner"></div>
            <div class="loader-text">处理中...</div>
        `;
        document.body.appendChild(loader);
    }
    
    loader.style.display = 'flex';
}

// 隐藏加载动画
function hideLoader() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// 防抖函数
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// 添加键盘导航
window.addEventListener('keydown', function(e) {
    // ESC 键关闭模态框
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
    
    // 左右箭头在照片查看器中导航
    const photoViewer = document.getElementById('photo-viewer');
    if (photoViewer.classList.contains('active')) {
        if (e.key === 'ArrowLeft') {
            showPreviousPhoto();
        } else if (e.key === 'ArrowRight') {
            showNextPhoto();
        }
    }
});

// 初始化相册选择器事件
function initAlbumSelectors() {
    document.querySelectorAll('.album-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有活动状态
            document.querySelectorAll('.album-btn').forEach(b => {
                b.classList.remove('active');
            });
            
            // 添加当前活动状态
            this.classList.add('active');
            
            // 加载对应相册的照片
            const albumId = this.getAttribute('data-album');
            loadPhotos(albumId);
        });
    });
    
    // 绑定添加轮播图按钮事件，确保页面加载后按钮即可使用
    bindAddCarouselButtonEvent();
}

// 页面加载完成后初始化相册选择器
window.addEventListener('DOMContentLoaded', function() {
    // 延迟初始化，确保相册已加载
    setTimeout(initAlbumSelectors, 100);
});

// 照片选择器相关变量


// 打开照片选择器






// 加载照片到选择器网格 - 增强版本带错误处理和响应式设计
















// 格式化日期
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}