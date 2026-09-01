# Bounded automation

## Monthly allocation and pull-request proof

This repository has an approved allocation of **100–300 GitHub Actions runner
minutes per month**. Pull requests targeting `develop` or `main` receive one
read-only `ubuntu-24.04` job on Python 3.13. Superseded runs cancel, and each
run has a ten-minute ceiling. The job validates governance contracts and
examples, workflow boundaries, root orientation, language, secret shapes, and
the repository-owned regression suite. Its parsed controls must match the
source-owned `.github/automation-controls.json` projection.

The pull-request path receives repository contents and proposed source through
read-only permissions. Protected values stay with their dedicated proof paths.
Monthly Dependabot updates target `develop`, group minor and patch updates, and
keep at most two update pull requests open.

## Deliberate full proof

The manual **Governance** workflow retains advisory author feedback, the
complete language and secret-shape passes, and the full regression proof. A
named receiver sets `ENABLE_GITHUB_ACTIONS=true`, selects `confirm_run`, and
dispatches it when a release or compatibility question calls for the wider
observation.

The two reusable workflows remain bounded contract surfaces. A reviewed caller
activates them with the declared inputs and, where required, an immutable
governance coordinate.

## Recovery

Local validation remains the complete source-owned proof path. Setting
`ENABLE_GITHUB_ACTIONS=false` rests the manual proof. Disabling Actions in
repository settings rests all hosted execution while local commands continue
to serve review. A reviewed rename from `.github/dependabot.yml` to
`.github/dependabot.manual.yml` returns dependency scheduling to a dormant
source state. The next receiver can restore either path from the same reviewed
workflow and configuration.
