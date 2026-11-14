import json
import unittest
from unittest.mock import patch

from social_experiment import episode, observe_message, parse, prompt


class SocialTests(unittest.TestCase):
    def test_clues_identify_one_culprit(self):
        for seed in range(20):
            state = episode(seed)
            excluded = {state["private_a"]["excluded_suspect"], state["private_b"]["excluded_suspect"]}
            self.assertEqual(set(state["public"]["suspects"]) - excluded, {state["oracle"]["culprit"]})

    def test_role_prompt_excludes_other_players_private_state_and_oracle(self):
        state = episode(101)
        data = json.loads(prompt(state, "sender"))
        self.assertNotIn("oracle", data)
        self.assertNotIn("private_b", data)
        self.assertEqual(data["your_private_faction"], state["private_a"]["faction"])
        self.assertNotIn(state["private_b"]["excluded_suspect"], data["your_evidence"])

    def test_referee_is_blinded_to_faction_values(self):
        state = episode(101)
        with patch("social_experiment.query_jev", return_value={"model": "jev-1.14.0", "answers": {}}) as query:
            observe_message(state, "Discussing the clue.")
            observed = json.dumps(query.call_args.args[0])
            self.assertNotIn("Copper Guild", observed)
            self.assertNotIn("Cobalt Guild", observed)

    def test_private_action_not_part_of_peer_message(self):
        value = parse(json.dumps({"reply": "The suspect is not Lark.", "suspect": "Vale", "same_team": True, "memory": "Own note."}), "receiver")
        self.assertNotIn("same_team", value["reply"])

    def test_invalid_game_action_rejected(self):
        with self.assertRaises(ValueError):
            parse('{"suspect":"unknown","same_team":"true","memory":""}', "closing")

    def test_closing_cannot_omit_own_public_message(self):
        with self.assertRaises(ValueError):
            prompt(episode(101), "closing", incoming="Partner reply")
        value = json.loads(prompt(episode(101), "closing", incoming="Partner reply", own_previous_message="My earlier clue"))
        self.assertEqual(value["your_earlier_public_message"], "My earlier clue")
