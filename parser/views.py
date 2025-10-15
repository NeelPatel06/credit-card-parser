
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import UploadedFile, ParsedData
from .utils import parse_pdf, parse_csv, parse_json
import os

def home(request):
    return render(request, 'home.html')

def upload_files(request):
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        
        if not files:
            return JsonResponse({'error': 'No files uploaded'}, status=400)
        
        batch_id = None
        processed_count = 0
        
        for file in files:
            file_ext = os.path.splitext(file.name)[1].lower()
            
            uploaded_file = UploadedFile.objects.create(
                file=file,
                file_type=file_ext[1:]
            )
            
            if batch_id is None:
                batch_id = uploaded_file.id
            
            try:
                if file_ext == '.pdf':
                    data = parse_pdf(uploaded_file.file.path)
                elif file_ext == '.csv':
                    data = parse_csv(uploaded_file.file.path)
                elif file_ext == '.json':
                    data = parse_json(uploaded_file.file.path)
                else:
                    continue
                
                ParsedData.objects.create(
                    uploaded_file=uploaded_file,
                    card_issuer=data.get('card_issuer', ''),
                    card_last_4=data.get('card_last_4', ''),
                    card_variant=data.get('card_variant', ''),
                    billing_cycle=data.get('billing_cycle', ''),
                    payment_due_date=data.get('payment_due_date', ''),
                    total_balance=data.get('total_balance', ''),
                    transaction_count=data.get('transaction_count', 0),
                    raw_data=data
                )
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {file.name}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'processed': processed_count,
            'redirect': f'/results/{batch_id}/'
        })
    
    return redirect('home')

def view_results(request, batch_id):
    parsed_data = ParsedData.objects.filter(
        uploaded_file_id__gte=batch_id
    ).select_related('uploaded_file')
    
    return render(request, 'results.html', {
        'parsed_data': parsed_data,
        'total_files': parsed_data.count()
    })