from django.shortcuts import render

# Create your views here.

def home(request):
    memberships = []
    if request.user.is_authenticated:
        memberships = request.user.club_memberships.filter(is_active=True).select_related(
            "club__division"
        )
    return render(request, "core/home.html", {"memberships": memberships})

