"""
AccountBooks 自动化截图工具。

该脚本使用 Playwright 驱动浏览器，自动执行以下操作：
1. 登录系统。
2. 抓取各个核心业务页面（概览、订单、商品、客户）。
3. 测试主题切换功能并抓取预览图。

所有截图将保存至项目根目录下的 docs/screenshots/ 文件夹。
"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

# ===========================================================================
# 配置区域
# ===========================================================================

# 基础 URL 和认证信息（优先从环境变量读取）
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin123")

# 截图保存目录
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 定义需要抓取的页面任务
SCREENSHOT_TASKS = [
    {
        "name": "dashboard",
        "path": "/",
        "wait_for": ".stats-grid",
    },  # 统计卡片
    {
        "name": "orders",
        "path": "/orders/",
        "wait_for": ".table-container",
    },  # 交易列表
    {
        "name": "customers",
        "path": "/customers/",
        "wait_for": ".table-container",
    },  # 客户管理
    {
        "name": "goods",
        "path": "/goods/",
        "wait_for": ".table-container",
    },  # 商品管理
]


class ScreenshotAutomation:
    """AccountBooks 自动化截图类。"""

    def __init__(self, base_url: str, headless: bool = False):
        """
        初始化自动化对象。

        Args:
            base_url: 目标系统的基础 URL。
            headless: 是否以无头模式运行浏览器。
        """
        self.base_url = base_url.rstrip("/")
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.pw = None

    async def start(self):
        """初始化 Playwright 浏览器环境。"""
        self.pw = await async_playwright().start()
        # 启动 Chromium 浏览器
        self.browser = await self.pw.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,  # 开启高分屏截图，使 UI 更加精致
        )
        self.page = await self.context.new_page()

    async def stop(self):
        """释放浏览器资源。"""
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

    async def login(self, username: str, password: str) -> bool:
        """执行登录操作。"""
        login_url = f"{self.base_url}/login"
        print(f"🔐 正在尝试登录: {login_url}")

        await self.page.goto(login_url)

        # 填充登录表单
        await self.page.fill('input[name="username"]', username)
        await self.page.fill('input[name="password"]', password)

        # 点击登录
        print("  正在提交登录表单...")
        async with self.page.expect_navigation(wait_until="networkidle"):
            await self.page.click('button[type="submit"]')

        # 验证是否成功跳转（即不再处于登录页）
        current_url = self.page.url.rstrip("/")
        if "/login" not in current_url:
            print("✅ 登录验证成功！")
            return True

        print("❌ 登录失败。正在保存错误快照...")
        await self.page.screenshot(path=str(OUTPUT_DIR / "login_error.png"))
        return False

    async def capture_page(self, name: str, path: str, wait_for_selector: str):
        """
        抓取特定页面的截图。

        Args:
            name: 截图文件的名称（不含后缀）。
            path: 相对路径。
            wait_for_selector: 需要等待出现的选择器。
        """
        target_url = f"{self.base_url}{path}"
        output_path = OUTPUT_DIR / f"{name}.png"
        print(f"📸 正在抓取页面: {name} ({target_url})")

        # 导航到目标页面
        await self.page.goto(target_url, wait_until="networkidle")

        # 等待关键元素加载完成
        try:
            await self.page.wait_for_selector(wait_for_selector, timeout=5000)

            # 如果是 Dashboard，额外等待 ECharts 图表渲染完成
            if name == "dashboard":
                await self.page.wait_for_selector("#revenueChart canvas", timeout=3000)
                await asyncio.sleep(0.5)  # 最后的渲染缓冲
        except Exception:
            print(f"⚠️ 等待元素 '{wait_for_selector}' 超时，将直接尝试截图。")

        # 截图
        await self.page.screenshot(path=str(output_path))
        print(f"🛡️  图片已保存: {output_path.name}")

    async def toggle_theme_and_capture(self):
        """测试主题切换功能并截图。"""
        print("🌈 正在测试主题切换并截图...")
        try:
            # 1. 点击用户头像展开下拉菜单
            await self.page.click("#userProfile")
            await asyncio.sleep(0.5)

            # 2. 点击切换主题（选择第二个主题点 Vercel Light 进行测试）
            theme_dots = await self.page.query_selector_all(".theme-dot")
            if len(theme_dots) > 1:
                # 点击 Light 主题
                await theme_dots[1].click()
                # 等待主题应用动画（base.html 中 transition 为 0.4s）
                await asyncio.sleep(1.2)

                output_path = OUTPUT_DIR / "theme_switch.png"
                await self.page.screenshot(path=str(output_path))
                print(f"🛡️  主题切换截图已保存: {output_path.name}")
            else:
                print("⚠️ 未找到足够的主题选择圆点。")
        except Exception as e:
            print(f"⚠️ 主题切换截图失败: {e}")


async def run_automation():
    """主执行逻辑协调。"""
    # 如果处于开发环境调试，可以将 headless 设为 False
    automation = ScreenshotAutomation(BASE_URL, headless=True)
    try:
        await automation.start()

        # 1. 第一步：登录
        if not await automation.login(ADMIN_USER, ADMIN_PASS):
            return

        # 2. 第二步：循环处理页面任务
        for task in SCREENSHOT_TASKS:
            await automation.capture_page(task["name"], task["path"], task["wait_for"])

        # 3. 第三步：额外处理主题切换预览
        await automation.toggle_theme_and_capture()

        print("\n✨ 所有自动化截图任务已顺利完成！")

    except Exception as e:
        print(f"🔥 运行过程中出现致命异常: {e}")
    finally:
        await automation.stop()


if __name__ == "__main__":
    asyncio.run(run_automation())
