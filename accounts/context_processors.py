from .models import UserProfile

def theme_processor(request):
    """自适应主题上下文处理器，将用户的持久化主题设置传递给模板。"""
    if request.user.is_authenticated:
        try:
            # 尝试获取 profile，如果不存在则自动创建（防御性编程）
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            return {'user_theme': profile.theme}
        except Exception:
            # 数据库尚未就绪或其它异常时回退到暗色
            return {'user_theme': 'dark'}
    return {'user_theme': 'dark'}
