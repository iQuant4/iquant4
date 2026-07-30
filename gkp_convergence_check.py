from __future__ import annotations

import numpy as np

from quantum_states import approximate_gkp_state


def pure_state_overlap_fidelity(
    state_a: np.ndarray,
    state_b: np.ndarray,
) -> float:
    """
    Return |<a|b>|^2 after normalizing both states.
    """
    state_a = np.asarray(
        state_a,
        dtype=np.complex128,
    )

    state_b = np.asarray(
        state_b,
        dtype=np.complex128,
    )

    norm_a = np.linalg.norm(state_a)
    norm_b = np.linalg.norm(state_b)

    if norm_a == 0.0 or norm_b == 0.0:
        raise ValueError(
            "States must have nonzero norm."
        )

    state_a = state_a / norm_a
    state_b = state_b / norm_b

    overlap = np.vdot(
        state_a,
        state_b,
    )

    return float(
        np.abs(overlap) ** 2
    )


def pad_state(
    state: np.ndarray,
    target_length: int,
) -> np.ndarray:
    """
    Pad a shorter Fock-basis state with zeros.
    """
    state = np.asarray(
        state,
        dtype=np.complex128,
    )

    if len(state) > target_length:
        raise ValueError(
            "Target length must not be smaller "
            "than the state length."
        )

    padded = np.zeros(
        target_length,
        dtype=np.complex128,
    )

    padded[: len(state)] = state

    return padded


def lattice_cutoff_check() -> None:
    """
    Compare GKP states generated with successive
    lattice cutoffs.
    """
    delta = 0.3
    kappa = 0.3
    cutoff = 50

    lattice_cutoffs = [
        3,
        4,
        5,
        6,
        7,
        8,
    ]

    states: dict[int, np.ndarray] = {}

    print("Lattice-cutoff convergence")
    print("--------------------------")
    print(
        f"Delta = {delta}, "
        f"kappa = {kappa}, "
        f"Fock cutoff = {cutoff}"
    )
    print()

    for lattice_cutoff in lattice_cutoffs:
        states[lattice_cutoff] = (
            approximate_gkp_state(
                delta=delta,
                kappa=kappa,
                cutoff=cutoff,
                logical_index=0,
                dimension=2,
                lattice_cutoff=lattice_cutoff,
            )
        )

    print(
        f"{'L':>5}"
        f"{'L+1':>7}"
        f"{'Fidelity':>16}"
        f"{'1 - Fidelity':>18}"
    )
    print("-" * 46)

    for current, following in zip(
        lattice_cutoffs[:-1],
        lattice_cutoffs[1:],
    ):
        fidelity = pure_state_overlap_fidelity(
            states[current],
            states[following],
        )

        print(
            f"{current:>5}"
            f"{following:>7}"
            f"{fidelity:>16.12f}"
            f"{1.0 - fidelity:>18.3e}"
        )

    print()


def fock_cutoff_check() -> None:
    """
    Compare GKP states generated with different
    Fock-space cutoffs.
    """
    delta = 0.3
    kappa = 0.3
    lattice_cutoff = 6

    fock_cutoffs = [
        40,
        45,
        50,
        55,
        60,
    ]

    states: dict[int, np.ndarray] = {}

    print("Fock-cutoff convergence")
    print("-----------------------")
    print(
        f"Delta = {delta}, "
        f"kappa = {kappa}, "
        f"lattice cutoff = {lattice_cutoff}"
    )
    print()

    for cutoff in fock_cutoffs:
        states[cutoff] = (
            approximate_gkp_state(
                delta=delta,
                kappa=kappa,
                cutoff=cutoff,
                logical_index=0,
                dimension=2,
                lattice_cutoff=lattice_cutoff,
            )
        )

    print(
        f"{'N':>5}"
        f"{'N next':>9}"
        f"{'Fidelity':>16}"
        f"{'1 - Fidelity':>18}"
    )
    print("-" * 50)

    for current, following in zip(
        fock_cutoffs[:-1],
        fock_cutoffs[1:],
    ):
        current_state = pad_state(
            states[current],
            target_length=following,
        )

        following_state = states[following]

        fidelity = pure_state_overlap_fidelity(
            current_state,
            following_state,
        )

        print(
            f"{current:>5}"
            f"{following:>9}"
            f"{fidelity:>16.12f}"
            f"{1.0 - fidelity:>18.3e}"
        )

    print()


def tail_population_check() -> None:
    """
    Inspect how much probability lies near the upper
    edge of the Fock cutoff.
    """
    delta = 0.3
    kappa = 0.3
    lattice_cutoff = 6

    fock_cutoffs = [
        35,
        40,
        45,
        50,
    ]

    tail_size = 5

    print("Fock-tail population")
    print("--------------------")
    print(
        f"Last {tail_size} Fock levels"
    )
    print()

    print(
        f"{'Cutoff':>8}"
        f"{'Tail probability':>20}"
    )
    print("-" * 30)

    for cutoff in fock_cutoffs:
        state = approximate_gkp_state(
            delta=delta,
            kappa=kappa,
            cutoff=cutoff,
            logical_index=0,
            dimension=2,
            lattice_cutoff=lattice_cutoff,
        )

        probabilities = np.abs(state) ** 2

        tail_probability = float(
            np.sum(
                probabilities[
                    cutoff - tail_size :
                ]
            )
        )

        print(
            f"{cutoff:>8}"
            f"{tail_probability:>20.3e}"
        )

    print()


def main() -> None:
    lattice_cutoff_check()
    fock_cutoff_check()
    tail_population_check()


if __name__ == "__main__":
    main()