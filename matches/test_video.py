"""Les petits conteneurs ci-dessous sont des fixtures structurelles, pas des vidéos lisibles."""
import shutil
import struct
import tempfile
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from .models import Match


def box(kind, data):
    return struct.pack(">I4s", len(data) + 8, kind) + data


def mp4_fixture(handler=b"vide"):
    return (
        box(b"ftyp", b"isom" + b"\x00" * 4 + b"isommp42")
        + box(b"moov", box(b"trak", box(b"mdia", box(b"hdlr", b"\x00" * 8 + handler))))
        + box(b"mdat", b"test-data-only")
    )


class VideoTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_directory = tempfile.mkdtemp()
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media_directory)
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        shutil.rmtree(cls.media_directory)
        super().tearDownClass()

    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.other = User.objects.create_user(username="other")
        self.data = mp4_fixture()
        self.match = Match.objects.create(
            title="Match test", played_on=date(2026, 11, 1), uploaded_by=self.owner,
            video=SimpleUploadedFile("match.mp4", self.data, content_type="video/mp4"),
        )
        self.video_url = reverse("matches:video", args=[self.match.pk])
        self.detail_url = reverse("matches:detail", args=[self.match.pk])
        self.list_url = reverse("matches:list")
        self.client.force_login(self.owner)

    def upload(self, content, filename="new.mp4"):
        return self.client.post(self.list_url, {
            "title": "Nouveau match", "played_on": "2026-11-02",
            "video": SimpleUploadedFile(filename, content),
        })

    def test_upload_records_owner_and_redirects_to_player(self):
        response = self.upload(self.data)
        match = Match.objects.get(title="Nouveau match")
        self.assertEqual(match.uploaded_by, self.owner)
        self.assertRedirects(response, reverse("matches:detail", args=[match.pk]))
        with match.video.open("rb") as saved:
            self.assertEqual(saved.read(), self.data)

    def test_invalid_container_and_audio_only_are_rejected(self):
        for content in [b"fake mp4", self.data[:-2], mp4_fixture(b"soun")]:
            response = self.upload(content)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "structure MP4")
        self.assertEqual(Match.objects.count(), 1)

    def test_wrong_extension_is_rejected(self):
        self.assertEqual(self.upload(self.data, "new.txt").status_code, 200)
        self.assertEqual(Match.objects.count(), 1)

    @override_settings(MAX_VIDEO_UPLOAD_BYTES=1)
    def test_upload_size_limit(self):
        response = self.upload(self.data)
        self.assertContains(response, "dépasse la limite")
        self.assertEqual(Match.objects.count(), 1)

    def test_anonymous_access_requires_login(self):
        self.client.logout()
        for url in [self.list_url, self.detail_url, self.video_url]:
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_other_user_cannot_list_view_or_stream_match(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.list_url), "Match test")
        self.assertEqual(self.client.get(self.detail_url).status_code, 404)
        self.assertEqual(self.client.get(self.video_url, HTTP_RANGE="bytes=0-10").status_code, 404)

    def test_superuser_can_access_video(self):
        self.other.is_superuser = True
        self.other.save()
        self.client.force_login(self.other)
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), self.data)

    def test_full_video_is_private(self):
        response = self.client.get(self.video_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertEqual(b"".join(response.streaming_content), self.data)

    def test_video_seeking_ranges(self):
        for header, start, end in [
            ("bytes=5-15", 5, 15), ("bytes=20-", 20, len(self.data)-1),
            ("bytes=-10", len(self.data)-10, len(self.data)-1),
            ("bytes=5-999999", 5, len(self.data)-1),
        ]:
            with self.subTest(header=header):
                response = self.client.get(self.video_url, HTTP_RANGE=header)
                self.assertEqual(response.status_code, 206)
                self.assertEqual(response["Content-Range"], f"bytes {start}-{end}/{len(self.data)}")
                self.assertEqual(int(response["Content-Length"]), end-start+1)
                self.assertEqual(b"".join(response.streaming_content), self.data[start:end+1])

    def test_invalid_ranges(self):
        for header in ["bytes=99999-", "bytes=10-5", "bytes=-0", "bytes=-", "bytes=0-1,5-6", "invalid"]:
            with self.subTest(header=header):
                response = self.client.get(self.video_url, HTTP_RANGE=header)
                self.assertEqual(response.status_code, 416)
                self.assertEqual(response["Content-Range"], f"bytes */{len(self.data)}")

    def test_head_returns_metadata_only(self):
        response = self.client.head(self.video_url, HTTP_RANGE="bytes=0-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response["Content-Length"]), len(self.data))
        self.assertEqual(response.content, b"")

    def test_missing_video_returns_404(self):
        self.match.video.storage.delete(self.match.video.name)
        self.assertEqual(self.client.get(self.video_url).status_code, 404)

    def test_player_uses_protected_url(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, self.video_url)
        self.assertNotContains(response, self.match.video.name)

    def test_no_public_media_route(self):
        self.assertEqual(self.client.get("/media/" + self.match.video.name).status_code, 404)
