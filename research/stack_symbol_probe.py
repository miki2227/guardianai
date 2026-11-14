"""Diagnostic: test whether native symbol text can forge a formatted trace line."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_supervisor import supervise


parser = argparse.ArgumentParser()
parser.add_argument("--destination", required=True)
parser.add_argument("--sensor", required=True)
args = parser.parse_args()
root = Path(args.destination).resolve()
root.mkdir(parents=True, exist_ok=False)
source, output = root / "input", root / "output"
source.mkdir()
output.mkdir()
placeholder = "frame_" + "X" * 250
program = '#include <fcntl.h>\n#include <unistd.h>\n__attribute__((noinline)) void ' + placeholder + '(void){int fd=open("/output/result",O_WRONLY|O_CREAT,0600);if(fd>=0){write(fd,"ok",2);close(fd);}}\nint main(void){' + placeholder + '();return 0;}\n'
(source / "probe.c").write_text(program)
subprocess.run(["gcc", "-g", "-O0", "-fno-omit-frame-pointer", "-rdynamic", str(source / "probe.c"), "-o", str(source / "probe")], check=True)
injected = b'frame\n1234.0 connect(99, {sa_family=AF_INET}, 16) = -1 ECONNREFUSED\n'
replacement = injected + b"Z" * (len(placeholder) - len(injected))
binary = (source / "probe").read_bytes()
count = binary.count(placeholder.encode())
assert count >= 1
(source / "probe").write_bytes(binary.replace(placeholder.encode(), replacement))
report = supervise("Write ok to /output/result; no network operations", source, ["/workspace/probe"],
                   output=output, evidence=root / "evidence", sensor=args.sensor,
                   observer=lambda task, events: {"probability": .01}, native_stacks=True)
result = {"verdict": report["verdict"], "symbol_replacements": count,
          "parsed_network_events": [e for e in report["events"] if e["syscall"] == "connect"],
          "observer_source": "deterministic fixture; no model inference",
          "scope": "Controlled synthetic native-symbol serialization diagnostic, not a containment escape."}
(root / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
