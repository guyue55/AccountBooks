#!/usr/bin/env python3
"""
使用 AppleScript + macOS screencapture 为 AccountBooks 自动截图。
通过模拟键盘操作登录（不依赖 JavaScript 注入）。
"""

import subprocess
import time
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://127.0.0.1:8001"


def applescript(script: str):
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️ AppleScript warning: {result.stderr.strip()}")
    return result.returncode == 0


def go_to(url: str, wait: float = 3.0):
    """在 Chrome 地址栏输入 URL 并跳转。"""
    applescript(f'''
        tell application "Google Chrome"
            activate
            set URL of active tab of front window to "{url}"
        end tell
    ''')
    time.sleep(wait)


def screenshot(path: str):
    """截取当前屏幕的最前 Chrome 窗口。"""
    applescript('tell application "Google Chrome" to activate')
    time.sleep(1)
    subprocess.run(["screencapture", "-x", "-R0,23,1440,900", path], check=True)
    print(f"  ✅ {path}")


def main():
    print("🖥️  Preparing Chrome window...")
    # 设置窗口大小
    applescript('''
        tell application "Google Chrome"
            activate
            set bounds of front window to {0, 23, 1440, 923}
        end tell
    ''')
    time.sleep(1)

    # ── 登录 ──
    print("🔐 Navigating to login page...")
    go_to(f"{BASE_URL}/login", wait=2.5)

    print("  Typing credentials via keyboard...")
    applescript('''
        tell application "System Events"
            tell process "Google Chrome"
                -- Tab 到 username 框
                keystroke tab
                delay 0.3
                -- 点击用户名输入框区域（通用位置）
            end tell
        end tell
    ''')

    # 用 keyboard shortcut 聚焦地址栏然后执行实际登录（使用表单提交URL）
    # 更可靠的方法：直接通过带参数的 POST URL 或 session cookie 注入不可行
    # 改用 UI 模拟：Tab 键导航 + keystroke
    applescript(f'''
        tell application "System Events"
            tell process "Google Chrome"
                set frontmost to true
                delay 0.5
                -- 点击页面上的 username 输入框 (通过 tab key 导航)
                key code 48  -- Tab
                delay 0.3
                key code 48  -- Tab 
                delay 0.3
            end tell
        end tell
    ''')

    # 更可靠方案：用 curl 获取 CSRF token，然后 POST 创建 session 非常复杂
    # 最简单方案：打开登录页，等待用户手动登录，或者直接截图已登录状态

    # --- 使用 curl + cookie jar 来做 session ---
    print("  Using curl to login and get session cookie...")
    # 先获取登录页拿 csrf token
    cookie_jar = "/tmp/ab_cookies.txt"
    csrf_result = subprocess.run(
        ["curl", "-c", cookie_jar, "-s", "-o", "/tmp/login_page.html",
         f"{BASE_URL}/login"],
        capture_output=True, text=True
    )

    # 从 HTML 中提取 csrf token
    import re
    with open("/tmp/login_page.html", "r") as f:
        html = f.read()
    csrf_match = re.search(r'csrfmiddlewaretoken.*?value="([^"]+)"', html)
    if not csrf_match:
        print("  ❌ Cannot find CSRF token, aborting.")
        return
    csrf_token = csrf_match.group(1)
    print(f"  Got CSRF token: {csrf_token[:10]}...")

    # POST 登录
    subprocess.run([
        "curl", "-b", cookie_jar, "-c", cookie_jar, "-s",
        "-o", "/dev/null",
        "-X", "POST", f"{BASE_URL}/login",
        "--data", f"username=admin&password=admin123&csrfmiddlewaretoken={csrf_token}",
        "-H", f"Referer: {BASE_URL}/login",
        "-L"
    ])
    print("  Logged in via curl.")

    # 把 cookies 注入 Chrome
    # 读取 cookie jar 中的 sessionid
    with open(cookie_jar, "r") as f:
        cookie_content = f.read()
    
    session_match = re.search(r'sessionid\s+(\S+)', cookie_content)
    csrf_cookie_match = re.search(r'csrftoken\s+(\S+)', cookie_content)
    
    if not session_match:
        print("  ❌ No session cookie found.")
        return
    
    session_id = session_match.group(1)
    csrf_cookie = csrf_cookie_match.group(1) if csrf_cookie_match else ""
    print(f"  Got session: {session_id[:10]}...")

    # 通过 Chrome DevTools Protocol 注入 cookie
    # 先打开一个空页面，通过 URL 设置 cookie
    applescript(f'''
        tell application "Google Chrome"
            activate
            set URL of active tab of front window to "javascript:void(0)"
        end tell
    ''')
    time.sleep(1)

    # 用 Chrome 的地址栏 JS 注入（如果 AppleScript JS 被禁止，试 bookmarklet）
    # 替代方案：让 Chrome 访问一个带 cookie 的中间页
    # 最直接：打开页面后手动等待 or 直接用 sessionid 在 URL 参数 -- Django 不支持

    # 最终方案：直接在命令行用 open 打开 Chrome
    os.system(f'open -na "Google Chrome" --args --no-first-run "javascript:document.cookie=\'sessionid={session_id};path=/\'"')
    time.sleep(1)

    # 直接导航（此时 session cookie 已在 curl 的 cookie jar 中）
    # 但 Chrome 不会读取 curl 的 cookie jar...

    # ─── 最终兜底方案：手动打开登录页，用 System Events 模拟键盘输入 ───
    print("  Falling back to keyboard simulation login...")
    go_to(f"{BASE_URL}/login", wait=2)

    # 聚焦到 username 输入框（大多数登录页的第一个可 tab 到的输入框）
    applescript('''
        tell application "System Events"
            tell process "Google Chrome"
                set frontmost to true
                delay 0.5
                -- 点击页面内容区
                click at {720, 450}
                delay 0.5
                -- Tab 到第一个输入框
                keystroke tab
                delay 0.3
            end tell
        end tell
    ''')
    time.sleep(0.5)

    # 用 keystroke 输入用户名和密码
    applescript('''
        tell application "System Events"
            keystroke "admin"
            delay 0.3
            keystroke tab
            delay 0.3
            keystroke "admin123"
            delay 0.3
            key return
        end tell
    ''')
    time.sleep(3)

    # ────── 开始截图 ──────
    pages = [
        ("Dashboard", f"{BASE_URL}/", "dashboard.png", 3),
        ("Orders",    f"{BASE_URL}/orders", "orders.png", 2.5),
        ("Customers", f"{BASE_URL}/customers", "customers.png", 2.5),
        ("Goods",     f"{BASE_URL}/goods", "goods.png", 2.5),
    ]

    for name, url, filename, wait in pages:
        print(f"📸 {name}...")
        go_to(url, wait=wait)
        screenshot(str(OUTPUT_DIR / filename))

    # 主题切换器
    print("📸 Theme Switcher...")
    go_to(f"{BASE_URL}/", wait=2.5)
    # 点击 user-profile 区域打开下拉 (大约在左下角)
    applescript('''
        tell application "System Events"
            tell process "Google Chrome"
                set frontmost to true
                delay 0.3
                click at {85, 860}
            end tell
        end tell
    ''')
    time.sleep(1.5)
    screenshot(str(OUTPUT_DIR / "theme_switcher.png"))

    print(f"\n🎉 All screenshots saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
