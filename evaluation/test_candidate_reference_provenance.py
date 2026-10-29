import unittest

from . import evaluation


class CandidateReferenceProvenanceTests(unittest.TestCase):
    def test_exact_gold_patch_is_rejected(self):
        instance = {"patch": "diff --git a/a b/a\n+gold\n", "pred_patch": "diff --git a/a b/a\n+gold\n"}
        with self.assertRaisesRegex(evaluation.CandidateProvenanceError, "byte-identical"):
            evaluation.validate_candidate_provenance(instance)

    def test_crlf_only_transport_match_is_rejected(self):
        instance = {"patch": "diff --git a/a b/a\n+gold\n", "pred_patch": "diff --git a/a b/a\r\n+gold\r\n"}
        with self.assertRaisesRegex(evaluation.CandidateProvenanceError, "CRLF-to-LF") as ctx:
            evaluation.validate_candidate_provenance(instance)
        self.assertTrue(ctx.exception.provenance["candidate_equals_gold_after_crlf_normalization"])

    def test_independent_candidate_is_accepted_with_hashes(self):
        instance = {"patch": "diff --git a/a b/a\n+gold\n", "pred_patch": "diff --git a/a b/a\n+candidate\n"}
        result = evaluation.validate_candidate_provenance(instance)
        self.assertFalse(result["candidate_equals_gold"])
        self.assertNotEqual(result["candidate_patch_sha256"], result["gold_patch_sha256"])


if __name__ == "__main__":
    unittest.main()