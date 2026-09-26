import unittest

from core.timing import ms_to_frames


class TimingTests(unittest.TestCase):
    def test_standard_lab_conversions(self):
        frame_period = 1.0 / 60.0
        self.assertEqual(ms_to_frames(17, frame_period), 1)
        self.assertEqual(ms_to_frames(33, frame_period), 2)
        self.assertEqual(ms_to_frames(66, frame_period), 4)

    def test_invalid_frame_period(self):
        with self.assertRaises(ValueError):
            ms_to_frames(17, 0)


if __name__ == "__main__":
    unittest.main()
