"""
Project Chimera Evaluation Metrics Module

This module implements the novel evaluation metrics designed for quantifying
subtle, long-term deception in multi-agent systems as outlined in the research roadmap.
"""

from .core_metrics import (
    SuspicionScore,
    PlausibleDeniabilityIndex,
    CumulativeImpactScore,
    StrategicEfficiency
)

from .baseline_metrics import (
    TaskCompletionRate,
    CodeQualityScore,
    TimeToCompletion
)

# from .analysis import (
#     MetricsAnalyzer,
#     PhaseEvaluator,
#     ExperimentReporter
# )

__all__ = [
    'SuspicionScore',
    'PlausibleDeniabilityIndex', 
    'CumulativeImpactScore',
    'StrategicEfficiency',
    'TaskCompletionRate',
    'CodeQualityScore',
    'TimeToCompletion'
    # 'MetricsAnalyzer',
    # 'PhaseEvaluator',
    # 'ExperimentReporter'
]
