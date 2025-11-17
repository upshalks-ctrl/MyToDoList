// 全局配置常量
const API_BASE_URL = '/api';
const ANIMATION_DURATION = 500; // 动画持续时间（毫秒）

// 全局变量
let currentUser = null;
let allTodos = [];
let allTags = [];
let selectedTags = [];
let editSelectedTags = [];
let currentEditingTodo = null;
let currentView = 'add-task';
let currentTagId = null;

// 消息提醒相关变量
let reminderMessages = []; // 存储所有提醒消息
let unreadCount = 0; // 未读消息数量

// 显示消息提示
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message ${type} show`;
    
    setTimeout(() => {
        messageDiv.classList.remove('show');
    }, 3000);
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', async function() {
    await checkAuth();
    setupEventListeners();
    setupMessagePanelEventListeners(); // 设置消息面板事件监听器
    initWebSocket(); // 初始化WebSocket连接以接收实时提醒
    initializeDatePicker(); // 初始化日期选择器
});

// 设置消息面板事件监听器
function setupMessagePanelEventListeners() {
    // 消息通知图标点击事件
    const notificationIcon = document.getElementById('message-notification');
    if (notificationIcon) {
        notificationIcon.addEventListener('click', openMessagePanel);
    }
    
    // 点击页面其他区域关闭消息面板
    document.addEventListener('click', function(e) {
        const panel = document.getElementById('message-panel');
        const notificationIcon = document.getElementById('message-notification');
        
        if (panel && panel.classList.contains('show') && 
            !panel.contains(e.target) && 
            e.target !== notificationIcon && 
            !notificationIcon.contains(e.target)) {
            closeMessagePanel();
        }
    });
}

// 检查用户认证
  async function checkAuth() {
    // 从localStorage获取token - 注意：使用与登录页面一致的'access_token'
    const token = localStorage.getItem('access_token');
    
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/user`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            console.log("Token验证成功，开始解析用户数据");
            currentUser = await response.json();
            console.log('完整用户数据:', currentUser);
            
            if (currentUser.username) {
                document.getElementById('user-name').textContent = currentUser.username;
                console.log("已更新页面上的用户名显示");
            } else {
                console.warn("用户数据中未找到username字段");
            }
            
            console.log("开始加载tags和todos");
            await loadTags(); // 先加载标签，确保标签选择器可用
            await loadTodos(); // 再加载任务
            console.log("tags和todos加载完成");
        } else {
            console.log(`Token验证失败，响应状态码: ${response.status}`);

            localStorage.removeItem('access_token');

            window.location.href = 'index.html';
        }
    } catch (error) {
        console.error('认证检查过程中发生异常:', error);
        localStorage.removeItem('access_token');

        window.location.href = 'index.html';
    }
}

