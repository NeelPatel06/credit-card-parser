

# Create your models here.
from django.db import models

class UploadedFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=10)
    
    def __str__(self):
        return f"{self.file.name} - {self.uploaded_at}"

class ParsedData(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    card_issuer = models.CharField(max_length=100, blank=True)
    card_last_4 = models.CharField(max_length=4, blank=True)
    card_variant = models.CharField(max_length=100, blank=True)
    billing_cycle = models.CharField(max_length=100, blank=True)
    payment_due_date = models.CharField(max_length=100, blank=True)
    total_balance = models.CharField(max_length=100, blank=True)
    transaction_count = models.IntegerField(default=0)
    raw_data = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.card_issuer} - {self.card_last_4}"