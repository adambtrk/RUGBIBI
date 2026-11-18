from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class User(AbstractUser):
    """Compte user de RUGBIBI"""


class Division(models.Model):
    name = models.CharField("nom", max_length=150, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "division"

    def __str__(self):
        return self.name


class Club(models.Model):
    name = models.CharField("nom", max_length=150)
    division = models.ForeignKey(
        Division, on_delete=models.PROTECT, related_name="clubs",
        verbose_name="division",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "division"], name="unique_club_per_division"
            ),
        ]

    def __str__(self):
        return self.name


class ClubMembership(models.Model):
    class Role(models.TextChoices):
        PLAYER = "player", "Joueur"
        COACH = "coach", "Entraîneur / Analyste"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="club_memberships", verbose_name="utilisateur",
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField("rôle", max_length=10, choices=Role.choices, default=Role.PLAYER)
    is_active = models.BooleanField("adhésion active", default=True)

    class Meta:
        ordering = ["club__name", "user__username"]
        verbose_name = "adhésion au club"
        verbose_name_plural = "adhésions aux clubs"
        constraints = [
            models.UniqueConstraint(fields=["user", "club"], name="unique_user_club"),
            models.CheckConstraint(
                condition=models.Q(role__in=["player", "coach"]),
                name="valid_club_role",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.club} ({self.get_role_display()})"


