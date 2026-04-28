from django.contrib import admin

from .models import Phase, Roadmap, Task


# ==========================================
# 1. INLINES (Bog'liq ma'lumotlarni bitta oynada ko'rish)
# ==========================================

class TaskInline(admin.TabularInline):
    """Faza (Modul) ichiga kirganda uning darslarini ko'rsatuvchi oyna."""
    model = Task
    extra = 0  # Bo'sh qatorlar chiqib turmasligi uchun
    fields = ("day_number", "title", "resource_link", "is_completed", "completed_at")
    readonly_fields = ("completed_at",)
    ordering = ("day_number",)


class PhaseInline(admin.TabularInline):
    """Reja (Roadmap) ichiga kirganda uning fazalarini ko'rsatuvchi oyna."""
    model = Phase
    extra = 0
    fields = ("order", "title", "is_completed")
    ordering = ("order",)
    show_change_link = True  # Fazaning ustiga bosib, uning ichiga kirish imkoniyati


# ==========================================
# 2. ROADMAP ADMIN
# ==========================================

@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "title",
        "estimated_months",
        "get_progress",  # @property dan olingan foiz
        "is_active",
        "is_completed",
        "created_at"
    )
    search_fields = ("user__email", "user__username", "title")
    list_filter = ("is_active", "is_completed", "created_at")

    # N+1 muammosini yo'q qilish
    list_select_related = ("user",)

    # Minglab userlar bo'lganda dropdown qotib qolmasligi uchun
    raw_id_fields = ("user",)

    readonly_fields = ("get_progress", "created_at", "updated_at")
    inlines = [PhaseInline]

    # Ommaviy arxivlash funksiyasi
    actions = ["make_archived"]

    fieldsets = (
        ("Foydalanuvchi va Reja nomi", {
            "fields": ("user", "title", "estimated_months")
        }),
        ("Holati va Statistika", {
            "fields": ("is_active", "is_completed", "get_progress")
        }),
        ("Vaqt", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)  # Admin panilda yig'ig'lik (yopiq) turadi
        }),
    )

    @admin.display(description="Progress (%)")
    def get_progress(self, obj):
        # Progressni rangli qilib ko'rsatish (qiziqarli UI uchun)
        progress = obj.progress_percentage
        color = "green" if progress == 100 else "orange" if progress > 50 else "red"
        return admin.utils.format_html(
            '<b style="color: {};">{}%</b>', color, progress
        )

    @admin.action(description="Tanlangan rejalarni arxivlash (Nofaol qilish)")
    def make_archived(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} ta reja arxivlandi.")


# ==========================================
# 3. PHASE ADMIN
# ==========================================

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ("id", "roadmap_short", "order", "title", "is_completed")
    search_fields = ("title", "roadmap__user__email", "roadmap__title")
    list_filter = ("is_completed",)

    list_select_related = ("roadmap", "roadmap__user")
    raw_id_fields = ("roadmap",)

    inlines = [TaskInline]

    @admin.display(description="Tegishli Reja")
    def roadmap_short(self, obj):
        return f"{obj.roadmap.user.username} | {obj.roadmap.title[:20]}..."


# ==========================================
# 4. TASK (KUNLIK DARS) ADMIN
# ==========================================

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "phase_short", "day_number", "title", "is_completed", "completed_at")
    search_fields = ("title", "phase__roadmap__user__email")
    list_filter = ("is_completed", "day_number", "phase__roadmap__is_active")

    # 3 ta jadvalni bitta so'rovda ulab olish (Juda yuqori tezlik)
    list_select_related = ("phase", "phase__roadmap", "phase__roadmap__user")
    raw_id_fields = ("phase",)

    readonly_fields = ("completed_at",)

    fieldsets = (
        ("Tegishlilik", {
            "fields": ("phase", "day_number")
        }),
        ("Dars mazmuni", {
            "fields": ("title", "description", "resource_link", "extra_resources")
        }),
        ("Bajarilish holati", {
            "fields": ("is_completed", "completed_at")
        }),
    )

    @admin.display(description="Faza (Modul)")
    def phase_short(self, obj):
        return f"{obj.phase.roadmap.user.username} - {obj.phase.title}"