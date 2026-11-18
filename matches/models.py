from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Match(models.Model):
    title = models.CharField("titre du match", max_length=200)
    played_on = models.DateField("date du match")

    video = models.FileField(
        "vidéo MP4",
        upload_to="matches/%Y/%m/",
        validators=[FileExtensionValidator(allowed_extensions=["mp4"])],
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_matches",
        verbose_name="importé par",
    )

    created_at = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        ordering = ["-played_on", "-created_at"]
        verbose_name = "match"
        verbose_name_plural = "matchs"

    def __str__(self):
        return self.title