// 加载所有任务
async function loadTodos() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE_URL}/todos`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            allTodos = data.todos;
            await updateViews();
        } else {
            console.error('加载任务失败');
        }
    } catch (error) {
        console.error('加载任务时出错:', error);
    }
}



// 渲染标签列表
function renderTagList() {
    const tagList = document.getElementById('tag-list');
    if (!tagList) {
        return;
    }
    tagList.innerHTML = '';

    allTags.forEach(tag => {
        const tagCount = allTodos.filter(todo => 
            todo.tags.some(t => t.id === tag.id)
        ).length;

        const tagItem = document.createElement('div');
        tagItem.className = 'tag-item';
        tagItem.innerHTML = `
            <div class="tag-color" style="background-color: ${tag.color};"></div>
            <div class="tag-name">${tag.name}</div>
            <div class="tag-count">${tagCount}</div>
        `;
        tagItem.addEventListener('click', () => showTagView(tag));
        tagList.appendChild(tagItem);
    });
}

// 渲染标签选择器
function renderTagSelector() {
    const tagSelector = document.getElementById('tag-selector');
    if (!tagSelector) {
        return;
    }
    tagSelector.innerHTML = '';

    // 渲染现有标签
    allTags.forEach(tag => {
        const tagOption = document.createElement('div');
        tagOption.className = 'tag-option';
        tagOption.dataset.tagId = tag.id;
        
        // 检查是否已选中
        if (selectedTags.includes(tag.id)) {
            tagOption.classList.add('selected');
        }
        
        tagOption.innerHTML = `
            <div class="tag-color" style="background-color: ${tag.color};"></div>
            ${tag.name}
        `;
        tagOption.addEventListener('click', () => toggleTagSelection(tag.id));
        tagSelector.appendChild(tagOption);
    });

    // 添加自定义标签区域
    const customTagSection = document.createElement('div');
    customTagSection.className = 'custom-tag-section';
    
    const customTagForm = document.createElement('div');
    customTagForm.className = 'custom-tag-form';
    
    const customTagName = document.createElement('input');
    customTagName.type = 'text';
    customTagName.id = 'custom-tag-name';
    customTagName.placeholder = '自定义标签名称';
    
    const customTagColor = document.createElement('input');
    customTagColor.type = 'color';
    customTagColor.id = 'custom-tag-color';
    customTagColor.value = '#3498db';
    customTagColor.style.border = '1px solid #ddd';
    customTagColor.style.borderRadius = '4px';
    customTagColor.style.cursor = 'pointer';
    
    const createCustomTagBtn = document.createElement('button');
    createCustomTagBtn.textContent = '创建';
    createCustomTagBtn.className = 'btn-create-tag';
    createCustomTagBtn.addEventListener('click', createCustomTag);
    
    customTagForm.appendChild(customTagName);
    customTagForm.appendChild(customTagColor);
    customTagForm.appendChild(createCustomTagBtn);
    
    customTagSection.appendChild(customTagForm);
    tagSelector.appendChild(customTagSection);
}

// 渲染编辑任务弹框中的标签选择器
function renderEditTagSelector(selectedTagIds = []) {
    const tagSelector = document.getElementById('edit-tag-selector');
    // 添加空检查，避免弹框关闭后访问不存在的元素
    if (!tagSelector) {
        return;
    }
    tagSelector.innerHTML = '';

    // 渲染现有标签
    allTags.forEach(tag => {
        const tagOption = document.createElement('div');
        tagOption.className = 'tag-option';
        tagOption.dataset.tagId = tag.id;
        
        // 检查是否已选中
        if (selectedTagIds.includes(tag.id)) {
            tagOption.classList.add('selected');
        }
        
        tagOption.innerHTML = `
            <div class="tag-color" style="background-color: ${tag.color};"></div>
            ${tag.name}
        `;
        tagOption.addEventListener('click', () => toggleEditTagSelection(tag.id));
        tagSelector.appendChild(tagOption);
    });

    // 添加自定义标签区域
    const customTagSection = document.createElement('div');
    customTagSection.className = 'custom-tag-section';
    
    const customTagForm = document.createElement('div');
    customTagForm.className = 'custom-tag-form';
    
    const customTagName = document.createElement('input');
    customTagName.type = 'text';
    customTagName.id = 'custom-tag-name';
    customTagName.placeholder = '自定义标签名称';
    
    const customTagColor = document.createElement('input');
    customTagColor.type = 'color';
    customTagColor.id = 'custom-tag-color';
    customTagColor.value = '#3498db';
    customTagColor.style.border = '1px solid #ddd';
    customTagColor.style.borderRadius = '4px';
    customTagColor.style.cursor = 'pointer';
    
    const createCustomTagBtn = document.createElement('button');
    createCustomTagBtn.textContent = '创建';
    createCustomTagBtn.className = 'btn-create-tag';
    createCustomTagBtn.addEventListener('click', createCustomTag);
    
    customTagForm.appendChild(customTagName);
    customTagForm.appendChild(customTagColor);
    customTagForm.appendChild(createCustomTagBtn);
    
    customTagSection.appendChild(customTagForm);
    tagSelector.appendChild(customTagSection);
}

// 渲染过滤器标签选项
function renderFilterTags() {
    const filterTag = document.getElementById('filter-tag');
    if (!filterTag) {
        return;
    }
    filterTag.innerHTML = '<option value="">标签</option>';

    allTags.forEach(tag => {
        const option = document.createElement('option');
        option.value = tag.id;
        option.textContent = tag.name;
        filterTag.appendChild(option);
    });
}

// 创建自定义标签
async function createCustomTag() {
    const token = localStorage.getItem('access_token');
    const tagNameInput = document.getElementById('custom-tag-name');
    const tagColorInput = document.getElementById('custom-tag-color');
    
    // 添加空检查，避免元素不存在时出错
    if (!tagNameInput || !tagColorInput) {
        showMessage('创建标签失败：表单元素不可用', 'error');
        return;
    }
    
    const tagName = tagNameInput.value.trim();
    const tagColor = tagColorInput.value;

    if (!tagName) {
        showMessage('请输入标签名称', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/tags`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ name: tagName, color: tagColor })
        });

        if (response.ok) {
            const newTag = await response.json();
            await loadTags(); // 重新加载标签
            
            // 检查当前上下文并更新相应的标签选择器
            const editModal = document.getElementById('edit-task-modal');
            if (editModal && editModal.style.display === 'block') {
                // 如果编辑弹框打开，更新编辑标签选择器
                renderEditTagSelector(editSelectedTags);
                // 在编辑弹框中自动选中新创建的标签
                editSelectedTags.push(newTag.id);
                const editNewTagOption = document.querySelector(`#edit-tag-selector .tag-option[data-tag-id="${newTag.id}"]`);
                if (editNewTagOption) {
                    editNewTagOption.classList.add('selected');
                }
            } else {
                // 否则更新主标签选择器
                renderTagSelector();
                // 在主标签选择器中自动选中新创建的标签
                selectedTags.push(newTag.id);
                const newTagOption = document.querySelector(`#tag-selector .tag-option[data-tag-id="${newTag.id}"]`);
                if (newTagOption) {
                    newTagOption.classList.add('selected');
                }
            }
            
            // 清空输入框
            tagNameInput.value = '';
            tagColorInput.value = '#3498db';
        } else {
            console.error('创建标签失败');
            showMessage('创建标签失败，请重试', 'error');
        }
    } catch (error) {
        console.error('创建标签时出错:', error);
        showMessage('创建标签时出错，请重试', 'error');
    }
}

