# Provisional candidates (88eca75)

`/runtime` classes were not rebuilt from this revision. No upstream novelty claimed. #22562 excluded. Not P0.

## 1. Default still loads a SYSTEM external DTD

`src/main/java/com/puppycrawl/tools/checkstyle/XmlLoader.java`
- 113-120: validating SAX reader; this object is the entity resolver.
- 83-95: classpath DTD only when public id is mapped; else null, so the system id stands.
- 156-164: `checkstyle.enableExternalDtdLoad` defaults false and sets `load-external-dtd`, `external-general-entities`, and `external-parameter-entities` false. Comments 148-150 call outside files a security problem.

`ConfigurationLoader.java` 319 `InternalLoader` extends `XmlLoader`. Stack in the failure below is `ConfigurationLoader.java:308`. `XmlLoaderTest.java` 56-62 does not cover a SYSTEM subset.

Trust boundary: the config is chosen by the invoker. A repo-controlled `checkstyle.xml` in CI is not an anonymous network parser, but it is not an OS-trusted file either.

Observed CLI (`Main`, SerialGC, 256m), fixtures only under `/output/csfix`:
- `system-ok.xml` `SYSTEM file:///output/csfix/ok.dtd` with a minimal `module` declaration: rc 0, `Starting audit... Audit done.` The external grammar was applied. Without it, `module` is undeclared.
- `system-bad.xml` `SYSTEM` to `marker.txt`: rc 254, marker text absent, `markup declarations ... must be well-formed.`

Impact: the secure default does not stop a validating external subset. Proven effect is a config-chosen local read that can change validation. Marker text was not echoed. No network and no `enableExternalDtdLoad=true` run. `load-external-dtd` is the nonvalidating feature.

Severity: P3. Reviewer: refute if `ok.dtd` is never opened, or find an existing issue before any novelty claim.

## 2. External general entity aborts in the JDK DTD processor

Same loader. `entity.xml` uses public id `-//Checkstyle//DTD Checkstyle Configuration 1.3//EN` (mapped, so the system id should be ignored) plus an internal-subset entity `SYSTEM file:///output/csfix/marker.txt` in `charset`.

Observed: rc 1. Marker absent. `NullPointerException` at `com.sun.org.apache.xerces.internal.impl.dtd.XMLDTDProcessor.endDTD` (`fTableOfNOTATIONAttributeNames` is null), reached from `XMLDTDScannerImpl.endEntity`. Not a clean Checkstyle SAX error.

Impact: one crafted config kills the process. No content disclosure observed. Ordinary parser crash on trusted-or-repo config, so not P0.

Severity: P4. Reviewer: reproduce under a newer JDK, or show the NPE is only this bundled XML parser.

## Not filed

`PropertyCacheFile.java` 75 static `BUFFER` and unsynchronized `toByteArray` 320-329 are a plausible in-process race, not executed. `loadExternalResource` 304-309 opens a config URI by design. `OsSpecificUtil.updateDirectory` 48-62 only creates directories. Those paths stay expected.
