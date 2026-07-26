#!/usr/bin/env python3

# Simple Tool to run C# Programs (single file or siblings sharing namespaces)
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

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


def which(name: str) -> Optional[str]:
    return shutil.which(name)


def quote_arg(a: str) -> str:
    if IS_WINDOWS:
        if not a or any(c in a for c in ' \t"&<>|^'):
            return '"' + a.replace('"', '\\"') + '"'
        return a
    if not a or any(c in a for c in " \t\"'\\$`!&|;<>()"):
        return "'" + a.replace("'", "'\"'\"'") + "'"
    return a


if len(ARGV) == 0:
    print("Usage: runcs <filename> [args...]")
    sys.exit()

if ARGV[0] == "--install":
    src = os.path.realpath(__file__)
    if IS_WINDOWS:
        py_path = os.path.dirname(sys.executable) + r"\Scripts"
        copy_file(src, f"{py_path}\\runcs.py")
        print("Installed as 'runcs'")
        sys.exit()
    elif IS_LINUX:
        inst_path = home() + "/.local/bin/runcs"
        copy_file(src, inst_path)
        cmd(f"chmod +x {quote_arg(inst_path)}")
        print("Installed as 'runcs'")
        sys.exit()

nm = ARGV[0]
app_args = ARGV[1:]

if nm.endswith(".cs"):
    nm = nm[:-3]
if not os.path.isfile(f"{nm}.cs"):
    print(nm + ".cs not found")
    sys.exit()

entry = os.path.abspath(f"{nm}.cs")
entry_dir = os.path.dirname(entry)
entry_name = os.path.basename(entry)


def is_library_cs(path: str) -> bool:
    """True if file looks like a companion source (not its own program entry)."""
    try:
        text = read_file(path)
    except Exception:
        return False
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*?$", "", text, flags=re.M)
    if re.search(
        r"\b(?:static\s+)?(?:async\s+)?(?:void|int|Task(?:\s*<\s*int\s*>)?)\s+Main\s*\(",
        text,
    ):
        return False
    has_type = bool(
        re.search(r"\b(?:namespace|class|struct|interface|enum|record)\b", text)
    )
    stripped = re.sub(r"^\s*#.*?$", "", text, flags=re.M)
    stripped = re.sub(r"^\s*using\s+[^;]+;\s*", "", stripped, flags=re.M)
    stripped = stripped.strip()
    if not has_type and stripped:
        return False
    return bool(has_type)


def collect_sources(entry_path: str) -> List[str]:
    """Entry file plus sibling .cs libraries in the same directory."""
    sources = [entry_path]
    parent = os.path.dirname(entry_path)
    entry_base = os.path.basename(entry_path)
    try:
        siblings = sorted(os.listdir(parent))
    except OSError:
        return sources
    for name in siblings:
        if not name.endswith(".cs") or name == entry_base:
            continue
        path = os.path.join(parent, name)
        if os.path.isfile(path) and is_library_cs(path):
            sources.append(path)
    return sources


def detect_tfm() -> str:
    """Pick a TargetFramework from the installed .NET runtime (fallback net8.0)."""
    if not which("dotnet"):
        return "net8.0"
    data = cmd("dotnet --list-runtimes", capture=True)
    out = data[1] if isinstance(data, list) and len(data) > 1 else str(data)
    versions: List[Tuple[int, int]] = []
    for line in str(out).splitlines():
        m = re.search(r"Microsoft\.NETCore\.App\s+(\d+)\.(\d+)", line)
        if m:
            versions.append((int(m.group(1)), int(m.group(2))))
    if not versions:
        return "net8.0"
    major, minor = max(versions)
    return f"net{major}.{minor}"


def run_dotnet_file(path: str, args: List[str]) -> int:
    c = f"dotnet run --file {quote_arg(path)}"
    if args:
        c += " -- " + " ".join(quote_arg(a) for a in args)
    return int(cmd(c) or 0)


def run_with_temp_project(sources: List[str], args: List[str]) -> int:
    """Compile entry + companion sources via a throwaway project (no leftover csproj)."""
    tfm = detect_tfm()
    with tempfile.TemporaryDirectory(prefix="runcs_") as tmp:
        compile_items = []
        for src in sources:
            base = os.path.basename(src)
            shutil.copy2(src, os.path.join(tmp, base))
            compile_items.append(f'    <Compile Include="{base}" />')
        csproj = os.path.join(tmp, "runcs_tmp.csproj")
        write_file(
            csproj,
            "\n".join(
                [
                    '<Project Sdk="Microsoft.NET.Sdk">',
                    "  <PropertyGroup>",
                    "    <OutputType>Exe</OutputType>",
                    f"    <TargetFramework>{tfm}</TargetFramework>",
                    "    <ImplicitUsings>enable</ImplicitUsings>",
                    "    <Nullable>enable</Nullable>",
                    "    <EnableDefaultCompileItems>false</EnableDefaultCompileItems>",
                    "  </PropertyGroup>",
                    "  <ItemGroup>",
                    *compile_items,
                    "  </ItemGroup>",
                    "</Project>",
                    "",
                ]
            ),
        )
        c = f"dotnet run --project {quote_arg(csproj)}"
        if args:
            c += " -- " + " ".join(quote_arg(a) for a in args)
        prev = os.getcwd()
        try:
            os.chdir(tmp)
            return int(cmd(c) or 0)
        finally:
            os.chdir(prev)