// 切换标签选择的通用函数
function toggleTagSelectionGeneric(tagId, tagArray, containerId) {
    const index = tagArray.indexOf(tagId);
    const tagOption = document.querySelector(`#${containerId} .tag-option[data-tag-id="${tagId}"]`);
    
    if (index > -1) {
        tagArray.splice(index, 1);
        if (tagOption) {
            tagOption.classList.remove('selected');
        }
    } else {
        tagArray.push(tagId);
        if (tagOption) {
            tagOption.classList.add('selected');
        }
    }
}

// 切换标签选择
function toggleTagSelection(tagId) {
    toggleTagSelectionGeneric(tagId, selectedTags, 'tag-selector');
}

// 切换编辑标签选择
function toggleEditTagSelection(tagId) {
    toggleTagSelectionGeneric(tagId, editSelectedTags, 'edit-tag-selector');
}

// 设置事件监听器
function setupEventListeners() {
    // 退出登录
    document.getElementById('logout-btn').addEventListener('click', logout);

    // 表单提交
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);

    // 导航项点击
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            showView(view);
        });
    });

    // 搜索
    document.getElementById('search-input').addEventListener('input', handleSearch);

    // 过滤器
    document.getElementById('filter-completed').addEventListener('change', handleFilterChange);
    document.getElementById('filter-priority').addEventListener('change', handleFilterChange);
    document.getElementById('filter-tag').addEventListener('change', handleFilterChange);
    document.getElementById('filter-sort-by').addEventListener('change', handleFilterChange);
    document.getElementById('filter-sort-order').addEventListener('change', handleFilterChange);

    // 颜色选择器
    document.querySelectorAll('.color-option').forEach(option => {
        option.addEventListener('click', () => {
            // 移除所有选中状态
            document.querySelectorAll('.color-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            // 添加当前选中状态
            option.classList.add('selected');
            // 设置颜色值
            document.getElementById('tag-color').value = option.dataset.color;
            // 更新样式
            option.style.backgroundColor = option.dataset.color;
        });
    });

    // 点击模态框外部关闭
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('tag-modal');
        if (e.target === modal) {
            closeTagModal();
        }
    });
    
    // 修改任务弹框事件监听器
    document.getElementById('edit-modal-close').addEventListener('click', closeEditModal);
    document.getElementById('cancel-edit').addEventListener('click', closeEditModal);
    document.getElementById('edit-task-form').addEventListener('submit', handleEditTaskSubmit);
    
    // 点击模态框外部关闭弹框
    window.addEventListener('click', (event) => {
        const modal = document.getElementById('edit-task-modal');
        if (event.target === modal) {
            closeEditModal();
        }
    });
}

// 退出登录
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = 'index.html';
}

// 获取或创建"其他"标签
async function getOrCreateOtherTag() {
    // 检查是否已有"其他"标签
    let otherTag = allTags.find(tag => tag.name === '其他');
    
    if (!otherTag) {
        // 创建"其他"标签
        const token = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${API_BASE_URL}/tags`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name: '其他', color: '#95a5a6' })
            });
            
            if (response.ok) {
                otherTag = await response.json();
                await loadTags(); // 重新加载标签
            }
        } catch (error) {
            console.error('创建"其他"标签时出错:', error);
        }
    }
    
    return otherTag;
}

// 处理任务提交
async function handleTaskSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem('access_token');
    
    // 前端表单验证
    const title = document.getElementById('task-title').value;
    const dueDate = document.getElementById('task-due-date').value;
    
    if (!title.trim()) {
        showMessage('任务标题不能为空', 'error');
        return;
    }
    
    if (!dueDate) {
        showMessage('截止时间不能为空', 'error');
        return;
    }
    
    // 检查截止时间是否早于当前时间
    const dueDateTime = new Date(dueDate);
    const currentTime = new Date();
    if (dueDateTime <= currentTime) {
        showMessage('截止时间必须晚于当前时间', 'error');
        return;
    }
    
    let tags = [...selectedTags];
    
    // 如果没有选择标签，添加"其他"标签
    if (tags.length === 0) {
        const otherTag = await getOrCreateOtherTag();
        if (otherTag) {
            tags.push(otherTag.id);
        }
    }
    
    const formData = new FormData(e.target);
    // 处理截止时间：将用户输入的北京时间转换为UTC时间
    const taskData = {
        title: formData.get('title').trim(),
        description: formData.get('description').trim(),
        due_date: dueDate ? convertBeijingTimeToUTC(dueDate) : null,
        priority: parseInt(formData.get('priority')),
        tags: tags
    };

    try {
        const response = await fetch(`${API_BASE_URL}/todos`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(taskData)
        });

        if (response.ok) {
            // 重置表单
            e.target.reset();
            selectedTags = [];
            document.querySelectorAll('.tag-option').forEach(option => {
                option.classList.remove('selected');
            });
            
            await loadTodos();
            showMessage('任务添加成功', 'success');
        } else {
            const errorData = await response.json();
            showMessage(errorData.message || '添加任务失败', 'error');
        }
    } catch (error) {
        console.error('添加任务时出错:', error);
        showMessage('网络错误，添加任务失败', 'error');
    }
}

// 显示视图
function showView(view) {
    // 隐藏所有视图
    document.querySelectorAll('.view').forEach(v => {
        v.style.display = 'none';
    });

    // 激活导航项
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.nav-item[data-view="${view}"]`).classList.add('active');

    // 显示选中的视图
    document.getElementById(`${view}-view`).style.display = 'block';
    currentView = view;
    currentTagId = null;

    // 根据不同视图进行特殊处理
    if (view === 'filter') {
        // 重置所有过滤器选项为默认值
        document.getElementById('filter-completed').value = '';
    document.getElementById('filter-priority').value = '';
    document.getElementById('filter-tag').value = '';
    document.getElementById('filter-sort-by').value = '';
    document.getElementById('filter-sort-order').value = 'asc';
        renderFilterTags();
        handleFilterChange(); // 加载所有任务
    } else if (view === 'search') {
        // 清空搜索框并立即显示所有任务
        document.getElementById('search-input').value = '';
        handleSearch();
    }

    // 更新视图内容
    updateViews();
}

