from __future__ import annotations

from rest_framework import serializers

from .models import Choice, Question


class ChoiceSerializer(serializers.ModelSerializer):
    """Public choice representation without score details."""

    text = serializers.CharField(label="Choice text", help_text="Displayed answer choice text.")

    class Meta:
        model = Choice
        fields = ("id", "text")


class QuestionSerializer(serializers.ModelSerializer):
    """Question payload used by the user-facing test API."""

    choices = ChoiceSerializer(many=True, read_only=True)
    text = serializers.CharField(label="Question text", help_text="Question text shown to the user.")
    skill_category = serializers.CharField(
        label="Skill category",
        help_text="Category used to group questions in the aptitude test.",
    )

    class Meta:
        model = Question
        fields = ("id", "text", "skill_category", "choices")


class AnswerItemSerializer(serializers.Serializer):
    """One submitted answer entry for a question."""

    question_id = serializers.IntegerField(
        min_value=1,
        label="Question ID",
        help_text="ID of the question being answered.",
    )
    choice_id = serializers.IntegerField(
        min_value=1,
        label="Choice ID",
        help_text="ID of the chosen answer option.",
    )


class TestSubmitSerializer(serializers.Serializer):
    """Write-only serializer used to submit completed test answers."""

    answers = AnswerItemSerializer(
        many=True,
        write_only=True,
        label="Answers",
        help_text="List of answers provided by the user.",
    )

    def validate_answers(self, value: list[dict[str, int]]) -> list[dict[str, object]]:
        if not value:
            raise serializers.ValidationError("At least one answer is required.")

        question_ids = [item["question_id"] for item in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("Each question can only be answered once.")

        active_questions = Question.objects.filter(id__in=question_ids, is_active=True)
        questions_map = {question.id: question for question in active_questions}
        if len(questions_map) != len(question_ids):
            raise serializers.ValidationError("One or more questions are invalid or inactive.")

        choice_ids = [item["choice_id"] for item in value]
        choices_map = {
            choice.id: choice
            for choice in Choice.objects.filter(id__in=choice_ids).select_related("question")
        }
        if len(choices_map) != len(choice_ids):
            raise serializers.ValidationError("One or more choices are invalid.")

        validated_answers = []
        for item in value:
            question = questions_map[item["question_id"]]
            choice = choices_map[item["choice_id"]]
            if choice.question_id != question.id:
                raise serializers.ValidationError(
                    "Selected choice does not belong to the provided question."
                )
            validated_answers.append({"question": question, "choice": choice})

        return validated_answers


class TestSubmitResponseSerializer(serializers.Serializer):
    """Response returned after test submission."""

    attempt_id = serializers.IntegerField(label="Attempt ID", help_text="Created test attempt identifier.")
    total_score = serializers.IntegerField(label="Total score", help_text="Calculated score for the submitted answers.")


