import click
import os
import logging as log

@click.command()
def process() -> None:
    base = './raw_data'
    for i in os.listdir(base):
        if not i.endswith('.json_list'):
            continue
        path = f'{base}/{i}'
        log.info(f'Processing file: {i}')