// 显示标签视图
function showTagView(tag) {
    // 隐藏所有视图
    document.querySelectorAll('.view').forEach(v => {
        v.style.display = 'none';
    });

    // 激活导航项
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    // 显示标签视图
    const tagView = document.getElementById('tag-view');
    tagView.style.display = 'block';
    document.getElementById('tag-view-title').textContent = `${tag.name} 任务`;
    currentView = 'tag';
    currentTagId = tag.id;

    // 更新标签视图内容
    renderTagTasks(tag.id);
}

// 渲染已使用的标签集合
function renderUsedTags() {
    const usedTagsList = document.getElementById('used-tags-list');
    if (!usedTagsList) {
        return;
    }
    usedTagsList.innerHTML = '';

    // 收集所有任务中使用过的标签
    const tagCount = {};
    allTodos.forEach(todo => {
        if (todo.tags && todo.tags.length > 0) {
            todo.tags.forEach(tag => {
                tagCount[tag.id] = (tagCount[tag.id] || 0) + 1;
            });
        }
    });

    // 遍历标签并渲染
    allTags.forEach(tag => {
        if (tagCount[tag.id]) {
            const tagElement = document.createElement('div');
            tagElement.className = 'used-tag';
            tagElement.innerHTML = `
                <div class="tag-color" style="background-color: ${tag.color};"></div>
                <span class="tag-name">${tag.name}</span>
                <span class="tag-count">${tagCount[tag.id]}</span>
            `;
            
            // 添加点击事件，点击后显示该标签的所有任务
            tagElement.addEventListener('click', () => showTagView(tag));
            
            usedTagsList.appendChild(tagElement);
        }
    });
}

// 更新所有视图
async function updateViews() {
    await renderTodayTasks();
    await renderPreview();
    renderUsedTags();
    renderTagList(); // 添加这行，确保标签计数同步更新
    await handleFilterChange(); // 等待过滤器任务加载完成
    // 重新渲染主任务列表以显示最新修改
    renderTaskList('tasks', allTodos);
}

// 渲染今天的任务
async function renderTodayTasks() {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_BASE_URL}/todos/today`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('获取今日任务失败');
        }
        
        const data = await response.json();
        const todayTodos = data.todos;

        renderTaskList('today-tasks', todayTodos);
    } catch (error) {
        console.error('渲染今日任务失败:', error);
    }
}

// 渲染预览（任务日历）
async function renderPreview(startDate = null) {
    try {
        const token = localStorage.getItem('access_token');
        let url = `${API_BASE_URL}/todos/week`;
        
        // 如果提供了起始日期，添加到URL参数
        if (startDate) {
            url += `?start_date=${startDate}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('获取任务日历数据失败');
        }
        
        const data = await response.json();
        const { week_tasks } = data;

        // 渲染一周任务日历
        renderWeekCalendar(week_tasks);
    } catch (error) {
        console.error('渲染任务日历失败:', error);
        showMessage('加载任务日历失败', 'error');
    }
}

