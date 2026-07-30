# Installed offline documentation

The `iq4comm` wheel contains a documentation generator that does not require a
source checkout, web server, or remote assets.

```powershell
iq4comm docs build --output-dir documentation_output
```

Open the result:

```powershell
iq4comm docs open --output-dir documentation_output
```

The portal contains:

- an iQuant4 architecture and roadmap overview;
- a five-minute `iqcore` and `iq4comm` quick start;
- receiver-family, lossy-cat, tomography, and dashboard workflow guides;
- generated API inventories based on intentional `__all__` exports;
- search data stored locally as JSON and JavaScript;
- explicit numerical, physical, security, and API limitations.

Generated files are static and portable. No remote stylesheet, script, font,
analytics service, or content-delivery network is required at runtime.

## Public preview integration

The installed documentation portal is automatically embedded under `docs/` when `iq4comm portal build` creates the static public preview.
