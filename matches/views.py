import re

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import MatchUploadForm
from .models import Match


def accessible_matches(user):
    if user.is_superuser:
        return Match.objects.all()
    return Match.objects.filter(uploaded_by=user)


@login_required
@require_http_methods(["GET", "POST"])
def match_list(request):
    form = MatchUploadForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        match = form.save(commit=False)
        match.uploaded_by = request.user
        match.save()
        return redirect("matches:detail", pk=match.pk)
    return render(request, "matches/list.html", {
        "form": form, "matches": accessible_matches(request.user),
    })


@login_required
def match_detail(request, pk):
    match = get_object_or_404(accessible_matches(request.user), pk=pk)
    return render(request, "matches/detail.html", {"match": match})


class FileSlice:
    """Lecture bornée ; Django ferme aussi le fichier si le client se déconnecte."""
    def __init__(self, file, start, length):
        self.file = file
        self.file.seek(start)
        self.remaining = length

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining <= 0:
            raise StopIteration
        data = self.file.read(min(64 * 1024, self.remaining))
        if not data:
            raise StopIteration
        self.remaining -= len(data)
        return data

    def close(self):
        self.file.close()


@login_required
@require_http_methods(["GET", "HEAD"])
def match_video(request, pk):
    match = get_object_or_404(accessible_matches(request.user), pk=pk)
    try:
        file = match.video.storage.open(match.video.name, "rb")
        size = file.size
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("Vidéo indisponible")

    start, end = 0, size - 1
    # HEAD décrit la ressource entière ; Range ne s'applique qu'à GET.
    range_header = request.headers.get("Range") if request.method == "GET" else None
    if range_header:
        found = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header)
        try:
            if not found or not any(found.groups()):
                raise ValueError
            first, last = found.groups()
            if first:
                start = int(first)
                end = min(int(last), size - 1) if last else size - 1
            else:
                suffix = int(last)
                if suffix <= 0:
                    raise ValueError
                start = max(0, size - suffix)
            if start > end or start >= size:
                raise ValueError
        except ValueError:
            file.close()
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            response["Cache-Control"] = "private, no-store"
            return response

    if request.method == "HEAD":
        file.close()
        response = HttpResponse(content_type="video/mp4")
    elif range_header:
        response = StreamingHttpResponse(
            FileSlice(file, start, end - start + 1), status=206, content_type="video/mp4",
        )
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
    else:
        response = FileResponse(file, content_type="video/mp4")
    response["Content-Length"] = str(end - start + 1 if range_header else size)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
