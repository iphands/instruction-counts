import socket
import click
import distro
import io
import os
import magic
import subprocess
import sys
import json
import logging as log
import multiprocessing as mp

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime

from cmd.process import process
from cmd.collect import collect

@click.group()
def cli() -> None:
    pass

if __name__ == "__main__":
    log.basicConfig(level=log.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    cli.add_command(collect)
    cli.add_command(process)
    cli()
