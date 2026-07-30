"""Reproducible flagship demonstrations for the iQuant4 developer alpha."""

from .dashboard import (
    ShowcaseDashboardResult,
    build_showcase_dashboard,
    open_showcase_dashboard,
    showcase_dashboard_payload,
)
from .lossy_cat import (
    LossyCatConfiguration,
    LossyCatRow,
    LossyCatShowcaseResult,
    run_lossy_cat_showcase,
)
from .receiver_family import (
    ReceiverFamilyShowcaseResult,
    run_receiver_family_showcase,
)
from .runner import run_alpha_showcase
from .tomography import (
    TomographyShowcaseConfiguration,
    TomographyShowcaseResult,
    cvxpy_available,
    run_sign_free_tomography_showcase,
)

__all__ = [
    "LossyCatConfiguration",
    "LossyCatRow",
    "LossyCatShowcaseResult",
    "ReceiverFamilyShowcaseResult",
    "ShowcaseDashboardResult",
    "TomographyShowcaseConfiguration",
    "TomographyShowcaseResult",
    "build_showcase_dashboard",
    "cvxpy_available",
    "open_showcase_dashboard",
    "run_alpha_showcase",
    "run_lossy_cat_showcase",
    "run_receiver_family_showcase",
    "run_sign_free_tomography_showcase",
    "showcase_dashboard_payload",
]
