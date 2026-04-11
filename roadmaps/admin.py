from django.contrib import admin

from .models import Phase, Roadmap, Task


class PhaseInline(admin.TabularInline):
	model = Phase
	extra = 1


class TaskInline(admin.TabularInline):
	model = Task
	extra = 1


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "title", "estimated_months", "is_completed", "created_at")
	search_fields = ("user__email", "title")
	list_filter = ("is_completed", "created_at")
	inlines = [PhaseInline]


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
	list_display = ("id", "roadmap", "title", "order", "is_completed")
	search_fields = ("title", "roadmap__user__email")
	list_filter = ("is_completed",)
	inlines = [TaskInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ("id", "phase", "title", "is_completed")
	search_fields = ("title", "phase__roadmap__user__email")
	list_filter = ("is_completed",)
