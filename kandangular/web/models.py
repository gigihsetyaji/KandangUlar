from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
