#!/bin/env python3

import os
import sys
import datetime
from typing import Literal

try:
    import typer
    from rich.console import Console
    from rich.prompt import Confirm, Prompt
    from pydantic.dataclasses import dataclass
except ImportError:
    os.system("sudo pacman --noconfirm -S python-typer python-rich python-pydantic")
    sys.exit(-1)

app = typer.Typer()
console = Console()

LOG_PATH = "/tmp/arch_app_installer"


def read_file(file: str) -> str:
    with open(file, encoding="utf-8", mode="r") as f:
        return f.read()


@dataclass
class InstallerOptions:
    cpu_type: Literal["intel"] | Literal["amd"] = None
    gpu_type: Literal["intel"] | Literal["nvidia"] | Literal["both"] = None
    frac_scale: float = 1
    setup_google_dns: bool = True


def ask_choices(prompt: str, options: list[str]):
    CHOICES = [str(i + 1) for i in range(len(options))]
    for i, option in enumerate(options):
        console.print(f"[blue]{i+1}. {option}[/]")

    choice = Prompt.ask(prompt, choices=CHOICES)
    return options[int(choice) - 1]


def get_script(opt: InstallerOptions):
    commands: list[str] = []

    def add_pkgs(pkgs: list[str] | str):
        if isinstance(pkgs, str):
            pkgs = [pkgs]
        commands.append(f"pacman --noconfirm -S {' '.join(pkgs)}")

    def add_comment(comment: str):
        commands.append(f"# {comment}")

    def base_system_setup():
        if opt.setup_google_dns:
            commads = [
                "# Setup Google DNS",
                """rm /etc/resolv.conf""",
                """bash -c 'echo "nameserver 2001:4860:4860::8888" >> /etc/resolv.conf'""",
                """bash -c 'echo "nameserver 2001:4860:4860::8844" >> /etc/resolv.conf'""",
                """bash -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'""",
                """bash -c 'echo "nameserver 8.8.8.4" >> /etc/resolv.conf'""",
            ]
            commands.extend(commads)

        # Setting Up Pacman and Chaotic AUR
        add_comment("Setting Up Pacman and Chaotic AUR")
        commands.extend(
            [
                "pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com",
                "pacman-key --lsign-key 3056513887B78AEB",
                "pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'",
                "pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'",
            ]
        )
        commands.append(
            "curl https://raw.githubusercontent.com/shubhattin/dotfiles/refs/heads/main/others/pacman.conf -o /etc/pacman.conf"
        )

        # Add reflector to update Mirror
        add_comment("Update Mirror")
        add_pkgs("reflector")
        commands.append(
            "reflector --verbose -c IN -c SG --protocol https --sort age --latest 20 --download-timeout 5 > /etc/pacman.d/mirrorlist"
        )

        # Update System and install base packages
        add_comment("Update System and install base packages")
        commands.append("pacman --noconfirm -Syyu")
        add_pkgs(
            "base-devel gdb cmake readline unzip zip man-pages p7zip wget curl git htop btop inxi fastfetch util-linux tree bat lf fzf"
        )

        # Basic CLI Setup
        add_comment("Basic CLI Setup")
        add_pkgs("zsh powerline-fonts fzf zoxide stow chaotic-aur/oh-my-posh")
        commands.append(
            "chsh -s $(which zsh)"
        )  # this will only set for root user, so set for user manually later on

        # Kernel Setup
        add_comment("Kernel Setup, both lts ans latest")
        add_pkgs("linux linux-header linux-firmware linux-lts linux-lts-header")
        grub_config_split = read_file("/etc/default/grub").split("\n# Custom\n")
        to_add_grub_settings = False
        to_check_for = (
            "GRUB_DISABLE_SUBMENU=y",
            "GRUB_DEFAULT=saved",
            "GRUB_SAVEDEFAULT=true",
        )
        if len(grub_config_split) == 1:
            to_add_grub_settings = True
        else:
            for check in to_check_for:
                if check not in grub_config_split[1]:
                    to_add_grub_settings = True
                    break
        if to_add_grub_settings:
            commands.extend(
                [
                    """echo "# Custom" >> /etc/default/grub""",
                    """echo "GRUB_DISABLE_SUBMENU=y" >> /etc/default/grub""",
                    """echo "GRUB_DEFAULT=saved" >> /etc/default/grub""",
                    """echo "GRUB_SAVEDEFAULT=true" >> /etc/default/grub""",
                ]
            )
        commands.append("grub-mkconfig -o /boot/grub/grub.cfg")

        # DPI scaling
        add_comment("DPI Scaling for sddm using X11")
        if opt.frac_scale > 1 and not os.path.isfile("/etc/sddm.conf.d/hidpi.conf"):
            #     [General]
            # GreeterEnvironment=QT_SCREEN_SCALE_FACTORS=1.25
            commands.extend(
                [
                    """echo "[General]" >> /etc/sddm.conf.d/hidpi.conf""",
                    f"""echo "GreeterEnvironment=QT_SCREEN_SCALE_FACTORS={opt.frac_scale}" >> /etc/sddm.conf.d/hidpi.conf""",
                ]
            )

        # CPU Specific
        if opt.cpu_type == "intel":
            add_comment("Intel CPU Specific")
            add_pkgs("intel-ucode")
        elif opt.cpu_type == "amd":
            add_comment("AMD CPU Specific")
            add_pkgs("amd-ucode")

        # GPU Driver Setup
        add_comment("# GPU Driver Setup")
        add_pkgs("glmark2")

        def intel_graphic_setup():
            add_comment("Intel Graphic Setup")
            add_pkgs(
                "xf86-video-intel vulkan-intel mesa intel-media-driver libva-mesa-driver"
            )

        def nvidia_graphic_setup():
            add_comment("Nvidia Graphic Setup")
            add_pkgs(
                "nvidia nvidia-utils nvidia-settings opencl-nvidia xorg-server-devel nvidia-prime"
            )

        if opt.gpu_type == "intel":
            intel_graphic_setup()
        elif opt.gpu_type == "nvidia":
            nvidia_graphic_setup()
        elif opt.gpu_type == "both":
            intel_graphic_setup()
            nvidia_graphic_setup()

    base_system_setup()
    return "\n".join(commands)


