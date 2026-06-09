# Changelog

All notable changes to this project will be documented in this file.

## [0.5.0](https://github.com/podonos/onepin-python/compare/v0.4.0...v0.5.0) (2026-06-09)


### Features

* **ci:** self-generate the SDK in-repo via Fern + .fernignore ([#30](https://github.com/podonos/onepin-python/issues/30)) ([16ebc24](https://github.com/podonos/onepin-python/commit/16ebc246a43387bef0e968c5584a6d046aba8a3d))

## [0.4.0](https://github.com/podonos/onepin-python/compare/v0.3.0...v0.4.0) (2026-06-05)


### Features

* **cli:** cross-tool onepin agent skill + skill install command ([#31](https://github.com/podonos/onepin-python/issues/31)) ([3ce5dba](https://github.com/podonos/onepin-python/commit/3ce5dba7b6a97dffb00374b5a5031a46abac1c6d))


### Bug Fixes

* **sdk:** correct list pagination `has_next` to stop at the last page ([#29](https://github.com/podonos/onepin-python/issues/29)) ([a53e37e](https://github.com/podonos/onepin-python/commit/a53e37e09f43370023351ab8814bf7ce786a7e1c))

## [0.3.0](https://github.com/podonos/onepin-python/compare/v0.2.0...v0.3.0) (2026-06-02)


### Features

* **cli:** full command surface over the Fern SDK ([#24](https://github.com/podonos/onepin-python/issues/24)) ([162d805](https://github.com/podonos/onepin-python/commit/162d8054323c2c72d50c0a62cff9f8f181f767b6))


### Bug Fixes

* **publish:** scope attestation verify to --repo, not --owner ([a1ea74c](https://github.com/podonos/onepin-python/commit/a1ea74c10ad40a1af11cfe17b8e679634ec43138))
* **release:** anchor release-please at the 0.2.0 commit ([#22](https://github.com/podonos/onepin-python/issues/22)) ([ca2dc22](https://github.com/podonos/onepin-python/commit/ca2dc22e82e5f3f4ae62ddf5d39271bb492ed8df))


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
