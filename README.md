# AccountBooks 账簿管理系统 2.0

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Django](https://img.shields.io/badge/Django-3.2+-green.svg)

一个高颜值、易操作的债务与账务管理系统，旨在帮助用户清晰记录每一笔借贷与还款。

## ✨ 特性

- **现代化 Dashboard**: 实时汇总待收、已全、赖账金额。
- **类视图架构**: 遵循 Django 最佳实践，代码高度可维护。
- **财务级精度**: 使用 `DecimalField` 处理所有金额，防止计算误差。
- **一键管理**: 基于 `SimpleUI` 的精美后台，集成富文本编辑。
- **Google 规范**: 严格执行 Google 编码风格，注释详尽。

## 🚀 快速开始

### 1. 环境准备

建议使用虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 初始化数据库

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### 4. 创建管理员

```bash
python manage.py createsuperuser
```

### 5. 启动服务

```bash
python manage.py runserver
```
访问：`http://127.0.0.1:8000`

## 📂 项目结构

- `accounts/`: 业务逻辑核心（模型、视图、路由）。
- `AccountBooks/`: 项目级配置。
- `templates/`: 响应式页面模板。
- `requirements.txt`: 传统依赖清单。
- `pyproject.toml`: 现代项目配置（PEP 621）。
- `LICENSE`: 项目许可证（MIT）。
- `.editorconfig`: 代码格式规范。

## 📝 编码准则

- 遵循 **Google Python Style Guide**。
- 类视图 (CBVs) 优于函数视图。
- 业务逻辑优先下沉至模型层 (Models)。

---
*由 Antigravity 协助构建与优化。*
