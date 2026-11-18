from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class DivisionRenameTests(TransactionTestCase):
    def test_rename_preserves_club_and_player_membership(self):
        old_target = [("accounts", "0002_federation_club_clubmembership_and_more")]
        new_target = [("accounts", "0003_rename_federation_division")]
        executor = MigrationExecutor(connection)
        executor.migrate(old_target)
        try:
            apps = executor.loader.project_state(old_target).apps
            old_division = apps.get_model("accounts", "Federation").objects.create(name="Régionale 1")
            club = apps.get_model("accounts", "Club").objects.create(
                name="Club de test", federation=old_division,
            )
            user = apps.get_model("accounts", "User").objects.create(username="migration_test")
            membership = apps.get_model("accounts", "ClubMembership").objects.create(
                user=user, club=club, role="player",
            )
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
        apps = executor.loader.project_state(new_target).apps
        renamed_club = apps.get_model("accounts", "Club").objects.get(pk=club.pk)
        self.assertEqual(renamed_club.division_id, old_division.pk)
        self.assertEqual(renamed_club.division.name, "Régionale 1")
        saved_membership = apps.get_model("accounts", "ClubMembership").objects.get(pk=membership.pk)
        self.assertEqual(saved_membership.club_id, club.pk)
        self.assertEqual(saved_membership.user_id, user.pk)
