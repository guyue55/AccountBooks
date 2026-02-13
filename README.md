# AccountBooks 账簿管理系统 2.0

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Django](https://img.shields.io/badge/Django-3.2+-green.svg)
![uv](https://img.shields.io/badge/uv-managed-purple.svg)

一个高颜值、易操作的债务与账务管理系统，旨在帮助用户清晰记录每一笔借贷与还款。

## ✨ 特性

- **现代化 Dashboard**: 实时汇总待收、已全、赖账金额。
- **类视图架构**: 遵循 Django 最佳实践，代码高度可维护。
- **财务级精度**: 使用 `DecimalField` 处理所有金额，防止计算误差。
- **一键管理**: 基于 `Django Jazzmin` 的现代化后台，界面美观且响应式支持极佳。
- **Google 规范**: 严格执行 Google 编码风格，注释详尽。
- **现代包管理**: 使用 `uv` 进行极速依赖安装与环境管理。

## 🚀 快速开始

本项目使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理和虚拟环境构建，请确保已安装 `uv`。

### 1. 环境准备与依赖安装

```bash
# 初始化环境并同步依赖 (会自动创建 .venv)
uv sync
```

### 2. 初始化数据库

```bash
uv run python manage.py makemigrations accounts
uv run python manage.py migrate
```

### 3. 创建管理员

```bash
uv run python manage.py createsuperuser
```

### 4. 启动服务

```bash
uv run python manage.py runserver
```

访问：`http://127.0.0.1:8000`

## 📂 项目结构

- `accounts/`: 业务逻辑核心（模型、视图、路由）。
- `AccountBooks/`: 项目级配置。
- `templates/`: 响应式页面模板。
- `pyproject.toml`: 现代项目配置与依赖定义。
- `LICENSE`: 项目许可证（MIT）。
- `.editorconfig`: 代码格式规范。

## 📝 编码准则

- 遵循 **Google Python Style Guide**。
- 类视图 (CBVs) 优于函数视图。
- 业务逻辑优先下沉至模型层 (Models)。

---
*由 Antigravity 协助构建与优化。*
