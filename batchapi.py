import click
import json
from os import listdir, mkdir
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
batch_file_name = "batch.jsonl"
batch_job_file_name = "batchjob.json"

@click.group()
def cli():
    pass

@cli.command()
@click.argument('input_folder_path', type=click.Path(exists=True, file_okay=False))
@click.argument('output_folder_name')
@click.option('-s', '--sys-prompt', "system_prompt", default="", help="String to be sent as system prompt")
@click.option('-p', '--prefix', "user_content_prefix", default="", help="String to be prefixed before every user input")
@click.option('-m', '--model', default="gpt-4o-mini", help="Specify a model to use. Default: gpt-4o-mini")
def start(input_folder_path, output_folder_name, system_prompt, user_content_prefix, model):
    """Create and start a batch job."""

    batch_output_path = Path("output", output_folder_name)
    if batch_output_path.exists() and not any(batch_output_path.iterdir()):
        raise Exception("Output folder is not empty")

    batch_output_path.mkdir(exist_ok=True, parents=True)
    batch_file_path = Path(batch_output_path, batch_file_name)

    #create batch file
    tasks = []
    with batch_file_path.open('w') as batch_file:
        for input_file_path in Path(input_folder_path).glob('*.txt'):
            user_content = input_file_path.read_text()
            task = {
                "custom_id": input_file_path.stem,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },{
                            "role": "user",
                            "content": user_content_prefix + user_content
                        }
                    ]            
                }
            }
            batch_file.write(json.dumps(task) + '\n')

    #upload batch file
    batch_file = client.files.create(
        file=batch_file_path.open("rb"),
        purpose="batch"
    )

    #create batch job
    batch_job = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    Path(batch_output_path, batch_job_file_name).write_text(json.dumps(batch_job))
