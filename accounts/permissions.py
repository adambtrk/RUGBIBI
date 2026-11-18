"""Contrôles d'accès à réutiliser dans les futures vues de matchs."""

from .models import ClubMembership


def can_access_club(user, club):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return ClubMembership.objects.filter(user=user, club=club, is_active=True).exists()


def can_manage_club(user, club):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return ClubMembership.objects.filter(
        user=user, club=club, is_active=True, role=ClubMembership.Role.COACH,
    ).exists()
