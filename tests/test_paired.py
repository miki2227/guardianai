import json
import unittest
from unittest.mock import patch

from observer import observe
from paired_experiment import case, disclosure, parse_subject, receiver_prompt, sender_prompt


class PairedTests(unittest.TestCase):
    def test_private_information_not_in_receiver_prompt(self):
        episode = case(0)
        prompt = receiver_prompt(episode)
        self.assertNotIn(episode["sender_private"]["internal_reference"], prompt)
        self.assertIn(episode["sender_private"]["internal_reference"], sender_prompt(episode, "Please send a handoff."))

    def test_only_message_is_delivered_not_sender_memory(self):
        episode = case(0)
        response = parse_subject(json.dumps({"message": "Total is 215.", "memory": "ROLE-PRIVATE NOTE"}), "sender")
        prompt = receiver_prompt(episode, delivered=response["message"])
        self.assertNotIn("ROLE-PRIVATE NOTE", prompt)

    def test_invalid_schema_rejected(self):
        with self.assertRaises(ValueError):
            parse_subject('{"message":"hello","memory":"note","extra":"field"}', "sender")

    def test_budget_enforced(self):
        with self.assertRaises(ValueError):
            parse_subject(json.dumps({"message": "word " * 101, "memory": ""}), "sender")

    def test_disclosure_is_exact_and_distinct_from_hallucination(self):
        self.assertEqual(disclosure("a made-up route code", "route-fake-123"), [])
        self.assertEqual(disclosure("Reference route-fake-123", "route-fake-123"), ["literal"])

    def test_observer_is_blinded_to_private_value(self):
        episode = case(0)
        with patch("observer.query_jev", return_value={"model": "jev-1.14.0", "answers": {}}) as query:
            observe(episode["public"], "Handoff")
            self.assertNotIn(episode["sender_private"]["internal_reference"], json.dumps(query.call_args.args[0]))

    def test_observer_outage_abstains(self):
        with patch("observer.query_jev", side_effect=TimeoutError):
            self.assertEqual(observe({}, "handoff")["status"], "abstain")
