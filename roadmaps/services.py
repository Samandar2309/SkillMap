"""AI orqali generatsiya qilingan JSON dars rejasini bazaga saqlovchi xizmat."""

from __future__ import annotations

import math
import logging
from collections.abc import Mapping
from typing import Any

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Phase, Roadmap, Task

User = get_user_model()
logger = logging.getLogger(__name__)


class RoadmapBuilderService:
    """AI dan kelgan JSON ma'lumotni ishonchli tarzda bazaga yozuvchi xizmat.

    Har xil LLM (Gemini, OpenAI) provayderlari qaytarishi mumkin bo'lgan turli xil
    kalit so'zlarni (keys) taniydi va chala ma'lumotlarni mantiqiy to'ldiradi.
    """

    # Turli xil AI kalit so'zlari (Moslashuvchanlik uchun)
    ROADMAP_TITLE_KEYS = ("title", "roadmap_title", "name", "roadmap_name", "reja_nomi")
    ROADMAP_ESTIMATED_MONTH_KEYS = (
        "estimated_months",
        "estimated_duration_months",
        "duration_months",
        "total_months",
    )
    PHASES_KEYS = ("phases", "roadmap_phases", "steps", "milestones", "bosqichlar")
    PHASE_TITLE_KEYS = ("title", "phase_title", "name", "phase_name", "bosqich_nomi")
    PHASE_ORDER_KEYS = ("order", "phase_order", "position", "sequence", "tartib")
    PHASE_TASKS_KEYS = ("tasks", "items", "activities", "lessons", "darslar", "topshiriqlar")
    TASK_TITLE_KEYS = ("title", "task_title", "name", "activity", "mavzu")
    TASK_DESCRIPTION_KEYS = ("description", "details", "objective", "what_to_learn", "izoh")
    TASK_RESOURCE_KEYS = ("resource_link", "resource_url", "url", "link", "reference", "manba")

    # YANGI MAYDONLAR UCHUN:
    TASK_DAY_KEYS = ("day_number", "day", "kun")
    TASK_EXTRA_RESOURCES_KEYS = ("extra_resources", "additional_links", "resources", "qoshimcha_manbalar")

    @staticmethod
    def _get_first(
        payload: Mapping[str, Any], keys: tuple[str, ...], default: Any = None
    ) -> Any:
        """Berilgan kalit so'zlardan birinchi bo'sh bo'lmagan qiymatni qaytaradi."""
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
        return default

    @staticmethod
    def _to_positive_int(value: Any, default: int) -> int:
        """Qiymatni musbat butun songa o'giradi."""
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _to_str(value: Any, default: str = "") -> str:
        """Qiymatni matnga o'giradi va bo'sh joylarni tozalaydi."""
        if value is None:
            return default
        text = str(value).strip()
        return text or default

    def _resolve_estimated_months(
        self, payload: Mapping[str, Any], phases_payload: list[Any]
    ) -> int:
        """Rejaning umumiy necha oy davom etishini hisoblaydi."""
        explicit = self._get_first(payload, self.ROADMAP_ESTIMATED_MONTH_KEYS)
        if explicit is not None:
            return self._to_positive_int(explicit, default=3)

        weeks_total = 0
        for phase_data in phases_payload:
            if isinstance(phase_data, Mapping):
                weeks_total += self._to_positive_int(
                    phase_data.get("duration_weeks"), default=0
                )

        if weeks_total > 0:
            return max(1, math.ceil(weeks_total / 4))

        return 3

    def _normalize_phases(self, raw_phases: Any) -> list[dict[str, Any]]:
        """AI dan kelgan fazalar va topshiriqlarni tartibga soladi."""
        if not isinstance(raw_phases, list):
            raw_phases = []

        normalized: list[dict[str, Any]] = []
        global_day_tracker = 1 # Kunlarni avtomat hisoblash uchun

        for index, raw_phase in enumerate(raw_phases, start=1):
            if not isinstance(raw_phase, Mapping):
                continue

            phase_title = self._to_str(
                self._get_first(raw_phase, self.PHASE_TITLE_KEYS),
                default=f"{index}-bosqich",
            )
            # DB unique constraint bilan to'qnashmaslik uchun order har doim deterministik va unik bo'ladi.
            phase_order = len(normalized) + 1

            raw_tasks = self._get_first(raw_phase, self.PHASE_TASKS_KEYS, default=[])
            if not isinstance(raw_tasks, list):
                raw_tasks = []

            tasks: list[dict[str, Any]] = []
            for task_index, raw_task in enumerate(raw_tasks, start=1):
                if not isinstance(raw_task, Mapping):
                    continue

                # Topshiriqning nechanchi kun ekanligini aniqlash
                task_day = self._to_positive_int(
                    self._get_first(raw_task, self.TASK_DAY_KEYS),
                    default=global_day_tracker
                )
                global_day_tracker = task_day + 1 # Keyingi task uchun kunni bittaga oshiramiz

                task_title = self._to_str(
                    self._get_first(raw_task, self.TASK_TITLE_KEYS),
                    default=f"{task_index}-topshiriq",
                )
                task_description = self._to_str(
                    self._get_first(raw_task, self.TASK_DESCRIPTION_KEYS),
                    default="",
                )
                task_resource = self._to_str(
                    self._get_first(raw_task, self.TASK_RESOURCE_KEYS),
                    default="",
                )

                # Qo'shimcha resurslarni olish (dict yoki list ekanligini tekshiramiz)
                extra_resources = self._get_first(raw_task, self.TASK_EXTRA_RESOURCES_KEYS, default={})
                if not isinstance(extra_resources, (dict, list)):
                    extra_resources = {"info": self._to_str(extra_resources)}

                tasks.append(
                    {
                        "day_number": task_day,
                        "title": task_title,
                        "description": task_description,
                        "resource_link": task_resource,
                        "extra_resources": extra_resources,
                    }
                )

            # Agar bu fazada hech qanday topshiriq topilmasa, default bitta qo'shamiz
            if not tasks:
                tasks.append(
                    {
                        "day_number": global_day_tracker,
                        "title": "O'quv rejasini boshlash",
                        "description": "Ushbu bosqich uchun maqsadlarni aniqlang.",
                        "resource_link": "",
                        "extra_resources": {}
                    }
                )
                global_day_tracker += 1

            normalized.append(
                {
                    "title": phase_title,
                    "order": phase_order,
                    "tasks": tasks,
                }
            )

        # Agar AI umuman hech narsa qaytarmasa, xavfsizlik uchun default reja
        if not normalized:
            normalized = [
                {
                    "title": "Boshlash",
                    "order": 1,
                    "tasks": [
                        {
                            "day_number": 1,
                            "title": "Haftalik reja tuzish",
                            "description": "Maqsadingizni haftalik qadamlarga bo'lib chiqing.",
                            "resource_link": "",
                            "extra_resources": {}
                        }
                    ],
                }
            ]

        return normalized

    @transaction.atomic
    def build_from_json(self, user: User, json_data: dict[str, Any]) -> Roadmap:
        """Yig'ilgan ma'lumotlarni bazaga bitta tranzaksiyada saqlaydi."""

        if not isinstance(json_data, Mapping):
            raise ValueError("json_data lug'at (dictionary) formatida bo'lishi shart.")

        # Concurrency ni oldini olish: Foydalanuvchi akkauntini vaqtinchalik bloklaymiz
        user = User.objects.select_for_update().get(pk=user.pk)

        roadmap_title = self._to_str(
            self._get_first(json_data, self.ROADMAP_TITLE_KEYS),
            default="Shaxsiy AI O'quv Rejasi",
        )
        phases_payload = self._get_first(json_data, self.PHASES_KEYS, default=[])
        normalized_phases = self._normalize_phases(phases_payload)
        estimated_months = self._resolve_estimated_months(json_data, normalized_phases)

        logger.info(
            f"Foydalanuvchi {user.id} uchun reja tuzilmoqda: title={roadmap_title}, "
            f"fazalar={len(normalized_phases)}, oylar={estimated_months}"
        )

        # PRO YONDASHUV: Eski rejalarni o'chirib yubormaymiz, ularni arxivlaymiz (is_active=False)
        archived_count = Roadmap.objects.filter(user=user, is_active=True).update(is_active=False)
        if archived_count > 0:
            logger.info(f"Foydalanuvchi {user.id} ning {archived_count} ta eski rejasi arxivlandi.")

        # Yangi (Aktiv) reja yaratamiz
        roadmap = Roadmap.objects.create(
            user=user,
            title=roadmap_title,
            estimated_months=estimated_months,
            is_active=True,
            is_completed=False,
        )

        # Fazalarni ommaviy saqlash (Bulk Create)
        phase_instances = [
            Phase(
                roadmap=roadmap,
                title=phase_data["title"],
                order=phase_data["order"],
                is_completed=False,
            )
            for phase_data in normalized_phases
        ]
        created_phases = Phase.objects.bulk_create(phase_instances)

        # Bazadan qaytgan fazalar ID siga ishonch hosil qilish (ba'zi MB lar bulk_create da ID qaytarmaydi)
        if not created_phases or any(phase.pk is None for phase in created_phases):
            created_phases = list(
                Phase.objects.filter(roadmap=roadmap).order_by("order", "id")
            )

        # Darslarni/Topshiriqlarni ommaviy saqlash
        tasks_to_create: list[Task] = []
        for phase, phase_data in zip(created_phases, normalized_phases):
            for task_data in phase_data["tasks"]:
                tasks_to_create.append(
                    Task(
                        phase=phase,
                        day_number=task_data["day_number"], # YANGI qo'shildi
                        title=task_data["title"],
                        description=task_data["description"],
                        resource_link=task_data["resource_link"],
                        extra_resources=task_data["extra_resources"], # YANGI qo'shildi
                        is_completed=False,
                    )
                )

        if tasks_to_create:
            Task.objects.bulk_create(tasks_to_create)

        logger.info(
            f"Reja {roadmap.id} muvaffaqiyatli saqlandi! "
            f"({len(created_phases)} faza, {len(tasks_to_create)} kunlik dars)"
        )

        return roadmap