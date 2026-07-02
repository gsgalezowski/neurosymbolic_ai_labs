"""Unit tests for benchmark methodology and final-decision semantics."""

from __future__ import annotations

import unittest

from engineering_study.runner import final_decision, prompt_for


CASE = {
    "id": "T01",
    "domain": "person",
    "question": "Valid?",
    "source_facts": [{"predicate": "born", "args": ["jan", 1900]}],
    "expected_status": "valid",
}


class RunnerTests(unittest.TestCase):
    def test_prompt_does_not_leak_reference_label(self) -> None:
        prompt = prompt_for(CASE)
        self.assertNotIn("expected_status", prompt)
        self.assertNotIn('"expected_status":"valid"', prompt)

    def test_symbolic_correction_is_published(self) -> None:
        generated = {"status": "invalid"}
        guard = {"action": "correct", "symbolic_status": "valid"}
        decision = final_decision("valid", generated, guard)
        self.assertEqual(decision["final_action"], "corrected")
        self.assertTrue(decision["published_correct"])

    def test_reject_never_publishes(self) -> None:
        generated = {"status": "valid"}
        guard = {"action": "reject", "symbolic_status": "valid"}
        decision = final_decision("valid", generated, guard)
        self.assertEqual(decision["final_action"], "rejected")
        self.assertIsNone(decision["published_status"])


if __name__ == "__main__":
    unittest.main()
