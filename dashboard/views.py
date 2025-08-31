from django.shortcuts import redirect

def dashboard_view(request):
    # Send the homepage to the Funds API (you can change this to /api/ if you prefer)
    return redirect("/api/funds/")
