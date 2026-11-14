# Run an ordinary worker under Jev oversight

Use Linux or WSL2 on x86_64, Python 3.10+, GCC, Bubblewrap with user namespaces,
and strace built with native stack support (`strace -V` lists libunwind).
The validated installation uses strace 7.0. Keep the project and run directories
on the native Linux filesystem. The supervisor needs `TYPESAFE_API_KEY` in its
environment; do not put it in the task, public directory, command arguments or logs.
The current development environment already has a working credential.
The current gate requires native launcher policy version 3. Rebuild an existing
helper after updating; an older helper is rejected before worker launch. The
demo command also rebuilds the helper automatically.
Workers cannot install their own seccomp filters in this profile; supported
seccomp queries and unrelated `prctl` operations remain allowed. Applications that
require their own seccomp sandbox need a different runtime profile.

From the project directory inside WSL:

```sh
gcc -Wall -Wextra -Werror -O2 native/notify_launch.c -o native/notify-launch
python3 research/working_demo.py --destination "$HOME/guardian-demo-$(date +%s)" \
  --sensor /path/to/strace
```

The destination must be new. The demo creates only synthetic data, calls the real
Jev observer, and retains source snapshots, traces, decisions and CLI outcomes.
It checks an approved read, a denied unregistered read and an ordinary exit-code
failure. It does not spawn additional model-agent subjects or train weights.

For an existing ordinary worker, place public files in a dedicated input directory
and keep protected files outside input/output and runtime mounts. Use an empty
output directory and a new evidence directory. For example, after preparing those
directories and an approved synthetic summary:

```sh
python3 guarded_agent.py \
  --task 'Read the approved summary and print its exact contents.' \
  --workspace /home/user/guardian-input \
  --output /home/user/guardian-empty-output \
  --evidence /home/user/guardian-new-evidence \
  --sensor /path/to/strace \
  --resource summary=/home/user/guardian-private/summary.txt -- \
  /usr/bin/cat /protected/summary
```

Replace `/home/user` and the strace path with actual Linux paths. Each resource
name is one component; each snapshot is at most 32 KiB. Add repeated `--resource`
arguments only for files the worker is allowed to request. Public inputs remain
readable without a Jev release decision. Jev sees resource identity/hash/size and
task metadata at this boundary, not the resource contents.

Exit 77 means a detected violation, 78 means abstention/failure to establish the
oversight contract. Otherwise the CLI preserves the worker's exit status. Worker
stdout is in `evidence/stdout.txt`; the CLI prints the verdict and evidence path.
`guarded-agent.json` joins runtime and release audits. `observer-input-*.json`
retains exact frozen native-event inputs submitted to the runtime observer.

Inspect the retained development evidence without a key or WSL:

```sh
python research/kernel_summary.py
```

Run the full tests inside Linux for actual containment coverage:

```sh
python3 -m unittest discover -s tests -v
```

Windows-only execution skips Linux tests. The [kernel report](KERNEL_GATE_REPORT.md)
defines the supported boundary and retained limitations. This launcher observes
local execution and gates provisioned protected resources; OS traces cannot read
latent model thoughts or stop a remote provider's inference session.
