import click
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

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

    if "/" in output_folder_name:
        print("Output folder name must be a string not a path")
        return

    batch_output_path = Path("output", output_folder_name)
    if batch_output_path.exists() and any(batch_output_path.iterdir()):
        print("Output folder already exists and is not empty")
        return

    batch_output_path.mkdir(exist_ok=True, parents=True)
    batch_file_path = Path(batch_output_path, "batch.jsonl")

    #create batch file
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
    print(f"Created batch job with id: {batch_job.id}")

    save_batch_data(batch_job, batch_output_path)

@cli.command()
def check():
    """Retrieve and update status of any ongoing batch jobs. Download and save results of completed batches"""
    status_list = ["validating", "in_progress", "finalizing"]
    #check and update status
    for ongoing in get_batch_data_list(status_list):
        batch_job = client.batches.retrieve(ongoing['id'])
        batch_output_path = Path(ongoing['path'])
        if batch_job.status != ongoing['status']:
            save_batch_data(batch_job, batch_output_path)

        #download results file
        if batch_job.status != "completed": continue
        result_file_path = Path(batch_output_path, "results.jsonl")
        result_file_path.write_bytes(client.files.content(batch_job.output_file_id).content)

        #read results file and save each response to separate file
        results_folder = Path(batch_output_path, "results")
        results_folder.mkdir(exist_ok=True)
        with result_file_path.open('r') as result_file:
            for line in result_file:
                result_obj = json.loads(line.strip())
                content = result_obj['response']['body']['choices'][0]['message']['content']
                Path(results_folder, result_obj["custom_id"]).with_suffix(".txt").write_text(content)

@cli.command()
def list_ongoing():
    """List currently ongoing batch jobs and their status"""
    status_list = ["validating", "in_progress", "finalizing"]
    data = get_batch_data_list(status_list)
    if not any(data):
        print("No ongoing batch jobs")
        return
    for ongoing in data:
        batch_id = ongoing['id']
        status = ongoing['status']
        output_folder = Path(ongoing['path']).name
        print(f"ID: {batch_id}, Status: {status}, Output folder: {output_folder}")

@cli.command()
@click.argument('batch-id')
def cancel(batch_id):
    """Cancel batch job by batch id"""
    client.batches.cancel(batch_id)

#search and return all batch data with specified status
def get_batch_data_list(status_list):
    output = Path("output")
    ongoing = []
    if not output.exists(): return ongoing
    for batch_output_path in output.iterdir():
        batch_data_path = Path(batch_output_path, "batch-data.json")
        if batch_data_path.exists(): continue
        batch_data = json.loads(batch_data_path.read_text())
        if batch_data['status'] in status_list:
            ongoing.append(batch_data)
    return ongoing

def save_batch_data(batch_job, batch_output_path):
    batch_job_data = {
        "id": batch_job.id,
        "created_at": batch_job.created_at,
        "status": batch_job.status,
        "path": str(batch_output_path),
    }
    Path(batch_output_path, "batch-data.json").write_text(json.dumps(batch_job_data))
