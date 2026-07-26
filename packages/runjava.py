#!/usr/bin/env python3

# Simple Tool to run java Programs
import os
import platform
import re
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
    print("Usage: runjava <filename>")
    sys.exit()

if ARGV[0] == "--install":
    src = os.path.realpath(__file__)
    if IS_WINDOWS:
        py_path = os.path.dirname(sys.executable) + r"\Scripts"
        copy_file(src, f"{py_path}\\runjava.py")
        print("Installed as 'runjava'")
        sys.exit()
    elif IS_LINUX:
        inst_path = home() + "/.local/bin/runjava"
        copy_file(src, inst_path)
        cmd(f"chmod +x {inst_path}")
        print("Installed as 'runjava'")
        sys.exit()

nm = ARGV[0]
if nm.endswith(".java"):
    nm = nm[:-5]
if not os.path.isfile(f"{nm}.java"):
    print(nm + ".java not found")
    sys.exit()

pth = nm.replace("\\", "/").split("/")
parent_path = parent_dir(nm)

compile_data: List = cmd(f"javac {nm}.java", capture=True)

if compile_data[0] != 0:
    print(compile_data[1])
elif compile_data[0] == 0:
    try:
        run = f"java {pth[-1]}"
        if len(pth) > 1:
            prev = os.getcwd()
            try:
                os.chdir(parent_path)
                cmd(run)
            finally:
                os.chdir(prev)
        else:
            cmd(run)
    except Exception:
        pass
for x in re.findall(r"class \w+", read_file(f"{nm}.java")):
    class_path = os.path.join(parent_path, f"{x[6:]}.class")
    if os.path.isfile(class_path):
        delete_file(class_path)
