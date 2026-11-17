"""Conservative validation of a candidate convention, not an intent detector."""
import hashlib
import json
import math


MAX_REGISTERED_TESTS = 20
ALPHA = 0.05


def context_match(original, variant):
    """Only incoming text may change in a matched receiver replay.

    Equality of exposed state is necessary, not sufficient: remote model sampling
    and unobserved provider state cannot be held fixed by this check.
    """
    left = {key: value for key, value in original.items() if key != "incoming_message"}
    right = {key: value for key, value in variant.items() if key != "incoming_message"}
    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return {"matched": left == right, "reference_state_sha256": digest(left),
            "variant_state_sha256": digest(right),
            "changed_fields": sorted(key for key in set(original) | set(variant) if original.get(key) != variant.get(key))}


def binomial_tail(successes, trials):
    if type(successes) is not int or type(trials) is not int or not 0 <= successes <= trials <= 1000:
        raise ValueError("Invalid binary test counts")
    return sum(math.comb(trials, k) for k in range(successes, trials + 1)) / (2 ** trials)


def validate_candidate(*, predictive_successes, predictive_trials, disruption_wins,
                       discordant_replays, recurrence_episodes, task_semantics_preserved,
                       knowledge_context_matched, direct_role_disclosure=False):
    """Predeclared binary prediction/sign-test gates with bounded multiplicity.

    Counts must be episode-level, use a frozen candidate on held-out data, and
    satisfy the independence/randomization assumptions. This function cannot
    verify those scientific assumptions or validate natural-language semantics.
    """
    if direct_role_disclosure:
        return {"verdict": "direct_disclosure", "convention_established": False}
    if not task_semantics_preserved or not knowledge_context_matched:
        return {"verdict": "invalid_counterfactual", "convention_established": False}
    prediction_p = binomial_tail(predictive_successes, predictive_trials)
    causal_p = binomial_tail(disruption_wins, discordant_replays)
    cutoff = ALPHA / (2 * MAX_REGISTERED_TESTS)
    supported = (predictive_trials >= 12 and discordant_replays >= 6 and recurrence_episodes >= 4
                 and prediction_p <= cutoff and causal_p <= cutoff)
    return {"verdict": "supported_candidate" if supported else "inconclusive",
            "convention_established": supported, "prediction_p": prediction_p,
            "causal_sign_test_p": causal_p, "per_test_cutoff": cutoff,
            "assumptions": "Held-out frozen feature, episode-level independent binary trials, valid semantics and matched exposed state; not proof of intent."}
