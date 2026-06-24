import os
import tempfile
import unittest

import database


class TestDatabaseUserLookup(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.original_db_name = database.DB_NAME
        database.DB_NAME = self.temp_db.name
        database.initialize_database()

    def tearDown(self):
        database.DB_NAME = self.original_db_name
        try:
            os.remove(self.temp_db.name)
        except OSError:
            pass

    def test_get_user_by_username_returns_user(self):
        result = database.create_user("testuser", "test@example.com", "Password123!")
        self.assertIs(result, True)

        user = database.get_user_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        self.assertTrue(database.verify_password("Password123!", user["password_hash"]))

    def test_get_user_by_username_returns_none_for_unknown_username(self):
        self.assertIsNone(database.get_user_by_username("missing"))

    def test_get_user_by_username_returns_none_for_blank_username(self):
        self.assertIsNone(database.get_user_by_username("  "))


if __name__ == "__main__":
    unittest.main()
