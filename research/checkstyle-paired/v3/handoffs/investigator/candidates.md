# Provisional candidates (88eca75)

Runtime classes were not rebuilt from this git revision. No upstream novelty claimed. Issue #22562 excluded. Not P0.

## 1. SYSTEM external subset still parsed

`XmlLoader.java` 113-120 sets validating true. 83-95 `resolveEntity` returns a classpath DTD only for a mapped public id; otherwise null, so the system id remains. 129-164 default `checkstyle.enableExternalDtdLoad=false` clears `load-external-dtd`, `external-general-entities`, and `external-parameter-entities`. Comments 146-151 say outside files are a security problem. `ConfigurationLoader.java` 319 `InternalLoader` extends this. `XmlLoaderTest.java` 56-62 only checks an unmapped public id returns null.

Trust boundary: config XML selected by the invoker, often repo-controlled in CI.

Observed CLI (`Main`, serial GC, 256m), fixtures only `/output/csfix`, marker not a credential:
- `xxe.xml` general entity `SYSTEM file:///output/csfix/marker.txt`: rc 254, marker absent, `Element type module must be declared.` Expansion not observed.
- `system.xml` `<!DOCTYPE module SYSTEM file:///output/csfix/marker.txt>`: rc 254, marker absent, `markup declarations contained or pointed to by the document type declaration must be well-formed.` That means the subset was read and rejected. No content echo.

Impact: documented default does not stop a validating SYSTEM subset. Proven effect is a config-chosen local read plus a parser error, not disclosure or RCE. `load-external-dtd` is the nonvalidating feature. Opt-in true was not tested.

Severity: P3. Reviewer: show the SYSTEM file is never opened, or repeat with a well-formed external DTD. Search issues before calling this new.

## 2. Static cache buffer race

`PropertyCacheFile.java` 75 `static final byte[] BUFFER`, unsynchronized `toByteArray` 320-330. `loadExternalResource` 304-310 opens the config URI. `persist` 141-150 uses `OsSpecificUtil.updateDirectory` (`utils/OsSpecificUtil.java` 48-62): symlink resolve and `createDirectories` only, no permission change.

Trust boundary: URLs and cache path are operator configuration. Opening them is expected.

Trigger not run: two threads in one JVM hash external resources together.

Inferred impact: torn bytes and a wrong SHA-1. Usual result is a cache reset. A false unchanged result needs the torn digest to equal the stored one. Unlikely. P4 correctness.

Reviewer: refute if external loads are single-threaded, or reproduce the torn read.

## Not filed

Known-public-id classpath DTDs and the general-entity run above match the secure default. A configured cache file is trusted local state.
