# Legacy compatibility policy

The root-level modules such as `quantum_states.py`, `beam_splitter.py`, and
`homodyne.py` remain in the development repository to support migration from
the original research scripts.

They follow three rules:

1. they forward to canonical implementations in `iqcore` or `iq4comm`;
2. canonical packages may never import them;
3. they are not included in the installed wheel and therefore are not part of
   the public package API.

New examples, tests, and documentation must use canonical package imports.
Removal of wrappers will be considered after the 0.1 alpha series and will be
announced in the changelog before it occurs.
