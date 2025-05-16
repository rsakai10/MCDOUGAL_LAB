import openai
import os
import requests
import zipfile
import shutil
import tempfile
import datetime
import subprocess

# Initialize OpenAI client
client = openai.OpenAI(organization="org-3z6NAgNdNa6W5HskVBdfqbxJ")


def clone_repo_from_github(repo_url, dest_path):
    if os.path.exists(dest_path):
        print(f"Destination path {dest_path} already exists. Removing it.")
        shutil.rmtree(dest_path)
    subprocess.run(["git", "clone", "--depth", "1", repo_url, dest_path], check=True)
    print(f"Repository cloned to {dest_path}")


def extract_readme(model_id, dest_path):
    if not os.path.isdir(dest_path):
        raise FileNotFoundError(f"Directory {dest_path} does not exist.")

    readme_filenames = {
        "index.html", "index.htm",
        "readme.txt", "readme.html", "readme.htm",
        "readme.md", "readme"
    }

    # Only check files in the top-level directory (no recursion)
    for filename in os.listdir(dest_path):
        file_path = os.path.join(dest_path, filename)
        if os.path.isfile(file_path) and filename.lower() in readme_filenames:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                return {
                    "filename": filename,
                    "format": filename,
                    "content": content
                }

    return {"error": "README file not found in top-level directory."}

def convert_to_markdown(readme_data):
    current_datetime = datetime.datetime.now()
    current_date = current_datetime.date()

    prompt = f"""
The following README is written in {readme_data['format']}. Convert it into clean, well-structured Markdown, but don’t wrap the result in code blocks or triple backticks. Italicize the names of the journals.
Preserve all key formatting: Headings, bullet points, code blocks, and tables. Exclude irrelevant metadata.
Do not rephrase or rewrite the content. At the end, add a changelog entry: '{current_date} – Standardized to Markdown.'

{readme_data['content']}
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a formatting assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def update_readme_file(dest_path, readme_data, markdown_content):
    # Change extension to .md
    base_name = os.path.splitext(readme_data["filename"])[0]
    old_readme_path = os.path.join(dest_path, readme_data["filename"])
    if os.path.exists(old_readme_path):
        os.remove(old_readme_path)
    new_readme_filename = base_name + ".md"
    new_readme_path = os.path.join(dest_path, new_readme_filename)

    with open(new_readme_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Updated README.md created at: {new_readme_path}")

    # Git add, commit
    subprocess.run(["git", "-C", dest_path, "add", new_readme_filename], check=True)
    subprocess.run(
        ["git", "-C", dest_path, "commit", "-m", "Standardized README to Markdown format"],
        check=True
    )

    return new_readme_path


# Example usage:
model_id = "240364"
repo_url = f"https://github.com/ModelDBRepository/{model_id}"
dest_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/readme-reformatting/{model_id}"
clone_repo_from_github(repo_url, dest_path)
readme_data = extract_readme(model_id, dest_path)


if "error" not in readme_data:
    markdown_content = convert_to_markdown(readme_data)
    update_readme_file(dest_path, readme_data, markdown_content)
else:
    print("README file not found.")

