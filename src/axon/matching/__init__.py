"""Sample matching module for case-control studies."""

from axon.matching.matcher import SampleMatcher, MatchResult, CandidateSample
from axon.matching.statistics import StatisticalReport, run_balance_tests
from axon.matching.service import MatchingService, MatchingCriteria, format_match_result_for_agent
from axon.matching.candidates import find_case_candidates, find_control_candidates

__all__ = [
    "SampleMatcher",
    "MatchResult", 
    "CandidateSample",
    "StatisticalReport",
    "run_balance_tests",
    "MatchingService",
    "MatchingCriteria",
    "format_match_result_for_agent",
    "find_case_candidates",
    "find_control_candidates",
]

