import click
import json
from os import listdir
from os.path import isfile, join

@click.group()
def cli():
    pass

@cli.command()
@click.argument('input_folder', type=click.Path(exists=True, file_okay=False))
@click.argument('system_prompt')
@click.argument('content_prefix', default="", required=False)
def start(input_folder, system_prompt, content_prefix):
    """Create and start a batch job."""

    inputs = []

    for input_file_name in listdir(input_folder):
        input_file_path = join(input_folder, input_file_name)
        if not isfile(input_file_path):
            continue
        with open(input_file_path, "r") as input_file:
            inputs.append(input_file.read())

    tasks = []

    for index, inp in inputs:
        task = {
            "custom_id": f"task-{index}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": content_prefix + inp
                    }
                ]            
            }
        }

        tasks.append(task)
            
    batch_file_name = "batch.jsonl"

    with open(batch_file_name, 'w') as batch_file:
        for obj in tasks:
            batch_file.write(json.dumps(obj) + '\n')
