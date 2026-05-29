# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0](https://github.com/podonos/onepin-python/compare/v0.2.0...v0.3.0) (2026-05-29)


### Features

* **cli:** implement auth commands and package smoke fixes ([dbc49d8](https://github.com/podonos/onepin-python/commit/dbc49d809382aa3424b283084a0a3cfe5be6a571))


### Bug Fixes

* **ci:** decouple from Fern-overwritten __init__.py + scope pytest ([f034d45](https://github.com/podonos/onepin-python/commit/f034d456e3bd9d82597567897104e5422d510483))
* **cli:** move __version__ to onepin._cli (avoid Fern __init__.py overwrite) ([09a778c](https://github.com/podonos/onepin-python/commit/09a778ca9baa3e7f30164ecfdd5dee15d8045932))
* **cli:** respect HOME on Windows credentials path ([14e7519](https://github.com/podonos/onepin-python/commit/14e7519ae947d1a80651324cb9dc0399ba73c856))
* **publish:** install pytest in build job + wire build outputs to testpypi-smoke ([0a93407](https://github.com/podonos/onepin-python/commit/0a934074e049afe6adf34fb3f80d0b7a1d9c7027))
* **publish:** scope attestation verify to --repo, not --owner ([a1ea74c](https://github.com/podonos/onepin-python/commit/a1ea74c10ad40a1af11cfe17b8e679634ec43138))
* **publish:** strip onepin-v prefix in version output + skip-existing on TestPyPI ([4b27693](https://github.com/podonos/onepin-python/commit/4b2769382852f63f5786244b8a7d69a93210bac0))
* **release:** accept release-please's component-prefixed tag format ([a9312f4](https://github.com/podonos/onepin-python/commit/a9312f4f189ba067deef3ae29dd78cd0dc5af928))


### Documentation

* add AGENTS.md and Claude Code hooks ([#6](https://github.com/podonos/onepin-python/issues/6)) ([0551199](https://github.com/podonos/onepin-python/commit/05511993a6b58d31664a619da9c069d4eab0f6ec))
* add community health files ([#15](https://github.com/podonos/onepin-python/issues/15)) ([3da0abf](https://github.com/podonos/onepin-python/commit/3da0abf48dbf6beffe35817869d9594a9be70db4))

## [0.2.0](https://github.com/podonos/onepin-python/compare/onepin-v0.1.0...onepin-v0.2.0) (2026-05-28)


### Features

* **cli:** implement auth commands and package smoke fixes ([dbc49d8](https://github.com/podonos/onepin-python/commit/dbc49d809382aa3424b283084a0a3cfe5be6a571))


### Bug Fixes

* **ci:** decouple from Fern-overwritten __init__.py + scope pytest ([f034d45](https://github.com/podonos/onepin-python/commit/f034d456e3bd9d82597567897104e5422d510483))
* **cli:** move __version__ to onepin._cli (avoid Fern __init__.py overwrite) ([09a778c](https://github.com/podonos/onepin-python/commit/09a778ca9baa3e7f30164ecfdd5dee15d8045932))
* **cli:** respect HOME on Windows credentials path ([14e7519](https://github.com/podonos/onepin-python/commit/14e7519ae947d1a80651324cb9dc0399ba73c856))

## [Unreleased]

### Features

- Initial scaffold: Typer CLI (`onepin`) with auth, workflows, voices, templates, uploads commands
- `py.typed` PEP 561 marker for typed SDK consumers
- Full CI matrix: Python 3.10–3.13 × Ubuntu/macOS/Windows
- OIDC-based PyPI publish via trusted publisher (no token stored)
- release-please bot manages version bumps and CHANGELOG
