from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserDetails(models.Model):
    CALORIE_PLAN_CHOICES = [
        ('cut', 'Похудання'),
        ('maintain', 'Статичний'),
        ('bulk', 'Набір ваги'),
    ]

    ROLE_CHOICES = [
        ('user', 'Користувач'),
        ('manager', 'Менеджер'),
        ('admin', 'Адмін'),
    ]

    ACCOUNT_STATUS_CHOICES = [
        ('active', 'Активний'),
        ('inactive', 'Неактивний'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="details"
    )
    sex = models.CharField(max_length=10, choices=[
        ('male', 'Чоловік'),
        ('female', 'Жінка'),
    ])
    age = models.PositiveSmallIntegerField()
    height_cm = models.PositiveSmallIntegerField()
    weight_kg = models.FloatField()
    activity_level = models.IntegerField(choices=[
        (1, 'Sedentary'),
        (2, 'Lightly active'),
        (3, 'Moderately active'),
        (4, 'Very active'),
        (5, 'Extra active'),
    ])
    current_streak = models.PositiveIntegerField(default=0)
    max_streak = models.PositiveIntegerField(default=0)
    date_last_streak_entry = models.DateField(null=True, blank=True)
    goal_calories = models.PositiveIntegerField(default=2000)
    calorie_plan = models.CharField(max_length=10, choices=CALORIE_PLAN_CHOICES, default='maintain')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    account_status = models.CharField(max_length=10, choices=ACCOUNT_STATUS_CHOICES, default='active')
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f"Details of {self.user.username}"
