from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ManagerRequest(models.Model):
	STATUS_CHOICES = [
		('pending', 'На розгляді'),
		('approved', 'Схвалено'),
		('rejected', 'Відхилено'),
		('blocked', 'Заблоковано'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manager_requests')
	full_name = models.CharField(max_length=120)
	phone = models.CharField(max_length=50)
	motivation = models.TextField()
	resume = models.FileField(upload_to='manager_resumes/', null=True, blank=True)
	status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
	admin_comment = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	reviewed_at = models.DateTimeField(null=True, blank=True)
	reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_manager_requests')

	def __str__(self):
		return f"Manager request {self.user.username} ({self.get_status_display()})"
