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

    for filename in os.listdir(dest_path):
        file_path = os.path.join(dest_path, filename)
        if filename.lower() in readme_filenames and os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                return {
                    "filename": filename,
                    "format": filename,
                    "content": content
                }

    return None

def convert_to_markdown(readme_data):
    current_datetime = datetime.datetime.now()
    current_date = current_datetime.date()

    prompt = f"""
The following README is written in {readme_data['format']}. Convert it into clean, well-structured Markdown.
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
    original_readme_path = os.path.join(dest_path, readme_data["filename"])
    # Backup the original README
    backup_path = original_readme_path + ".bak"
    shutil.copy2(original_readme_path, backup_path)

    # Write the new Markdown content to README.md (overwrite or create)
    new_readme_path = os.path.join(dest_path, "README.md")
    with open(new_readme_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"Updated README.md created at: {new_readme_path}")
    return new_readme_path


# Example usage:
model_id = "267691"
#repo_url = f"https://github.com/ModelDBRepository/{model_id}"
dest_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/readme-reformatting/{model_id}"
#clone_repo_from_github(repo_url, dest_path)
readme_data = extract_readme(model_id, dest_path)


if "error" not in readme_data:
    markdown_content = convert_to_markdown(readme_data)
    update_readme_file(dest_path, readme_data, markdown_content)
else:
    print("README file not found.")

