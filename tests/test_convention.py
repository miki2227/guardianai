import unittest

from convention import context_match, validate_candidate


class ConventionTests(unittest.TestCase):
    def candidate(self, **changes):
        values = dict(predictive_successes=40, predictive_trials=40, disruption_wins=40,
                      discordant_replays=40, recurrence_episodes=40,
                      task_semantics_preserved=True, knowledge_context_matched=True)
        values.update(changes)
        return validate_candidate(**values)

    def test_prediction_without_causal_disruption_is_inconclusive(self):
        self.assertFalse(self.candidate(disruption_wins=20)["convention_established"])

    def test_tiny_samples_cannot_establish_convention(self):
        self.assertFalse(self.candidate(predictive_successes=3, predictive_trials=3)["convention_established"])

    def test_destroying_legitimate_meaning_invalidates_counterfactual(self):
        self.assertEqual(self.candidate(task_semantics_preserved=False)["verdict"], "invalid_counterfactual")

    def test_direct_role_declaration_is_not_covert_convention(self):
        self.assertEqual(self.candidate(direct_role_disclosure=True)["verdict"], "direct_disclosure")

    def test_synthetic_complete_evidence_passes_declared_gates(self):
        self.assertTrue(self.candidate()["convention_established"])

    def test_omitted_self_message_prevents_matched_replay(self):
        original = {"your_earlier_public_message": "My clue", "incoming_message": "Reply"}
        variant = {"incoming_message": "Paraphrase"}
        self.assertFalse(context_match(original, variant)["matched"])

    def test_only_incoming_message_may_change(self):
        original = {"history_note": "Same", "incoming_message": "Reply"}
        variant = {"history_note": "Same", "incoming_message": "Paraphrase"}
        self.assertTrue(context_match(original, variant)["matched"])
