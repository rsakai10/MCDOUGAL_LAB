import openai
import os
import requests
import zipfile
import shutil
import tempfile
import datetime
import random
import json
import re
import random
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

def update_zip_with_markdown(original_zip_path, readme_data, markdown_content):
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
        old_path = os.path.join(target_folder, readme_data["format"])
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

model_id = "138382"  # Example model ID
zip_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/model_{model_id}.zip"
readme_data = extract_readme_from_zip(zip_path)
if "error" not in readme_data:
    markdown_content = convert_to_markdown(readme_data)
    new_readme_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/readme-reformatting/{model_id}_README.md"
    with open(new_readme_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
        print(f"README file converted for model {model_id} at {new_readme_path}.")
else:
    print(f"README file not found for model {model_id}.")

# # Example usage:
# # Fetch the list of all model IDs from ModelDB
# response = requests.get("https://modeldb.science/api/v1/models")
# if response.status_code == 200:
#     all_ids = response.json()
#     random_model_ids = random.sample(all_ids, 20)
#     print(f"Randomly selected model IDs: {random_model_ids}")
# else:
#     raise Exception("Failed to fetch model list.")

# # Example: process each random model
# for model_id in random_model_ids:
#     zip_path = f"/Users/riesakai/Desktop/MCDOUGAL_LAB/model_{model_id}.zip"
#     zip_path = download_model_zip(model_id, zip_path)
#     readme_data = extract_readme_from_zip(zip_path)

#     if "error" not in readme_data:
#         markdown_content = convert_to_markdown(readme_data)
#         #update_zip_with_markdown(zip_path, readme_data, markdown)
#         # Save new README.md inside the detected folder
#         new_readme_path = os.path.join(f"{model_id}_README.md")
#         with open(new_readme_path, "w", encoding="utf-8") as f:
#             f.write(markdown_content)

#     else:
#         print(f"README file not found for model {model_id}.")

