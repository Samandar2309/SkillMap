from __future__ import annotations

from django.conf import settings
from django.db import models


class Roadmap(models.Model):
	"""Top-level generated roadmap bound to exactly one user."""

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="roadmap",
	)
	title = models.CharField(max_length=255)
	estimated_months = models.PositiveIntegerField()
	is_completed = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return f"Roadmap #{self.pk} for {self.user}"


class Phase(models.Model):
	"""A roadmap phase with ordered progression."""

	roadmap = models.ForeignKey(
		Roadmap,
		on_delete=models.CASCADE,
		related_name="phases",
	)
	title = models.CharField(max_length=255)
	order = models.PositiveIntegerField()
	is_completed = models.BooleanField(default=False)

	class Meta:
		ordering = ["order"]
		constraints = [
			models.UniqueConstraint(
				fields=["roadmap", "order"],
				name="unique_phase_order_per_roadmap",
			)
		]

	def __str__(self) -> str:
		return f"Phase {self.order}: {self.title}"


class Task(models.Model):
	"""Atomic actionable task inside a phase."""

	phase = models.ForeignKey(
		Phase,
		on_delete=models.CASCADE,
		related_name="tasks",
	)
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	resource_link = models.URLField(blank=True)
	is_completed = models.BooleanField(default=False)

	class Meta:
		ordering = ["id"]

	def __str__(self) -> str:
		return f"Task #{self.pk}: {self.title}"
