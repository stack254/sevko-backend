from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_INITIALIZE_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"

@csrf_exempt
def initiate_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email')
            amount = data.get('amount')
            
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "email": email,
                "amount": int(float(amount) * 100),  # Convert to kobo and ensure it's an integer
            }
            
            response = requests.post(PAYSTACK_INITIALIZE_URL, json=payload, headers=headers)
            
            if response.status_code == 200:
                return JsonResponse(response.json())
            return JsonResponse({'error': 'Failed to initiate payment'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def verify_payment(request, reference):
    try:
        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        }
        
        response = requests.get(f"{PAYSTACK_VERIFY_URL}{reference}", headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            return JsonResponse(response_data)
        return JsonResponse({'error': 'Payment verification failed'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)