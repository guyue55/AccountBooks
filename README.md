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

## 🚀 快速开始 (Quick Start)

### 1. 一键初始化 (推荐)
如果您是第一次运行本项目，可以使用我们提供的一键初始化脚本，自动完成依赖安装、数据库迁移和管理员创建：

```bash
# 确保已安装 uv (https://github.com/astral-sh/uv)
./init_project.sh
```

脚本执行完成后，将自动创建默认管理员：
- **用户名**: `admin`
- **密码**: `admin123`

### 2. 手动安装
如果更喜欢手动操作：

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

### 3. 生产环境部署 (Production)
为了获得更好的性能和稳定性，我们提供了生产环境启动脚本，使用 **Gunicorn** 作为应用服务器：

```bash
# 1. 确保已完成初始化 (见上文)
./init_project.sh

# 2. 启动生产服务
./start_prod.sh
```

此脚本会自动执行：
- 收集静态文件 (`collectstatic`)
- 启动 4 个 Gunicorn 工作进程
- 监听 `0.0.0.0:8000`

> **注意**: 在生产环境中，建议配合 **Nginx** 反向代理使用，以处理静态文件和 SSL 证书。

## 🛠️ 技术栈 (Tech Stack)

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
