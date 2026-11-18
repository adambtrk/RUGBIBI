from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from .models import Club, ClubMembership, Division, User
from .permissions import can_access_club, can_manage_club


class ClubAccessTests(TestCase):
    def setUp(self):
        division = Division.objects.create(name="Régionale 1")
        self.club = Club.objects.create(name="Club A", division=division)
        self.other_club = Club.objects.create(name="Club B", division=division)
        self.user = User.objects.create_user(username="joueur_test")
        self.membership = ClubMembership.objects.create(user=self.user, club=self.club)

    def test_player_can_only_access_their_club(self):
        self.assertTrue(can_access_club(self.user, self.club))
        self.assertFalse(can_access_club(self.user, self.other_club))
        self.assertFalse(can_manage_club(self.user, self.club))

    def test_coach_role_is_scoped_to_a_club(self):
        ClubMembership.objects.create(
            user=self.user, club=self.other_club, role=ClubMembership.Role.COACH,
        )
        self.assertTrue(can_manage_club(self.user, self.other_club))
        self.assertFalse(can_manage_club(self.user, self.club))

    def test_inactive_membership_denies_access(self):
        self.membership.is_active = False
        self.membership.save()
        self.assertFalse(can_access_club(self.user, self.club))
        self.assertFalse(can_manage_club(self.user, self.club))

    def test_anonymous_and_inactive_users_are_denied(self):
        self.assertFalse(can_access_club(AnonymousUser(), self.club))
        self.assertFalse(can_manage_club(AnonymousUser(), self.club))
        self.user.is_active = False
        self.user.is_superuser = True
        self.assertFalse(can_access_club(self.user, self.club))
        self.assertFalse(can_manage_club(self.user, self.club))

    def test_staff_does_not_grant_club_management(self):
        self.user.is_staff = True
        self.assertFalse(can_manage_club(self.user, self.club))
        self.assertFalse(can_access_club(self.user, self.other_club))

    def test_active_superuser_can_manage_all_clubs(self):
        self.user.is_superuser = True
        self.assertTrue(can_access_club(self.user, self.other_club))
        self.assertTrue(can_manage_club(self.user, self.other_club))

    def test_duplicate_membership_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClubMembership.objects.create(user=self.user, club=self.club)

    def test_unknown_role_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ClubMembership.objects.create(
                user=self.user, club=self.other_club,role="admin")

    def test_division_with_clubs_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.club.division.delete()

    def test_home_only_displays_own_active_memberships(self):
        other_user = User.objects.create_user(username="autre_test")
        ClubMembership.objects.create(user=other_user, club=self.other_club)
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertContains(response, "Club A")
        self.assertNotContains(response, "Club B")
        self.membership.is_active = False
        self.membership.save()
        response = self.client.get("/")
        self.assertNotContains(response, "Club A")
        self.assertContains(response, "Aucun club associé")

    def test_anonymous_home_does_not_disclose_clubs(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Club A")
