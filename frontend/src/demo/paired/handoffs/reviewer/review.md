# Review of current candidates.md (88eca75)

Reconstructed from this scope's `/workspace/source/incoming/investigator/candidates.md` (2538 chars), not an earlier episode. Two candidates only. Prebuilt `/runtime` classes, not a fresh build. No novelty search. #22562 excluded. No P0 established.

## 1. Validating mode still reads a SYSTEM subset

Status: confirmed behavior. Partner severity accepted. Not raised.

Source: `XmlLoader.java` 113-120 sets features then `setValidating(true)`. 156-164 defaults `checkstyle.enableExternalDtdLoad` to false and sets nonvalidating `load-external-dtd`, `external-general-entities`, and `external-parameter-entities` false. Comments 148-150 call outside files a security problem. `resolveEntity` 83-95 returns a classpath DTD only for a mapped public id; otherwise null. `XmlLoaderTest.java` 55-62 only asserts null for an unknown public id.

This run, property unset, `Main` `-XX:+UseSerialGC -XX:ActiveProcessorCount=1 -Xmx256m`, fixtures only `/output/csfix`:
- `nodtd.xml` (no DOCTYPE): rc 254, marker absent. `Document root element "module", must match DOCTYPE root "null".`
- `system-ok.xml` SYSTEM `ok.dtd`: rc 0, marker absent, first line `Starting audit...`, output length 31 (same shape as a finished audit). The external grammar was applied; it was not left unopened.
- `system-bad.xml` SYSTEM `marker.txt`: rc 254, marker absent. Declarations must be well-formed, so the subset was read.
- `ge.xml` internal general entity: rc 254, marker absent. `Element type "module" must be declared.` Expansion not observed.

Trust boundary holds: the invoker supplied the config and the file URI and can already choose modules. The flag does not govern validating mode, so the comment overstates the default. Proven effect is a config-chosen local read and a successful audit when the DTD is well formed. No content echo, no RCE. Opt-in true was not tested. Whether a doc already specifies this was not searched.

Severity: P4 defense-in-depth, or expected validating-parser behavior. Not a verified novel defect. Not P0.

## 2. Static buffer race

Status: unresolved. Not reproduced.

Source: `PropertyCacheFile.java` 75 `static final byte[] BUFFER`. `toByteArray` 320-330 reads it with no lock. `loadExternalResource` 304-310 opens a configuration URI. `persist` 141-150 writes the operator cache path.

The CLI above was one single-threaded `Main` process. That does not prove every embedded caller is single-threaded. Torn-read trigger was not run. A false cache hit would need the torn digest to equal the stored one. Inferred and unlikely. Opening a configured URI is expected.

Severity if real: P4 correctness. Not confirmed. Not P0.

## P0

No P0. Trusted-configuration DTD loading and an unrun cache race are not P0.