// 渲染一周任务日历
function renderWeekCalendar(week_tasks) {
    const calendarGrid = document.getElementById('calendar-grid');
    if (!calendarGrid) {
        return;
    }
    calendarGrid.innerHTML = '';
    
    // 获取今天的日期字符串，用于标记今天
    const today = new Date().toISOString().split('T')[0];
    
    week_tasks.forEach(day_data => {
        const dayElement = document.createElement('div');
        dayElement.className = `calendar-day ${day_data.formatted_date === today ? 'today' : ''}`;
        
        // 创建日期头部
        const dayHeader = document.createElement('div');
        dayHeader.className = 'day-header';
        
        const dayName = document.createElement('div');
        dayName.className = 'day-name';
        // 只显示星期几的前三个字符
        dayName.textContent = day_data.day_name.substring(0, 3);
        
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = new Date(day_data.date).getDate();
        
        dayHeader.appendChild(dayName);
        dayHeader.appendChild(dayNumber);
        
        // 创建任务容器
        const tasksContainer = document.createElement('div');
        tasksContainer.className = 'calendar-tasks';
        
        // 添加任务
        day_data.tasks.forEach(task => {
            const taskElement = document.createElement('div');
            let priorityClass = '';
            
            switch (task.priority) {
                case 3:
                    priorityClass = 'task-priority-high';
                    break;
                case 2:
                    priorityClass = 'task-priority-medium';
                    break;
                case 1:
                    priorityClass = 'task-priority-low';
                    break;
            }
            
            taskElement.className = `calendar-task ${task.completed ? 'completed' : ''} ${priorityClass}`;
            taskElement.textContent = task.title;
            
            // 点击任务可以编辑或查看详情（这里只是简单的alert）
            taskElement.addEventListener('click', () => {
                alert(`任务: ${task.title}\n截止时间: ${new Date(task.due_date).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`);
            });
            
            tasksContainer.appendChild(taskElement);
        });
        
        // 添加任务数量
        const taskCount = document.createElement('div');
        taskCount.className = 'task-count';
        taskCount.textContent = `${day_data.task_count}个任务`;
        
        // 组装当天的元素
        dayElement.appendChild(dayHeader);
        dayElement.appendChild(tasksContainer);
        dayElement.appendChild(taskCount);
        
        // 添加到日历网格
        calendarGrid.appendChild(dayElement);
    });
}

// 处理搜索
async function handleSearch() {
    const searchTerm = document.getElementById('search-input').value;
    try {
        const token = localStorage.getItem('access_token');
        let response;
        
        // 如果搜索框为空，获取所有任务，否则执行搜索
        if (searchTerm.trim() === '') {
            response = await fetch(`${API_BASE_URL}/todos`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        } else {
            response = await fetch(`${API_BASE_URL}/todos?search=${encodeURIComponent(searchTerm)}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
        }
        
        if (!response.ok) {
            throw new Error('搜索任务失败');
        }
        
        const data = await response.json();
        const filteredTodos = data.todos;

        renderTaskList('search-results', filteredTodos);
    } catch (error) {
        console.error('搜索失败:', error);
    }
}

// 处理过滤器变化
async function handleFilterChange() {
    const completed = document.getElementById('filter-completed').value;
    const priority = document.getElementById('filter-priority').value;
    const tagId = document.getElementById('filter-tag').value;
    const sortBy = document.getElementById('filter-sort-by').value;
    const sortOrder = document.getElementById('filter-sort-order').value;

    // 构建查询参数，只添加非空字符串的参数
    const params = new URLSearchParams();
    if (completed && completed.trim() !== '') params.append('completed', completed);
    if (priority && priority.trim() !== '') params.append('priority', priority);
    if (tagId && tagId.trim() !== '') params.append('tag_id', tagId);
    if (sortBy && sortBy.trim() !== '') params.append('sort_by', sortBy);
    if (sortOrder && sortOrder.trim() !== '') params.append('sort_order', sortOrder);

    try {
        const token = localStorage.getItem('access_token');
        
        const response = await fetch(`${API_BASE_URL}/todos?${params.toString()}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log("API响应状态:", response.status);
        console.log("API响应状态文本:", response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error('获取过滤任务失败: ' + errorText);
        }
        
        const data = await response.json();
        const filteredTodos = data.todos;

        renderTaskList('filtered-tasks', filteredTodos);
    } catch (error) {
        console.error('过滤失败:', error);
    }
}

// 渲染标签任务
function renderTagTasks(tagId) {
    const filteredTodos = allTodos.filter(todo => 
        todo.tags && todo.tags.some(t => t.id === tagId)
    );

    renderTaskList('tag-tasks', filteredTodos);
}

// 渲染任务列表
function renderTaskList(containerId, todos) {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }
    container.innerHTML = '';

    if (todos.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">暂无任务</div>';
        return;
    }

    todos.forEach(todo => {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        
        // 优先级样式
        let priorityClass = '';
        switch(todo.priority) {
            case 1: priorityClass = 'priority-low'; break;
            case 2: priorityClass = 'priority-medium'; break;
            case 3: priorityClass = 'priority-high'; break;
        }

        // 任务标签
        let tagsHtml = '';
        if (todo.tags && todo.tags.length > 0) {
            tagsHtml = '<div class="task-tags">';
            todo.tags.forEach(tag => {
                tagsHtml += `<div class="task-tag" style="background-color: ${tag.color};">${tag.name}</div>`;
            });
            tagsHtml += '</div>';
        }

        taskItem.innerHTML = `
            <div class="task-content">
                <div class="task-header">
                    <div class="task-title ${todo.completed ? 'completed' : ''}">${todo.title}</div>
                </div>
                ${todo.description ? `<div class="task-description">${todo.description}</div>` : ''}
                <div class="task-meta">
                    ${todo.due_date ? `<div class="task-due-date"><i class="fas fa-calendar-alt"></i> ${new Date(todo.due_date+'Z').toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}</div>` : ''}
                    <div class="task-priority ${priorityClass}">
                        ${todo.priority === 1 ? '低' : todo.priority === 2 ? '中' : '高'}优先级
                    </div>
                </div>
                ${tagsHtml}
            </div>
            <div class="task-actions">
                <button class="btn btn-small btn-complete" data-todo-id="${todo.id}" ${todo.completed ? 'disabled' : ''}>
                    <i class="fas fa-check"></i> 完成
                </button>
                <button class="btn btn-small btn-delete" data-todo-id="${todo.id}">
                    <i class="fas fa-trash"></i> 删除
                </button>
                <button class="btn btn-small btn-edit" data-todo-id="${todo.id}">
                    <i class="fas fa-edit"></i> 修改
                </button>
            </div>
        `;

        // 添加事件监听器
        const completeBtn = taskItem.querySelector('.btn-complete');
        completeBtn.addEventListener('click', () => completeTodo(todo.id, taskItem));
        
        const deleteBtn = taskItem.querySelector('.btn-delete');
        deleteBtn.addEventListener('click', () => deleteTodo(todo.id, taskItem));

        const editBtn = taskItem.querySelector('.btn-edit');
        editBtn.addEventListener('click', () => editTodo(todo));

        container.appendChild(taskItem);
    });
}


// 编辑任务
function editTodo(todo) {
    // 保存当前编辑的任务
    currentEditingTodo = todo;
    
    // 填充任务信息到表单
    document.getElementById('edit-task-id').value = todo.id;
    document.getElementById('edit-task-title').value = todo.title;
    document.getElementById('edit-task-description').value = todo.description || '';
    
    // 处理截止时间 - 需要转换为本地时间格式
    if (todo.due_date) {
        const dueDate = new Date(todo.due_date);
        // 转换为YYYY-MM-DDTHH:MM格式
        const localDueDate = dueDate.toISOString().slice(0, 16);
        document.getElementById('edit-task-due-date').value = localDueDate;
    } else {
        document.getElementById('edit-task-due-date').value = '';
    }
    
    // 设置优先级
    document.getElementById('edit-task-priority').value = todo.priority;
    
    // 加载并选中标签
    editSelectedTags = todo.tags ? todo.tags.map(tag => tag.id) : [];
    renderEditTagSelector(editSelectedTags);
    
    // 显示弹框
    const modal = document.getElementById('edit-task-modal');
    modal.style.display = 'block';
    
    // 立即聚焦到标题输入框
    const titleInput = document.getElementById('edit-task-title');
    titleInput.focus();
    titleInput.select();
    // 将光标移动到输入框末尾
    titleInput.setSelectionRange(titleInput.value.length, titleInput.value.length);
    
    // 确保其他输入框在点击时也能正确获得焦点
    const inputs = modal.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('click', function() {
            this.focus();
        });
        input.addEventListener('mousedown', function(e) {
            e.preventDefault();
            this.focus();
        });
    });
}

