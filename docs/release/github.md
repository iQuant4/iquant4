# GitHub repository and launch checklist

This guide takes the verified local iQuant4 workspace to a controlled GitHub
repository without exposing development artifacts or credentials.

## 1. Create the remote repository

Create an empty GitHub repository named `iQuant4` under the intended user or
organization account. Do not ask GitHub to create a README, license, or
`.gitignore`; those files already exist locally.

A private repository is recommended for the first external review. Public
visibility can be enabled after the release gates and independent installation
checks have passed.

## 2. Connect the local repository

From the project root:

```powershell
git remote add origin https://github.com/<OWNER>/iQuant4.git
git remote -v
git push -u origin main
```

Replace `<OWNER>` with the GitHub user or organization name. SSH may be used
instead when keys are configured:

```powershell
git remote add origin git@github.com:<OWNER>/iQuant4.git
```

## 3. Confirm real CI

After the first push:

1. open the **Actions** tab;
2. confirm the Windows and Ubuntu test matrix starts;
3. confirm all scientific, architecture, packaging, and isolated-install
   checks pass;
4. download the release-candidate artifact and test it on a clean machine when
   possible.

A workflow file is only a configuration until it has completed successfully
on GitHub-hosted runners.

## 4. Configure repository settings

Recommended settings:

- default branch: `main`;
- Issues: enabled;
- Discussions: optional for the public alpha;
- vulnerability alerts and Dependabot alerts: enabled;
- secret scanning and push protection: enabled when available;
- branch protection: require the CI checks before merging;
- squash merge: enabled;
- auto-delete merged branches: enabled.

## 5. Deploy the static preview

The repository contains a manual GitHub Pages workflow. In repository
**Settings → Pages**, select **GitHub Actions** as the source. Then run the
`iQuant4 Public Preview` workflow manually.

The generated site is an informational developer-alpha preview. It must retain
its limitations and pre-release status language.

## 6. Build a release candidate

Run the manual `iQuant4 Release Candidate` workflow. It tests the package,
builds the wheel and source distribution, runs metadata and isolated-install
checks, and uploads the verified artifacts without publishing them.

## 7. TestPyPI preparation

Before uploading to TestPyPI:

- confirm the version is unique;
- confirm `twine check` passes;
- confirm both wheel and source distribution include the license;
- install the exact wheel into a clean environment;
- run `iq4comm doctor` and at least one showcase workflow;
- verify that no credentials or private data are present.

Publishing credentials must be stored as GitHub environment secrets or entered
locally through trusted tooling. They must never be committed to the
repository.

## 8. Public developer-alpha gate

The repository is ready to become public when:

- real Windows and Linux CI are green;
- the static preview deploys successfully;
- a trusted external reviewer completes a clean installation;
- the scientific validation report is current;
- the README, license, security policy, citation file, and known limitations
  are accurate;
- the current release candidate installs and runs outside the source checkout.
