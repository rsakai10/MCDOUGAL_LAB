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

def download_model_zip(model_id, save_path):
    url = f"https://modeldb.science/download/{model_id}"
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return save_path
    else:
        raise Exception(f"Failed to download model. Status code: {response.status_code}")

def extract_readme_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_file:
        for subfilename in zip_file.namelist():
            filename = os.path.basename(subfilename).lower()
            if filename in ("index.html", "index.htm", "readme.txt", "readme.html", "readme.htm", "readme.md", "readme"):
                with zip_file.open(subfilename) as f:
                    content = f.read().decode('utf-8', errors='replace')
                    return {
                        "filename": subfilename,
                        "format": filename,
                        "content": content
                    }
    return {"error": "No suitable README found"}

def update_zip_with_markdown(original_zip_path, readme_data, markdown_content, model_id):
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract ZIP
        with zipfile.ZipFile(original_zip_path, 'r') as zip_file:
            zip_file.extractall(temp_dir)

        # Detect the folder name inside the ZIP
        folder_names = [name for name in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, name))]
        if not folder_names:
            raise Exception("No folder found inside the ZIP file.")
        target_folder = os.path.join(temp_dir, folder_names[0])  # Assuming there's only one folder

        # Remove old README
        old_path = os.path.join(target_folder, os.path.basename(readme_data["filename"]))
        if os.path.exists(old_path):
            os.remove(old_path)

        # Save new README.md inside the detected folder
        new_readme_path = os.path.join(target_folder, f"{model_id}_README.md")
        with open(new_readme_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        # Repackage the ZIP
        updated_zip_path = original_zip_path.replace(".zip", "_updated.zip")
        with zipfile.ZipFile(updated_zip_path, 'w') as zipf:
            for folder, _, files in os.walk(temp_dir):
                for file in files:
                    abs_path = os.path.join(folder, file)
                    rel_path = os.path.relpath(abs_path, temp_dir)
                    zipf.write(abs_path, rel_path)

        print(f"Updated ZIP created at: {updated_zip_path}")
        return updated_zip_path

def clone_repo_from_github(repo_url, dest_path):
    if os.path.exists(dest_path):
        print(f"Destination path {dest_path} already exists. Removing it.")
        shutil.rmtree(dest_path)
    subprocess.run(["git", "clone", "--depth", "1", repo_url, dest_path], check=True)
    print(f"Repository cloned to {dest_path}")

def extract_readme_from_folder(dest_path):
    readme_filenames = {
        "index.html", "index.htm",
        "readme.txt", "readme.html", "readme.htm",
        "readme.md", "readme"
    }
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
Instructions:
    • Use proper Markdown heading levels to reflect section structure.
    • Preserve key formatting: headings, bullet points, code blocks, and any tables.
    • Convert visually styled headers (surrounded by #, -, *, or similar characters) to proper Markdown format.
    • Italicize journal names.
    • Do not rephrase or rewrite the content. Preserve the original wording as closely as possible.
    • Remove any characters or symbols that do not make sense in the context of Markdown.
    • Do not wrap the final result in code blocks or triple backticks.

Final Task:
    • At the very end of the file, add a changelog entry: {current_date} – Standardized to Markdown.
    • If there are any entries near the end of the file that begin with a date (in formats like YYYYMMDD, YYYY-MM-DD, or Month Year), treat them as part of a changelog and follow the same format.
    • If no such entries exist, create a new changelog section  (but don't make a header) at the end of the file and begin with this entry.

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

# --------- USAGE EXAMPLES ---------

model_id = "138382"
zip_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/{model_id}.zip"
readme_data = extract_readme_from_zip(zip_path)
if "error" not in readme_data:
    markdown_content = convert_to_markdown(readme_data)
    updated_zip = update_zip_with_markdown(zip_path, readme_data, markdown_content, model_id)
else:
    print(f"README file not found for model {model_id} in ZIP.")

# --- For GitHub repositories ---
repo_url = f"https://github.com/ModelDBRepository/{model_id}"
dest_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/readme-reformatting/{model_id}"
clone_repo_from_github(repo_url, dest_path)
readme_data = extract_readme_from_folder(dest_path)
if "error" not in readme_data:
    markdown_content = convert_to_markdown(readme_data)
    update_readme_file(dest_path, readme_data, markdown_content)
else:
    print("README file not found in repository.")