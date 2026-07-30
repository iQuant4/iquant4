# Public API for the 0.1.0a1 developer alpha

The following namespaces are the supported public entry points for the first
alpha. Internal module paths may change without notice.

## Shared engine (`iqcore`)

```python
from iqcore.states import (
    fock_state,
    coherent_state,
    even_cat_state,
    approximate_gkp_state,
    squeezed_vacuum_state,
    thermal_state,
    two_mode_squeezed_vacuum_state,
    density_matrix,
    tensor_product,
    partial_trace,
)

from iqcore.operators import (
    annihilation_operator,
    displacement_operator,
    squeezing_operator,
)

from iqcore.measurements import (
    quadrature_statistics,
    quadrature_probability_density,
    sample_quadrature,
    build_measurement_operators,
)

from iqcore.channels import pure_loss_channel
from iqcore.optics import apply_beam_splitter, phase_shift_channel, SignFreeOPA
from iqcore.phase_space import wigner_function, wigner_negativity
from iqcore.tomography import reconstruct_density_matrix
from iqcore.metrics import pure_state_fidelity, mean_photon_number
```

## Communications branch (`iq4comm`)

```python
from iq4comm import (
    BinaryCoherentSource,
    FiberChannel,
    HomodyneReceiver,
    HeterodyneReceiver,
    PNRReceiver,
    ErasureHomodyneReceiver,
    ErasureHeterodyneReceiver,
    ErasurePNRReceiver,
    optimize_receiver,
)

from iq4comm.analysis.receiver_family import compare_receiver_families

from iq4comm.showcase import (
    build_showcase_dashboard,
    open_showcase_dashboard,
    run_alpha_showcase,
    run_lossy_cat_showcase,
    run_receiver_family_showcase,
    run_sign_free_tomography_showcase,
)

from iq4comm.documentation import (
    build_documentation_portal,
    documentation_payload,
    open_documentation_portal,
)
```

## Command line

```powershell
iq4comm --version
iq4comm doctor
iq4comm docs build --output-dir documentation_output
iq4comm receiver-family --distances 0 20 40
iq4comm showcase all --output-dir showcase_output
iq4comm showcase dashboard --output-dir showcase_output
```

## Compatibility policy

The root-level research modules are compatibility wrappers for the development
source checkout. They are not shipped in the wheel and are not part of the
supported installed API. They may be removed after the alpha migration period.

## Public preview

```python
from iq4comm.portal import (
    PublicPreviewResult,
    build_public_preview,
    open_public_preview,
)
```

Command-line interface:

```text
iq4comm portal build
iq4comm portal open
```
