import struct

from django import forms
from django.conf import settings

from .models import Match


def mp4_boxes(file, start, end):
    """Lire les en-têtes ISO BMFF sans charger la vidéo en mémoire."""
    position = start
    while position < end:
        file.seek(position)
        header = file.read(8)
        if len(header) != 8:
            raise ValueError("En-tête incomplet")
        size, kind = struct.unpack(">I4s", header)
        header_size = 8
        if size == 1:
            extended = file.read(8)
            if len(extended) != 8:
                raise ValueError("Taille incomplète")
            size = struct.unpack(">Q", extended)[0]
            header_size = 16
        elif size == 0:
            size = end - position
        if size < header_size or position + size > end:
            raise ValueError("Taille invalide")
        yield kind, position + header_size, position + size
        position += size


def validate_mp4(file):
    """Vérifier le conteneur et une piste vidéo, sans prétendre décoder le codec."""
    try:
        kinds = set()
        video_track = False
        for kind, start, end in mp4_boxes(file, 0, file.size):
            kinds.add(kind)
            if kind == b"moov":
                for child, track_start, track_end in mp4_boxes(file, start, end):
                    if child != b"trak":
                        continue
                    for track_child, media_start, media_end in mp4_boxes(file, track_start, track_end):
                        if track_child != b"mdia":
                            continue
                        for media_child, handler_start, handler_end in mp4_boxes(file, media_start, media_end):
                            if media_child == b"hdlr" and handler_end - handler_start >= 12:
                                file.seek(handler_start + 8)
                                video_track |= file.read(4) == b"vide"
        if not {b"ftyp", b"moov", b"mdat"}.issubset(kinds) or not video_track:
            raise ValueError("Piste vidéo absente")
    except (ValueError, OSError, struct.error):
        raise forms.ValidationError("Ce fichier ne contient pas une structure MP4 vidéo valide.")
    finally:
        file.seek(0)


class MatchUploadForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["title", "played_on", "video"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Ex. : Rugby Club A — Rugby Club B"}),
            "played_on": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "video": forms.FileInput(attrs={"accept": ".mp4,video/mp4"}),
        }

    def clean_video(self):
        video = self.cleaned_data["video"]
        limit = getattr(settings, "MAX_VIDEO_UPLOAD_BYTES", 8 * 1024**3)
        if video.size > limit:
            raise forms.ValidationError("La vidéo dépasse la limite de 8 Go par fichier.")
        validate_mp4(video)
        return video
