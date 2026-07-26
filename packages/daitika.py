#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from typing_extensions import Annotated

from rich.console import Console
import typer

console = Console()
app = typer.Typer()


def home() -> str:
    return os.path.expanduser("~")


def copy_file(frm: str, to: str) -> None:
    parent = os.path.dirname(to)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.copy2(frm, to)


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


@app.command()
def install():
    """
    Install the tool
    """

    pth = os.path.realpath(__file__)
    inst_path = home() + "/.local/bin/daitika"
    copy_file(pth, inst_path)
    cmd(f"chmod +x {inst_path}")
    print("Installed as 'daitika'")
    sys.exit()


"""
Use `sudo ddcutil detect` to find the display numebr
"""


@app.command()
def up(
    perc: int,
    external: bool = False,
    external_no: Annotated[int, typer.Argument(envvar="EXTERNAL_MONITOR_NUMBER")] = 10,
):
    """
    Increase Brightness
    """
    if not external:
        cmd(f"brightnessctl set +{perc}%")
    else:
        [_, data] = cmd(f"ddcutil getvcp {external_no}", capture=True)
        # VCP code 0x10 (Brightness                    ): current value =    xx, max value =   yyy
        current = int(data.split(":")[1].split(",")[0].split("=")[1].strip())
        max_value = int(data.split(":")[1].split(",")[1].split("=")[1].strip())
        new_brightness = min(current + int(perc / 100.0 * max_value), max_value)
        cmd(f"ddcutil setvcp {external_no} {new_brightness}", capture=True)


@app.command()
def down(
    perc: int,
    external: bool = False,
    external_no: Annotated[int, typer.Argument(envvar="EXTERNAL_MONITOR_NUMBER")] = 10,
):
    """
    Decrease Brightness
    """
    if not external:
        cmd(f"brightnessctl set {perc}%-", capture=True)
    else:
        [_, data] = cmd(f"ddcutil getvcp {external_no}", capture=True)
        # VCP code 0x10 (Brightness                    ): current value =    xx, max value =   yyy
        current = int(data.split(":")[1].split(",")[0].split("=")[1].strip())
        max_value = int(data.split(":")[1].split(",")[1].split("=")[1].strip())
        min_value_possible = os.environ.get("MIN_EXTERNAL_BRIGHTNESS")
        new_brightness = max(
            current - int(perc / 100.0 * max_value),
            int(min_value_possible) if min_value_possible else 0,
        )
        cmd(f"ddcutil setvcp {external_no} {new_brightness}", capture=True)


if __name__ == "__main__":
    app()
    # Prefix with `~/local/bin/` while registering shortcut in KDE