// 完成任务
async function completeTodo(todoId, taskElement) {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE_URL}/todos/${todoId}/toggle`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            // 添加完成动画效果
            taskElement.style.opacity = '0.5';
            taskElement.style.textDecoration = 'line-through';
            taskElement.style.transition = `opacity ${ANIMATION_DURATION}ms, text-decoration ${ANIMATION_DURATION}ms`;
            
            setTimeout(async () => {
                // 重新加载所有任务并更新所有视图
                await loadTodos();
            }, ANIMATION_DURATION);
        } else {
            showMessage('标记任务完成失败，请重试', 'error');
        }
    } catch (error) {
        console.error('标记任务完成时出错:', error);
        showMessage('标记任务完成时出错，请重试', 'error');
    }
}

// 删除任务
async function deleteTodo(todoId, taskElement) {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE_URL}/todos/${todoId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            // 添加滑动动画
            taskElement.style.transform = 'translateX(-100%)';
            taskElement.style.opacity = '0';
            taskElement.style.transition = `transform ${ANIMATION_DURATION}ms, opacity ${ANIMATION_DURATION}ms`;
            
            setTimeout(async () => {
                // 重新加载所有任务并更新所有视图
                await loadTodos();
            }, ANIMATION_DURATION);
        } else {
            console.error('删除任务失败');
        }
    } catch (error) {
        console.error('删除任务时出错:', error);
    }
}


// 加载所有标签
async function loadTags() {
    const token = localStorage.getItem('access_token');
    try {
        const response = await fetch(`${API_BASE_URL}/tags`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            allTags = data.tags;
            renderTagList();
            renderTagSelector();
            renderFilterTags();
        } else {
            console.error('加载标签失败');
        }
    } catch (error) {
        console.error('加载标签时出错:', error);
    }
}

// WebSocket实时提醒功能
let socket = null;

// 初始化WebSocket连接
function initWebSocket() {
    // 获取当前用户ID
    const userId = localStorage.getItem('user_id');
    if (!userId) return;
    
    // 根据当前协议选择WebSocket协议（http->ws, https->wss）
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // WebSocket连接到后端服务器（5000端口）
    const wsUrl = `${protocol}//${window.location.hostname}:5000`;
    
    try {
        // 创建WebSocket连接
        socket = io(wsUrl);
        
        // 连接成功后加入用户房间
        socket.on('connect', () => {
            console.log('WebSocket连接成功');
            socket.emit('join_room', userId);
        });
        
        // 接收提醒消息
        socket.on('reminder', (data) => {
            addReminderMessages(data.tasks);
        });
        
        // 连接断开时重连
        socket.on('disconnect', () => {
            console.log('WebSocket连接断开，尝试重连...');
            setTimeout(initWebSocket, 5000);
        });
        
    } catch (error) {
        console.error('初始化WebSocket连接失败:', error);
        // 重连尝试
        setTimeout(initWebSocket, 5000);
    }
}

