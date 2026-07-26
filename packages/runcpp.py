#!/usr/bin/env python3

# Simple Tool to run C/C++ Programs
import os
import platform
import shutil
import subprocess
import sys
from typing import List

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
ARGV = sys.argv[1:]


def home() -> str:
    return os.path.expanduser("~")


def read_file(loc: str) -> str:
    with open(loc, encoding="utf-8") as f:
        return f.read()


def write_file(loc: str, val: str) -> None:
    parent = os.path.dirname(loc)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(loc, encoding="utf-8", mode="w") as f:
        f.write(val)


def copy_file(frm: str, to: str) -> None:
    parent = os.path.dirname(to)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.copy2(frm, to)


def delete_file(fl: str) -> None:
    if os.path.exists(fl):
        os.remove(fl)


def cmd(comm: str, capture: bool = False):
    """Run a shell command. capture=True → [returncode, output]; else live exit code."""
    if capture:
        p = subprocess.run(
            comm,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return [p.returncode, p.stdout or ""]
    return subprocess.call(comm, shell=True)


def parent_dir(loc: str) -> str:
    return os.path.dirname(os.path.abspath(loc)) or "."


if len(ARGV) == 0:
    print("Usage: runcpp <filename>")
    sys.exit()

if ARGV[0] == "--install":
    src = os.path.realpath(__file__)
    if IS_WINDOWS:
        py_path = os.path.dirname(sys.executable) + r"\Scripts"
        copy_file(src, f"{py_path}\\runcpp.py")
        print("Installed as 'runcpp'")
        sys.exit()
    elif IS_LINUX:
        inst_path = home() + "/.local/bin/runcpp"
        copy_file(src, inst_path)
        cmd(f"chmod +x {inst_path}")
        print("Installed as 'runcpp'")
        sys.exit()

NM = ARGV[0]

if os.path.isfile(f"{NM}.cpp"):
    NM = f"{NM}.cpp"
elif os.path.isfile(f"{NM}.c"):
    NM = f"{NM}.c"

if not NM.endswith(".c") and not NM.endswith(".cpp"):
    print("Not a C/C++ file")
    sys.exit()
if not os.path.isfile(f"{NM}"):
    print(NM + " not found")
    sys.exit()

compiler_name = {"cpp": "g++", "c": "gcc"}[NM.split(".")[-1]]

pth = NM.replace("\\", "/").split("/")
ONLY_NAME = ".".join(pth[-1].split(".")[:-1])
OUTPUT_EXT = "exe" if IS_WINDOWS else "o"
compile_data: List = cmd(
    f"{compiler_name} {NM} -o {ONLY_NAME}.{OUTPUT_EXT}", capture=True
)

if compile_data[0] != 0:
    print(compile_data[1])
elif compile_data[0] == 0:
    try:
        if IS_LINUX:
            cmd(f"./{ONLY_NAME}.{OUTPUT_EXT}")
        elif IS_WINDOWS:
            cmd(f".\\{ONLY_NAME}.{OUTPUT_EXT}")
    except Exception:
        pass
    finally:
        delete_file(f"{ONLY_NAME}.{OUTPUT_EXT}")
