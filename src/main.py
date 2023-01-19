import logging as log

import click

from cmds.process import process
from cmds.collect import collect
from cmds.ingest import ingest_refs
from cmds.query import query

@click.group()
def cli() -> None:
    pass

if __name__ == "__main__":
    log.basicConfig(level=log.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    cli.add_command(collect)
    cli.add_command(process)
    cli.add_command(ingest_refs)
    cli.add_command(query)
    cli()
