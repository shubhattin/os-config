#!/usr/bin/env python3

import os
import sys
from typing_extensions import Annotated

from rich.console import Console
import shubhlipi as sh
import typer

console = Console()
app = typer.Typer()


@app.command()
def install():
    """
    Install the tool
    """

    pth = os.path.realpath(__file__)
    inst_path = sh.home() + "/.local/bin/daitika"
    sh.copy_file(pth, inst_path)
    sh.cmd(f"chmod +x {inst_path}")
    print("Installed as 'daitika'")
    sys.exit()


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
        sh.cmd(f"brightnessctl set +{perc}%", display=None)
    else:
        [_, data] = sh.cmd(f"ddcutil getvcp {external_no}", display=False)
        # VCP code 0x10 (Brightness                    ): current value =    xx, max value =   yyy
        current = int(data.split(":")[1].split(",")[0].split("=")[1].strip())
        max_value = int(data.split(":")[1].split(",")[1].split("=")[1].strip())
        new_brightness = current + int(perc / 100.0 * max_value)
        sh.cmd(f"ddcutil setvcp {external_no} {new_brightness}", display=False)


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
        sh.cmd(f"brightnessctl set {perc}%-", display=False)
    else:
        [_, data] = sh.cmd(f"ddcutil getvcp {external_no}", display=False)
        # VCP code 0x10 (Brightness                    ): current value =    xx, max value =   yyy
        current = int(data.split(":")[1].split(",")[0].split("=")[1].strip())
        max_value = int(data.split(":")[1].split(",")[1].split("=")[1].strip())
        new_brightness = current - int(perc / 100.0 * max_value)
        sh.cmd(f"ddcutil setvcp {external_no} {new_brightness}", display=False)


if __name__ == "__main__":
    app()
