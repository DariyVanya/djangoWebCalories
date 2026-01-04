from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserDetails(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="details"
    )
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

    def __str__(self):
        return f"Details of {self.user.username}"