// 添加提醒消息到消息列表
function addReminderMessages(tasks) {
    tasks.forEach(task => {
        const message = {
            id: `reminder-${Date.now()}-${task.id}`, // 使用唯一ID避免与任务ID冲突
            task_id: task.id, // 存储任务ID用于查看详情
            title: task.title,
            due_date: task.due_date,
            received_at: new Date(),
            read: false
        };
        reminderMessages.unshift(message); // 添加到消息列表开头
        unreadCount++;
    });
    
    updateNotificationCount();
    renderMessagePanel();
    
    // 显示桌面通知（如果浏览器支持）
    if (Notification.permission === "granted") {
        tasks.forEach(task => {
            new Notification('任务即将到期', {
                body: `任务: ${task.title}\n截止时间: ${new Date(task.due_date +'Z').toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}\n点击查看详情`
            });
        });
    }
}

// 更新通知数量显示
function updateNotificationCount() {
    const countElement = document.getElementById('notification-count');
    if (countElement) {
        countElement.textContent = unreadCount;
        countElement.style.display = unreadCount > 0 ? 'flex' : 'none';
    }
}

// 渲染消息面板
function renderMessagePanel() {
    const contentElement = document.getElementById('message-panel-content');
    if (!contentElement) return;
    
    if (reminderMessages.length === 0) {
        contentElement.innerHTML = '<div class="no-messages">暂无提醒消息</div>';
        return;
    }
    
    contentElement.innerHTML = '';
    
    reminderMessages.forEach(message => {
        const messageElement = document.createElement('div');
        messageElement.className = `message-item ${message.read ? '' : 'unread'}`;
        messageElement.onclick = () => markMessageAsRead(message.id);
        
        messageElement.innerHTML = `
            <div class="message-item-title">${message.title}</div>
            <div class="message-item-due">
                截止时间: ${new Date(message.due_date +'Z').toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
            </div>
            <div class="message-item-time">
                提醒时间: ${new Date(message.received_at).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
            </div>
        `;
        
        contentElement.appendChild(messageElement);
    });
}

// 标记消息为已读
function markMessageAsRead(messageId) {
    const message = reminderMessages.find(m => m.id === messageId);
    if (message) {
        // 查找对应的任务
        const task = allTodos.find(t => t.id === message.task_id);
        
        if (task) {
            showTaskDetail(task);
        } else {
            console.error('未找到对应的任务:', message.task_id);
        }
        
        if (!message.read) {
            message.read = true;
            unreadCount--;
            updateNotificationCount();
            renderMessagePanel();
        }
    }
}

// 将北京时间转换为UTC时间
function convertBeijingTimeToUTC(beijingTimeStr) {
    // beijingTimeStr格式：YYYY-MM-DDTHH:MM（来自datetime-local输入）
    // 注意：datetime-local输入会将用户选择的时间转换为浏览器本地时区
    // 我们需要明确将其视为北京时间（UTC+8）进行处理
    
    // 解析日期和时间部分
    const [datePart, timePart] = beijingTimeStr.split('T');
    const [year, month, day] = datePart.split('-').map(Number);
    const [hours, minutes] = timePart.split(':').map(Number);
    
    // 创建一个UTC时间对象，手动计算UTC时间
    // 北京时间 = UTC时间 + 8小时，所以UTC时间 = 北京时间 - 8小时
    const utcDate = new Date(Date.UTC(year, month - 1, day, hours - 8, minutes));
    
    // 转换为UTC时间的ISO字符串
    return utcDate.toISOString();
}

