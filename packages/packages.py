#!/usr/bin/env python3

import os
import subprocess
import sys

ARGV = sys.argv[1:]


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


pkg = {
    "lekhika": ["keyboard", "mouse", "winregistry", "pillow", "pystray"],
    "sarve": [
        "black",  # Python Beutifier
        "pyaml",  # .yaml file management
        "wheel",
        "deta",
        "toml",
        "flask",
        "fastapi",
        "twine",  # upload pip package
        "uvicorn[standard]",  # Server ASGI
        "GitPython",
        "python-dotenv",  # .env file parsing
        "autopep8",  # Python Beutifier
        "openpyxl",  # Managing Excel files
        "pywin32",
        "pyperclip",  # Clipboard copy and paste
        "requests",
        "markdown",  # Markdown to HTML
        "markdownify",  # HTML to Markdown
        "Pygments",  # Code Highlighting
        "brotlipy",  # decodng 'br' based responses
        "virtualenv",  # Virtual Environment manages
        "bcrypt",  # Encryption Algorithm
        "croytography",  # Encrypting and Decrypting text
        "python-multipart",  # Form Parser in FastAPI
        "python-jose[cryptography]",  # JWT Handler
        "datamodel_code_generator",  # Type Server
    ],
    "exe": ["https://github.com/pyinstaller/pyinstaller/tarball/develop"],
}
extra_cmd = {
    "sarve": [
        "pywin32_postinstall.py -instal",  # To setup pywin32
        "npm install -g terser",  # JS minifier installation
        "npm install -g serve",  # Serve static assets locally for testing
        # type script json iteface generator
        "npm install -g tslib prettier json-to-typing",
    ]
}
if __name__ == "__main__":
    for x in ARGV:
        if x in pkg:
            for c in pkg[x]:
                cmd(f"pip install {c}")
        if x in extra_cmd:
            for c in extra_cmd[x]:
                cmd(c)
