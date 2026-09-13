import json
import tempfile
import unittest
from pathlib import Path

from tools.workflow_tracker import WorkflowTracker


class WorkflowTrackerTests(unittest.TestCase):
    def test_records_ordered_agent_interactions_in_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "workflow.jsonl"
            tracker = WorkflowTracker(log_path)

            tracker.record("Product Manager", "started", "分析需求")
            tracker.record("Human Reviewer", "approved", "批准 PRD")

            events = [json.loads(line) for line in log_path.read_text().splitlines()]
            self.assertEqual([event["sequence"] for event in events], [1, 2])
            self.assertEqual(events[0]["actor"], "Product Manager")
            self.assertEqual(events[1]["status"], "approved")


if __name__ == "__main__":
    unittest.main()
