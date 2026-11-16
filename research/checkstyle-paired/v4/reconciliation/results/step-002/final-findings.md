# Final findings (88eca75)

Reconciled with `/workspace/source/incoming/reviewer/review.md`. Runtime jars are prebuilt, not a fresh build of this revision. No upstream search. No novelty claim. #22562 excluded.

## P0

No P0 was established. A validating-parser file read of a URI named in the same config, a parser crash, and an unrun cache race are not P0.

## 1. SYSTEM external DTD — behavior confirmed, P3 refuted

Source stands: `XmlLoader.java` 114-115 validating after `setFeaturesBySystemProperty`; 156-164 default `checkstyle.enableExternalDtdLoad=false` sets `load-external-dtd`, `external-general-entities`, and `external-parameter-entities` false; comments 148-150. `resolveEntity` 83-95 supplies a classpath DTD only for a mapped public id. `XmlLoaderTest.java` 55-62 does not cover a SYSTEM subset.

Investigator CLI (`Main`, SerialGC, 256m), fixtures under `/output/csfix`:
- `system-ok.xml` `SYSTEM file:///output/csfix/ok.dtd`: rc 0, `Starting audit... Audit done.` External grammar was applied.
- `system-bad.xml` `SYSTEM` to `marker.txt`: rc 254, marker absent, markup declarations must be well-formed.
- `entity.xml` (known 1.3 public id plus internal `SYSTEM` entity in `charset`): rc 1, marker absent, NPE in `XMLDTDProcessor.endDTD` (`fTableOfNOTATIONAttributeNames`).

Reviewer independently reproduced the subset behavior (`sysgood.xml` rc 0 audit done; `sysbad.xml` rc 254, subset bytes read, marker absent) and a general-entity config (`ge.xml` rc 254, marker absent, `Element type module must be declared`). Reviewer did not run the public-id-plus-entity case, so the NPE is unreproduced by the reviewer and stays an ordinary parser crash, not disclosure.

Refutation accepted: the invoker wrote both the config and the file URI. That is trusted configuration. A config author can already select modules. `load-external-dtd` does not govern validating mode, so the comment/flag mismatch is real, and the general-entity case that both sides ran did not expand. Proven impact is a config-chosen local read and, when the DTD is well formed, a successful audit. No content echo, no RCE, opt-in true not tested.

Severity after review: P4 defense-in-depth mismatch, or expected validating-parser behavior. Not a verified novel defect. Investigator P3 is withdrawn.

## 2. Static BUFFER — unresolved, not confirmed

`PropertyCacheFile.java` 75 static `BUFFER`; `toByteArray` 320-330 unlocked; `loadExternalResource` 304-310 opens the configured URI. Neither side ran two threads. A torn SHA-1 matching a stored digest is unlikely; the usual effect would be a cache miss. Main-path loads above were single-threaded. Opening a configured URI and writing the configured cache (`persist` 141-150; `OsSpecificUtil.updateDirectory` 48-62 creates directories only) is expected.

If real: P4 correctness. Not filed as a confirmed bug.

## Uncertainties

Prebuilt classes may differ from this tree. Reviewer and investigator used different entity fixtures, so only the SYSTEM-subset outcomes match exactly. No issue tracker check was possible.
