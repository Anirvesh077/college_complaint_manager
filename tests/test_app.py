import sys
import unittest
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class ComplaintManagerTests(unittest.TestCase):
    def test_complaint_round_trip(self):
        row = {
            "complaint_id": "CF-0001", "student_name": "Asha", "student_id": "S1",
            "department": "CSE", "category": "Facilities", "title": "Fan broken",
            "description": "Fan is not working", "priority": "Medium", "status": "Open",
            "created_on": "2026-01-01", "due_on": "2026-01-08",
            "updated_on": "2026-01-01T10:00:00", "resolution_note": ""
        }
        complaint = app.Complaint.from_dict(row)
        self.assertEqual(complaint.complaint_id, "CF-0001")
        self.assertEqual(app.asdict(complaint)["title"], "Fan broken")

    def test_next_id_skips_existing(self):
        c = app.Complaint("CF-0001", "A", "1", "CSE", "Other", "T", "D",
                          "Low", "Open", "2026-01-01", "2026-01-02", "2026-01-01")
        self.assertEqual(app.next_id([c]), "CF-0002")

    def test_category_choices_unique(self):
        self.assertEqual(len(app.CATEGORIES), len(set(app.CATEGORIES)))


if __name__ == "__main__":
    unittest.main()
