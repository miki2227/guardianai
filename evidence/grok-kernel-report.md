# Grok kernel containment report

Independent check of `guardian.sandbox_argv` and `guardian.execute` against the claims in `RESEARCH.md`. The implementation and the other evidence files were not modified. Payload code ran only inside Bubblewrap. Canaries were synthetic strings created for this run.

## Environment

- WSL distro `kali-linux`, user `pratz`
- Source import path: `/home/pratz/guardianai-pilot` (not edited)
- Bubblewrap 0.11.0 at `/usr/bin/bwrap`
- Disposable host directory `/home/pratz/guardianai-kernel-probe` (removed after the run)
- Probe runner: `C:\Users\sayal\.t3\projects\guardianai\evidence\grok-kernel-probes.py`
- Ten probes, all completed, no timeout. The existing nine-test suite was not re-run here.

`sandbox_argv` uses `bwrap --unshare-all --die-with-parent --new-session --cap-drop ALL --clearenv`, read-only binds of `/usr`, `/bin`, `/lib`, and `/lib64` when present, a new `/proc` and `/dev`, a tmpfs on `/tmp`, and a writable bind of the task directory at `/workspace`.

## Outcomes

| # | Probe | Result | Class |
| --- | --- | --- | --- |
| 1 | Mount table and sentinel path | Held | Containment, with read-only runtime binds |
| 2 | `/proc` fd walk and PID namespace | Held | Containment |
| 3 | Inherited fd and env canary | Fd read succeeded; env stripped | Mount bypass only if the caller leaves an fd open |
| 4 | Planted and in-sandbox symlinks | Held | Containment |
| 5 | Grandchild env and sentinel | Held | Containment |
| 6 | Inet, loopback, Unix, abstract socket | No host connection | Containment; loopback is the sandbox's own stack |
| 7 | Workspace file vs `/tmp` file | Workspace visible on host; `/tmp` not | Expected writable workspace |
| 8 | Two workspaces vs same workspace | Other workspace hidden; same workspace readable | Documented shared-storage channel |
| 9 | Capabilities, mount, devices, `/usr` write | Held | Containment |
| 10 | `execute` with a fake API key | Held | Containment |

No probe read the host sentinel through a path, symlink, `/proc` walk, other workspace, or host Unix socket. No probe reached `192.0.2.1`, changed the host, or wrote outside the task directory.

## Probe details

1. **Mount visibility.** Inside the sandbox, mounts were `/`, the read-only runtime binds, `/proc`, a minimal `/dev`, `/tmp`, and `/workspace`. `/home`, `/etc`, `/mnt`, `/opt`, `/run`, `/var`, and `/sys` were absent. The host sentinel path did not exist. Nested read-only mounts came along with `/usr` and `/lib`: `/usr/lib/wsl/drivers`, `/usr/lib/wsl/lib`, `/usr/lib/modules/6.6.87.2-microsoft-standard-WSL2`, and the matching `/lib/...` paths. That is host WSL content exposed because those directories live under the documented runtime binds. It is not a writable host escape.

2. **`/proc` fd and PID namespace.** The sandbox saw only PIDs 1 and 2. The supervisor PID 721 was not listed. Opening `/workspace` and walking `/proc/self/fd/<dirfd>/../../../../../../home/pratz/.../host-sentinel.txt` failed with `FileNotFoundError`. The same happened for `/proc/self/root/...` and `/proc/1/root/...`. `realpath` of the fd parent was `/`, so `..` stopped at the sandbox root.

3. **Inherited fd.** The supervisor opened `/home/pratz/guardianai-kernel-probe/env-canary.txt` (`FAKE-FD-CANARY`) and spawned `sandbox_argv` with `pass_fds` so that descriptor stayed open in `bwrap`. The payload's `/proc/self/fd` included that host path and `read` returned the canary. The environment variable `FAKE_CANARY=fake-canary` set on the same spawn was absent (`--clearenv`). `execute` was not the caller for this probe. `execute` uses `close_fds=True`, and probe 10 confirms the API-key variable does not arrive. Bubblewrap 0.11.0 did not close the extra descriptor on its own. This is a real mount-namespace bypass of file content when a caller of `sandbox_argv` inherits a live fd. It is not a break of the `execute` path that closes fds first.

4. **Symlinks.** A host-planted symlink in the workspace and a symlink created inside the sandbox, both aimed at the host sentinel, failed with `FileNotFoundError`.

5. **Grandchild.** `python3` inside the sandbox spawned another `python3`. The child saw `FAKE_CANARY` as missing and the host sentinel path as absent.

6. **Network.** Connect to `192.0.2.1:443` raised `OSError`. Connect to the host filesystem socket raised `FileNotFoundError`. The host was listening on abstract name `@guardianai-grok-probe`; the sandbox connect raised `ConnectionRefusedError`, which is what an absent abstract name returns, and the connect did not succeed. Connect to `127.0.0.1:9` raised `ConnectionRefusedError`, so the sandbox has its own loopback and that attempt never left the new net namespace. `socket.gethostname()` was `PRATZ1337`, the same string as the host. This probe did not call `sethostname`, so a copied UTS value and a shared UTS namespace were not distinguished. No `--hostname` is set in `sandbox_argv`.

7. **Workspace versus `/tmp`.** The payload wrote `visible.txt` in `/workspace` and `/tmp/guardian-grok-marker`. The workspace file was readable on the host as `workspace-visible-marker`. The `/tmp` marker was not present on the host. Writes in the task directory are supposed to be visible to the host. `/tmp` is a private tmpfs.

8. **Shared storage.** The host placed `channel.txt` (`SHARED-FAKE-CANARY`) in workspace A. A sandbox on workspace B did not see `channel.txt` or the host path of A's file. A sandbox on workspace A read the canary. Two agents that share a task directory can communicate through it. Agents with different directories cannot use that channel. `RESEARCH.md` already states this limit.

9. **Capabilities and devices.** `/proc/self/status` showed `CapInh`, `CapPrm`, `CapEff`, `CapBnd`, and `CapAmb` all zero. `mount -t tmpfs tmpfs /workspace/submount` exited 32: `must be superuser to use mount`. Opening `/usr/guardian-grok` for write raised `OSError`. `/dev/null` and `/dev/urandom` existed; `/dev/mem`, `/dev/kmsg`, and `/dev/sda` did not.

10. **`execute` API.** With `TYPESAFE_API_KEY=fake-canary-not-real` in the supervisor environment, `guardian.execute` ran a payload that printed `{"key": false, "sentinel": false, "home": "/tmp"}` and exited 0. The fake key was not in the child environment, the sentinel path was absent, and `HOME` was the sandbox `/tmp`.

## What was not an escape

- A writable workspace file showing up on the host.
- A second sandbox reading a file in that same workspace.
- Loopback inside the sandbox refusing a local port.
- The host hostname string appearing before any in-sandbox `sethostname` test.
- Read-only WSL directories visible under the `/usr` and `/lib` binds.

## Correction

Qualify the `RESEARCH.md` sentence that the child receives no inherited extra descriptors. That is true for `execute`, which passes `close_fds=True`. It is not true of Bubblewrap 0.11.0 or of `sandbox_argv` by themselves: an inherited descriptor remains open in the sandbox and can read the host file it already references, including a path that is not mounted. Callers of `sandbox_argv` have to close extra descriptors, as `execute` does.

No code change was made. A later patch can keep the current `execute` behavior and state the `sandbox_argv` requirement, or add a regression test that `execute` does not retain a pre-opened canary fd. Hostname copying and the read-only WSL submounts are residual host identity and runtime exposure, not the fd finding.
