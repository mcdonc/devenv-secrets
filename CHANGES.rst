Changes
=======

v0.3 (Jun 24, 2025)
-------------------

- Use Python 3.13 rather than 3.11.

- Run tests on MacOS too.

- Use PlaintextKeyring during GH functional tests for end-to-end testing.

v0.2 (Jun 24, 2025)
-------------------

- Use lib.mkBefore instead of lib.mkAfter to invoke the enterShell of
  ``devenv-secrets`` so the user can override envvars at shell startup.

- Improve testing.

v0.1 (Jun 23, 2025)
-------------------

- Initial release.