def find_ref_dir() -> Optional[str]:
    """Locate Microsoft.NETCore.App.Ref reference assemblies."""
    candidates = []
    info = cmd("dotnet --info", capture=True)
    text = info[1] if isinstance(info, list) and len(info) > 1 else ""
    roots = []
    for line in str(text).splitlines():
        if "Base Path" in line:
            base = line.split(":", 1)[-1].strip().rstrip("/\\")
            roots.append(os.path.dirname(os.path.dirname(base)))
    for env_key in ("DOTNET_ROOT", "DOTNET_ROOT(x86)"):
        v = os.environ.get(env_key)
        if v:
            roots.append(v)
    if IS_WINDOWS:
        roots.append(r"C:\Program Files\dotnet")
        roots.append(os.path.expandvars(r"%ProgramFiles%\dotnet"))
    else:
        roots.extend(
            ["/usr/share/dotnet", "/usr/lib/dotnet", os.path.expanduser("~/.dotnet")]
        )
    for root in roots:
        pack = os.path.join(root, "packs", "Microsoft.NETCore.App.Ref")
        if not os.path.isdir(pack):
            continue
        for ver in sorted(os.listdir(pack), reverse=True):
            ref_root = os.path.join(pack, ver, "ref")
            if not os.path.isdir(ref_root):
                continue
            for tfm in sorted(os.listdir(ref_root), reverse=True):
                d = os.path.join(ref_root, tfm)
                if os.path.isfile(os.path.join(d, "System.Runtime.dll")):
                    candidates.append(d)
    return candidates[0] if candidates else None


def find_roslyn_csc() -> Optional[str]:
    info = cmd("dotnet --info", capture=True)
    text = info[1] if isinstance(info, list) and len(info) > 1 else ""
    for line in str(text).splitlines():
        if "Base Path" in line:
            base = line.split(":", 1)[-1].strip()
            csc = os.path.join(base, "Roslyn", "bincore", "csc.dll")
            if os.path.isfile(csc):
                return csc
    return None


def run_with_csc(sources: List[str], args: List[str]) -> int:
    """Fallback: compile with Roslyn csc / PATH csc, then execute."""
    out_dll = os.path.join(entry_dir, os.path.splitext(entry_name)[0] + ".dll")
    runtimeconfig = out_dll[:-4] + ".runtimeconfig.json"
    src_args = " ".join(quote_arg(s) for s in sources)

    csc_dll = find_roslyn_csc()
    ref_dir = find_ref_dir()
    compile_cmd = None

    if csc_dll and ref_dir and which("dotnet"):
        refs = [
            "System.Runtime.dll",
            "System.Console.dll",
            "System.Linq.dll",
            "System.Collections.dll",
            "netstandard.dll",
        ]
        ref_flags = " ".join(
            f"-r:{quote_arg(os.path.join(ref_dir, r))}"
            for r in refs
            if os.path.isfile(os.path.join(ref_dir, r))
        )
        compile_cmd = (
            f"dotnet {quote_arg(csc_dll)} -nologo -nostdlib+ {ref_flags} "
            f"-t:exe -out:{quote_arg(out_dll)} {src_args}"
        )
    elif which("csc"):
        compile_cmd = f"csc -nologo -t:exe -out:{quote_arg(out_dll)} {src_args}"

    if not compile_cmd:
        print("Neither 'dotnet' nor 'csc' is available")
        return 1

    compile_data = cmd(compile_cmd, capture=True)
    code = compile_data[0] if isinstance(compile_data, list) else 1
    if code != 0:
        print(compile_data[1] if isinstance(compile_data, list) else compile_data)
        return int(code) if code else 1

    try:
        tfm = detect_tfm()
        major = tfm[3:].split(".")[0] if tfm.startswith("net") else "8"
        write_file(
            runtimeconfig,
            "\n".join(
                [
                    "{",
                    '  "runtimeOptions": {',
                    f'    "tfm": "{tfm}",',
                    '    "framework": {',
                    '      "name": "Microsoft.NETCore.App",',
                    f'      "version": "{major}.0.0"',
                    "    }",
                    "  }",
                    "}",
                    "",
                ]
            ),
        )
        run_cmd = f"dotnet {quote_arg(out_dll)}"
        if args:
            run_cmd += " " + " ".join(quote_arg(a) for a in args)
        return int(cmd(run_cmd) or 0)
    finally:
        delete_file(out_dll)
        delete_file(runtimeconfig)
        delete_file(out_dll[:-4] + ".pdb")
        delete_file(out_dll[:-4] + ".exe")


sources = collect_sources(entry)
has_dotnet = which("dotnet") is not None

try:
    if has_dotnet:
        if len(sources) == 1:
            rc = run_dotnet_file(entry, app_args)
        else:
            rc = run_with_temp_project(sources, app_args)
    else:
        rc = run_with_csc(sources, app_args)
except Exception:
    rc = 1

sys.exit(rc if isinstance(rc, int) else 0)
