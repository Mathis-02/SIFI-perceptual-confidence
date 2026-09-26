import unittest

from core.session_io import sanitize_participant_id


class SessionIoTests(unittest.TestCase):
    def test_participant_id_is_filesystem_safe(self):
        self.assertEqual(sanitize_participant_id(" P 01/alpha "), "P_01_alpha")

    def test_empty_participant_id_is_rejected(self):
        with self.assertRaises(ValueError):
            sanitize_participant_id("  ...  ")


if __name__ == "__main__":
    unittest.main()
