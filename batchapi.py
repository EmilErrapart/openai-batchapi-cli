import click
import json
from os import listdir
from os.path import isfile, exists, join
from openai import OpenAI

client = OpenAI()
batch_file_name = "batch.jsonl"
ongoing_batch_jobs_file_name = "ongoing-batch-jobs.json"

@click.group()
def cli():
    pass

@cli.command()
@click.argument('input_folder', type=click.Path(exists=True, file_okay=False))
@click.argument('system_prompt')
@click.argument('content_prefix', default="", required=False)
def start(input_folder, system_prompt, content_prefix):
    """Create and start a batch job."""

    tasks = []

    for input_file_name in listdir(input_folder):
        input_file_path = join(input_folder, input_file_name)
        if not isfile(input_file_path):
            continue
        with open(input_file_path, "r") as file:
            input_str = file.read()
            task = {
                "custom_id": input_file_name,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },{
                            "role": "user",
                            "content": content_prefix + input_str
                        }
                    ]            
                }
            }
            tasks.append(task)

    with open(batch_file_name, 'w') as file:
        for obj in tasks:
            file.write(json.dumps(obj) + '\n')

    batch_file = client.files.create(
        file=open(batch_file_name, "rb"),
        purpose="batch"
    )

    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    ongoing_batch_jobs = {}
    
    if exists(ongoing_batch_jobs_file_name):
        with open(ongoing_batch_jobs_file_name, 'r') as file:
            ongoing_batch_jobs = json.loads(file.read())

    ongoing_batch_jobs.update({batch_job.id: input_folder})

    with open(ongoing_batch_jobs_file_name, 'w') as file:
        file.write(json.dumps(ongoing_batch_jobs))
