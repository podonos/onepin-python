# Changelog

All notable changes to this project will be documented in this file.

## [0.8.2](https://github.com/podonos/onepin-python/compare/v0.8.1...v0.8.2) (2026-07-08)


### Bug Fixes

* **cli:** accept any provider in voices list --provider; docs: 30 TTS models ([#72](https://github.com/podonos/onepin-python/issues/72)) ([3c88600](https://github.com/podonos/onepin-python/commit/3c88600513bc73ae9bc3fb55463d662473ca0c18))

## [0.8.1](https://github.com/podonos/onepin-python/compare/v0.8.0...v0.8.1) (2026-07-07)


### Bug Fixes

* **cli:** unwrap .data list envelopes in pager output ([7086729](https://github.com/podonos/onepin-python/commit/70867293ef63dc3b4e7747aa2e222e627268624e))
* **fern:** enable pagination in python-sdk generator config ([107f35c](https://github.com/podonos/onepin-python/commit/107f35c661815d1eb154077ef1f020f8a2888425))

## [0.8.0](https://github.com/podonos/onepin-python/compare/v0.7.1...v0.8.0) (2026-07-03)


### Features

* sync SDK to OnePin API v0.40.2 ([#64](https://github.com/podonos/onepin-python/issues/64)) ([aa97888](https://github.com/podonos/onepin-python/commit/aa97888912968233d7b8278a5e028789d15ef281))
* sync SDK to OnePin API v0.40.3 ([#66](https://github.com/podonos/onepin-python/issues/66)) ([2f2e765](https://github.com/podonos/onepin-python/commit/2f2e7652d49fd266ba50ede69669196f3e254659))
* sync SDK to OnePin API v0.41.33 ([#70](https://github.com/podonos/onepin-python/issues/70)) ([394f488](https://github.com/podonos/onepin-python/commit/394f488ea3cfcae0b60d5d6a87f4ff06c9beb08d))


### Bug Fixes

* **ci:** make PyPI promote idempotent for already-published versions ([#67](https://github.com/podonos/onepin-python/issues/67)) ([9acc656](https://github.com/podonos/onepin-python/commit/9acc656075c4ab37342d99405b9e12debae3aa64))
* **ci:** regenerate SDK from public-spec.yaml, add narrowing guard ([#69](https://github.com/podonos/onepin-python/issues/69)) ([76a0b71](https://github.com/podonos/onepin-python/commit/76a0b71893b02defdab9fb41fea3c42d842d4578))

## [0.7.1](https://github.com/podonos/onepin-python/compare/v0.7.0...v0.7.1) (2026-06-22)


### Bug Fixes

* **cli:** correct dead api-key dashboard url and align brand to Onepin ([#61](https://github.com/podonos/onepin-python/issues/61)) ([ffd5649](https://github.com/podonos/onepin-python/commit/ffd5649c50b0982b68b232d9c51e28afa483cfeb))

## [0.7.0](https://github.com/podonos/onepin-python/compare/v0.6.0...v0.7.0) (2026-06-19)


### Features

* SDK version-compat gate, health version surface, upgrade nudge ([#52](https://github.com/podonos/onepin-python/issues/52)) ([e61a07d](https://github.com/podonos/onepin-python/commit/e61a07d289073104a086ed6aec6161a6169f829a))
* sync SDK to OnePin API v0.38.12 ([#54](https://github.com/podonos/onepin-python/issues/54)) ([0338590](https://github.com/podonos/onepin-python/commit/0338590eb1439b8e4051dd506da479d6b1317cab))

## [0.6.0](https://github.com/podonos/onepin-python/compare/v0.5.0...v0.6.0) (2026-06-15)


### Features

* regenerate SDK from API spec [@9fe47587946f7ab984ac1dd701c85c15c368a67](https://github.com/9fe47587946f7ab984ac1dd701c85c15c368a67)c (spec v0.37.7) ([#43](https://github.com/podonos/onepin-python/issues/43)) ([f429244](https://github.com/podonos/onepin-python/commit/f4292440ac7481a07a2ef8670b6a88ecb8ad0791))

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