@app.command()
def main(
    cpu_type: str = None,
    gpu_type: str = None,
    execute_script: bool = typer.Option(
        True, help="Execute the generated Installer script"
    ),
    frac_scale: float = typer.Option(None, help="Screen Scale"),
    setup_google_dns: bool = typer.Option(None, help="Setup Google DNS"),
):
    if not os.path.isdir(LOG_PATH):
        os.makedirs(LOG_PATH)
    script_out_file = os.path.join(
        LOG_PATH, f"{datetime.datetime.isoformat(datetime.datetime.now())}.sh"
    )
    # console.print(
    #     "[yellow]Make sure you are superuser. use `[white bold]sudo su[/]`[/]"
    # )
    if not frac_scale:
        frac_scale = Prompt.ask("Enter Fractional Scaling factor", default=1)
    if not setup_google_dns:
        setup_google_dns = Confirm.ask("Setup Google DNS", default=True)
    if not cpu_type:
        cpu_type = ask_choices("Enter CPU type", ["intel", "amd"])
    if not gpu_type:
        gpu_type = ask_choices("Enter GPU type", ["intel", "nvidia", "both"])

    with open("a.sh", "w") as f:
        f.write(
            get_script(
                InstallerOptions(
                    cpu_type=cpu_type,
                    gpu_type=gpu_type,
                    setup_google_dns=setup_google_dns,
                    frac_scale=frac_scale,
                )
            )
        )


if __name__ == "__main__":
    app()
