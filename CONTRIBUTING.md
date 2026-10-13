# Contributing

## Plan work collaboratively

1. Open a feature, design, bug, or test issue using the repository forms.
2. Identify the responsible team, subsystem, requirement IDs, dependencies,
   affected interfaces, and measurable acceptance criteria.
3. Coordinate interface changes with all affected mechanical, electrical,
   controls, software, vision, and integration teams before implementation.

Competition rules and component specifications must cite an authoritative source
and revision. Mark unverified information **TBD**; do not treat assumptions as
approved requirements.

## Branch naming

Use `feature/<issue-number>-<short-description>` for work branches, for example
`feature/12-shooter-design-study`. Keep each branch focused on one issue or
closely related engineering change. Submit a pull request; do not merge directly
into `main`.

## Place artifacts correctly

- Keep subsystem CAD in its mechanical subsystem directory. Reference shared
  parts and subsystem models rather than copying full-robot CAD.
- Keep system-level assemblies under `mechanical/assemblies/`.
- Separate production robot software (`software/`) from support tools (`tools/`).
- Store verification plans in `docs/06_verification/`, executable tests and test
  reports in `tests/`, and notebook evidence references in
  `docs/08_engineering_notebook/`.
- Use descriptive artifact names and relative links. Keep a README in every
  otherwise empty directory so Git tracks the intended architecture.
- Preserve existing content and do not commit secrets, credentials, or
  copyrighted resources without distribution authorization. Use source links
  and resource registers instead.

## Engineering notebook

Start a [design log entry](docs/08_engineering_notebook/design_log/entry_template.md)
when work begins. Update it during design, prototype, test, failure analysis, and
corrective action. Record alternatives and the rationale for decisions, including
rejected approaches. Link requirements, issues, CAD revisions, measurements,
test reports, and other evidence. Do not reconstruct the notebook only at the
end of the project.

## Verification and review

Use the [verification hierarchy](tests/README.md) and
[test report template](tests/test_report_template.md). Agree on expected results
and pass/fail criteria before testing. Record the tested hardware/software
configuration, actual results, measurements with units, and unresolved issues.
Never mark an unperformed test as passed.

Complete the pull request template, link the issue, describe interface and
competition-rule impacts, and provide evidence. Request review from the
responsible subsystem and affected interface teams; integration changes need
integration review. Reviewers should check design rationale, traceability,
interfaces, safety, rules compliance, and evidence before an authorized
maintainer merges.

The architecture scaffold has no configured build, linter, test runner, or
simulation framework. For documentation-only changes, check directory coverage,
relative links, form validity, and preservation of existing artifacts. When
implementation is introduced, document its actual validation commands in the
relevant README; do not invent passing checks.
