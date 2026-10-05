# report.py
import os
import django

# مطمئن شو که این نام دقیقاً همان پوشه‌ای است که settings.py در آن است
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shine_star_project.settings')
django.setup()

from django.apps import apps

print("=== SHINE STAR PROJECT REPORT ===\n")

# گرفتن لیست تمام اپلیکیشن‌های فعال در پروژه
all_apps = apps.get_app_configs()

for app_config in all_apps:
    # ما می‌خواهیم اپلیکیشن‌های خودمان را ببینیم، نه اپلیکیشن‌های داخلی جنگو (مثل admin, auth)
    # پس چک می‌کنیم که اپلیکیشن جزو اپ‌های پیش‌فرض جنگو نباشد
    if not app_config.name.startswith('django.contrib'):
        
        # همچنین می‌خواهیم پوشه تنظیمات اصلی (project core) را هم نبینیم که خروجی تمیز باشد
        if app_config.name != 'shine_star_project':
            
            print(f"📦 App: {app_config.name}")
            models = app_config.get_models()
            
            if not models:
                print("  └── ⚠️ No models found in this app.")
            
            for model in models:
                print(f"  └── 🔹 Model: {model.__name__}")
                for field in model._meta.get_fields():
                    # نمایش فیلدها (بدون فیلدهای سیستمی مثل id یا رابطه با مدل‌های دیگر برای خلوت شدن)
                    if not field.is_relation and not field.auto_created:
                        print(f"      ├── field: {field.name} ({field.get_internal_type()})")
            print("-" * 30)

print("\n✅ Report Completed.")
