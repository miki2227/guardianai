# Provisional candidates (88eca75)

Prebuilt `/runtime` classes, not a fresh build. No novelty claim. #22562 excluded. No P0.

## 1. Validating mode still reads a SYSTEM subset

`XmlLoader.java` 113-120: features then `setValidating(true)`. 156-164: `checkstyle.enableExternalDtdLoad` defaults false and sets `load-external-dtd`, `external-general-entities`, and `external-parameter-entities` false. Comments 148-150 say outside files are a security problem. `resolveEntity` 83-95 returns a classpath DTD only for a mapped public id; otherwise null, so the system id remains. `ConfigurationLoader.loadConfiguration` stack line 308. `XmlLoaderTest` only checks a null resolver result for an unknown public id.

Trust boundary: the same invoker supplies the config and the file URI. That is trusted configuration. A config author can already choose modules.

This run, fixtures only `/output/csfix`, property unset, `Main` SerialGC 256m:
- `system-ok.xml` `SYSTEM file:///output/csfix/ok.dtd`: rc 0, `Starting audit... Audit done.` The external grammar was applied.
- `system-bad.xml` `SYSTEM` `marker.txt`: rc 254, marker absent, declarations must be well-formed (subset was read).
- `ge.xml` internal general entity: rc 254, marker absent, `Element type module must be declared.` Expansion not observed.

Impact: comment/flag mismatch. `load-external-dtd` does not govern validating mode. Proven effect is a config-chosen local read and a successful audit when the DTD is well formed. No content echo, no RCE. Opt-in true not tested. General-entity blocking matches the secure default and is expected.

Severity: P4 defense-in-depth, or expected validating-parser behavior. Not a verified novel defect.

Reviewer: refute if `ok.dtd` is never opened, or show this is already specified. Do not treat it as P0.

## 2. Static buffer race — not reproduced

`PropertyCacheFile.java` 75 `static final byte[] BUFFER`. `toByteArray` 320-329 reads it with no lock. `loadExternalResource` 304-310 opens a URI from configuration. `persist` 141-150 writes the cache path the operator set.

Trust boundary: resource URLs and the cache file are operator configuration. Opening them is expected.

Trigger not run: two threads in one JVM hashing external resources. Inferred torn SHA-1 would usually miss the cache. A false hit needs the torn digest to equal the stored one. Unlikely. The CLI above was single-threaded.

Severity if real: P4 correctness. Not confirmed.

Reviewer: refute if external loads are single-threaded, or reproduce the torn read.
