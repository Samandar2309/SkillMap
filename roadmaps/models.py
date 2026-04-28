from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.utils import timezone


# ==========================================
# 1. CUSTOM MANAGER (Tezlikni oshirish uchun)
# ==========================================
class RoadmapManager(models.Manager):
    """
    N+1 muammosini avtomatik hal qiluvchi maxsus menejer.
    Bitta so'rovda Roadmap, uning barcha Fazalari va Tasklarini olib keladi.
    """

    def get_active_with_details(self, user):
        return self.filter(user=user, is_active=True).prefetch_related(
            models.Prefetch('phases', queryset=Phase.objects.order_by('order')),
            'phases__tasks'
        ).first()

    def annotate_progress(self):
        """Annotate roadmap queryset with task counters for cheap progress computation."""
        return self.annotate(
            total_tasks_count=Count("phases__tasks"),
            completed_tasks_count=Count("phases__tasks", filter=Q(phases__tasks__is_completed=True)),
        )


# ==========================================
# 2. ROADMAP MODELI
# ==========================================
class Roadmap(models.Model):
    """Foydalanuvchining umumiy yo'l xaritasi."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roadmaps",
        db_index=True  # Qidiruv tezligini oshirish uchun indeks
    )
    title = models.CharField(max_length=255, verbose_name="Reja nomi")
    estimated_months = models.PositiveIntegerField(verbose_name="Kutilayotgan davomiylik (oy)")

    # db_index=True eng ko'p filter qilinadigan maydonlarga qo'yiladi
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Faolmi?")
    is_completed = models.BooleanField(default=False, db_index=True, verbose_name="Tugallanganmi?")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Qachon oxirgi marta o'zgarganini bilish uchun

    objects = RoadmapManager()  # Maxsus menejerni ulash

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Yo'l xaritasi"
        verbose_name_plural = "1. Yo'l xaritalari"

    def __str__(self) -> str:
        return f"{self.user} ning rejasi: {self.title}"

    @property
    def progress_percentage(self) -> int:
        """Roadmap'ning necha foizi bitganini tezkor hisoblash"""
        total_tasks = getattr(self, "total_tasks_count", None)
        completed_tasks = getattr(self, "completed_tasks_count", None)

        if total_tasks is None or completed_tasks is None:
            total_tasks = Task.objects.filter(phase__roadmap=self).count()
            completed_tasks = Task.objects.filter(phase__roadmap=self, is_completed=True).count()

        if total_tasks == 0:
            return 0
        return int((completed_tasks / total_tasks) * 100)


# ==========================================
# 3. PHASE (MODUL/BOSQICH) MODELI
# ==========================================
class Phase(models.Model):
    """Reja ichidagi alohida modullar (Masalan: Python Asoslari, Django)"""

    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name="phases",
    )
    title = models.CharField(max_length=255, verbose_name="Modul nomi")
    order = models.PositiveIntegerField(db_index=True, verbose_name="Tartib raqami")
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]
        constraints = [
            # Bitta roadmap ichida 1-bosqich degan narsa 2 marta bo'lishiga yo'l qo'ymaydi
            models.UniqueConstraint(
                fields=["roadmap", "order"],
                name="unique_phase_order_per_roadmap",
            )
        ]
        verbose_name = "Bosqich"
        verbose_name_plural = "2. Bosqichlar"

    def __str__(self) -> str:
        return f"{self.order}-bosqich: {self.title}"


# ==========================================
# 4. TASK (KUNLIK VAZIFA) MODELI
# ==========================================
class Task(models.Model):
    """Har bir kunga mo'ljallangan aniq dars va topshiriqlar"""

    phase = models.ForeignKey(
        Phase,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    day_number = models.PositiveIntegerField(default=1, db_index=True, verbose_name="Nechanchi kun")

    title = models.CharField(max_length=255, verbose_name="Dars mavzusi")
    description = models.TextField(blank=True, verbose_name="Dars izohi")
    resource_link = models.URLField(blank=True, verbose_name="Asosiy manba")

    # JSONField orqali xohlagancha qo'shimcha resurslarni strukturali saqlash mumkin
    extra_resources = models.JSONField(
        default=dict,
        blank=True,
        help_text="Qo'shimcha havolalar (YouTube, GitHub, vs)"
    )

    is_completed = models.BooleanField(default=False, db_index=True, verbose_name="Bajarildimi?")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Bajarilgan vaqti")

    class Meta:
        ordering = ["day_number", "id"]
        verbose_name = "Topshiriq"
        verbose_name_plural = "3. Topshiriqlar"

    def __str__(self) -> str:
        return f"Day {self.day_number}: {self.title}"

    def mark_as_done(self):
        """Topshiriqni bajarildi deb belgilovchi maxsus metod"""
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save(update_fields=['is_completed', 'completed_at'])

            phase = self.phase
            if not phase.tasks.filter(is_completed=False).exists() and not phase.is_completed:
                phase.is_completed = True
                phase.save(update_fields=["is_completed"])

            roadmap = phase.roadmap
            if not Task.objects.filter(phase__roadmap=roadmap, is_completed=False).exists():
                update_fields: list[str] = []
                if not roadmap.is_completed:
                    roadmap.is_completed = True
                    update_fields.append("is_completed")
                if roadmap.is_active:
                    roadmap.is_active = False
                    update_fields.append("is_active")
                if update_fields:
                    roadmap.save(update_fields=update_fields)
