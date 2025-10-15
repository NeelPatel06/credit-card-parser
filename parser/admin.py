from django.contrib import admin
from .models import UploadedFile, ParsedData

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['file', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']

@admin.register(ParsedData)
class ParsedDataAdmin(admin.ModelAdmin):
    list_display = ['card_issuer', 'card_last_4', 'card_variant', 'payment_due_date', 'total_balance']
    list_filter = ['card_issuer', 'card_variant']
    search_fields = ['card_issuer', 'card_last_4']