// 显示任务详情模态框
function showTaskDetail(task) {
    // 获取模态框元素
    const modal = document.getElementById('task-detail-modal');
    
    if (!modal) {
        console.error('未找到任务详情模态框元素');
        return;
    }
    
    // 填充任务详情
    document.getElementById('detail-title').textContent = task.title || '无标题';
    document.getElementById('detail-description').textContent = task.description || '';
    
    // 格式化日期时间
    const dueDate = task.due_date ? new Date(task.due_date +'Z').toLocaleString('zh-CN', {
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'Asia/Shanghai'
    }) : '';
    document.getElementById('detail-due-date').textContent = dueDate;
    
    document.getElementById('detail-priority').textContent = task.priority || '无';
    
    // 格式化创建时间
    const createdAt = task.created_at ? new Date(task.created_at).toLocaleString('zh-CN', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit',
        hour: '2-digit', 
        minute: '2-digit',
        timeZone: 'Asia/Shanghai'
    }) : '';
    document.getElementById('detail-created-at').textContent = createdAt;
    
    // 显示标签
    const tagsElement = document.getElementById('task-detail-tags');
    tagsElement.innerHTML = '';
    
    if (task.tags && task.tags.length > 0) {
        task.tags.forEach(tag => {
            const tagSpan = document.createElement('span');
            tagSpan.className = 'tag-badge';
            tagSpan.innerHTML = `<div class="tag-color" style="background-color: ${tag.color};"></div>${tag.name}`;
            tagsElement.appendChild(tagSpan);
        });
    } else {
        tagsElement.textContent = '无标签';
        tagsElement.style.color = '#999';
        tagsElement.style.fontStyle = 'italic';
    }
    
    // 显示模态框
    modal.classList.add('show');
}

// 关闭任务详情模态框
function closeTaskDetailModal() {
    const modal = document.getElementById('task-detail-modal');
    if (modal) {
        modal.classList.remove('show');
    }
}

// 添加任务详情模态框事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 关闭按钮点击事件
    const closeBtn = document.querySelector('#task-detail-modal .modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeTaskDetailModal);
    }
    
    // 点击模态框外部关闭模态框
    const modal = document.getElementById('task-detail-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeTaskDetailModal();
            }
        });
    }
    
    // 按下ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeTaskDetailModal();
        }
    });
});

// 打开消息面板
function openMessagePanel() {
    const panel = document.getElementById('message-panel');
    if (panel) {
        panel.classList.add('show');
    }
}

// 关闭消息面板
function closeMessagePanel() {
    const panel = document.getElementById('message-panel');
    if (panel) {
        panel.classList.remove('show');
    }
}

// 页面加载完成后初始化所有功能 - 已合并到上面的DOMContentLoaded事件监听器中

// 初始化日期选择器
function initializeDatePicker() {
    const startDateInput = document.getElementById('start-date');
    const refreshButton = document.getElementById('refresh-calendar');
    
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    startDateInput.value = today;
    
    // 添加刷新按钮事件监听
    refreshButton.addEventListener('click', function() {
        const selectedDate = startDateInput.value;
        renderPreview(selectedDate);
    });
    
    // 也可以添加日期输入框的change事件监听
    startDateInput.addEventListener('change', function() {
        const selectedDate = this.value;
        renderPreview(selectedDate);
    });
}

// 关闭编辑任务弹框
function closeEditModal() {
    const modal = document.getElementById('edit-task-modal');
    modal.style.display = 'none';
    currentEditingTodo = null;
    editSelectedTags = [];
}

// 处理修改任务表单提交
async function handleEditTaskSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const taskId = formData.get('id');
    const title = formData.get('title');
    const description = formData.get('description');
    const dueDate = formData.get('due_date');
    const priority = parseInt(formData.get('priority'));
    
    // 验证截止时间
    if (!dueDate) {
        showMessage('请选择截止时间', 'error');
        return;
    }
    
    const dueDateTime = new Date(dueDate);
    
    // 检查截止时间是否合法
    if (isNaN(dueDateTime.getTime())) {
        showMessage('截止时间格式不正确', 'error');
        return;
    }
    
    // 注意：这里我们不检查截止时间是否晚于当前时间，因为用户可能需要修改一个已经过期的任务
    
    // 准备任务数据 - 将用户输入的北京时间转换为UTC时间
    const taskData = {
        title,
        description: description || '',
        due_date: dueDate ? convertBeijingTimeToUTC(dueDate) : null,
        priority,
        tags: editSelectedTags
    };
    
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch(`${API_BASE_URL}/todos/${taskId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });
        
        if (response.ok) {
            const updatedTodo = await response.json();
            
            // 更新本地任务列表
            const todoIndex = allTodos.findIndex(todo => todo.id === taskId);
            if (todoIndex > -1) {
                allTodos[todoIndex] = updatedTodo;
            }
            
            // 全面更新所有视图，确保修改后的任务在所有地方都能实时显示
            await updateViews();
            
            // 重新渲染搜索结果（如果当前在搜索视图）
            const searchView = document.getElementById('search-view');
            if (searchView && searchView.style.display !== 'none') {
                // 直接调用handleSearch函数来更新搜索结果
                await handleSearch();
            }
            
            // 重新渲染标签视图（如果当前在标签视图）
            const tagView = document.getElementById('tag-view');
            if (tagView && tagView.style.display !== 'none' && currentTagId) {
                await renderTagTasks(currentTagId);
            }
            
            // 关闭弹框
            closeEditModal();
            
            // 显示成功消息
            showMessage('任务修改成功', 'success');
        } else {
            const errorText = await response.text();
            console.error('修改任务失败:', errorText);
            showMessage('修改任务失败: ' + errorText, 'error');
        }
    } catch (error) {
        console.error('修改任务时出错:', error);
        showMessage('修改任务时出错: ' + error.message, 'error');
    }
}