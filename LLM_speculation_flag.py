import re

def is_speculation(sections):
    results = []
    speculative_words = [
        'seems to', 'appears to', 'might', 'could', 'possibly',
        'probably', 'likely', 'suggests'
    ]
    for section in sections:
        text_lower = section.lower()
        count = sum(word in text_lower for word in speculative_words)
        if count >= 2:
            results.append(f'{section}\nFLAG: SPECULATION\n')
        else:
            results.append(f'{section}\nFLAG: CORRECT\n')
    output_text = ('\n' + '-' * 60 + '\n').join(results)
    output_path = '/Users/riesakai/Desktop/MCDOUGAL_LAB/LLM_flagged.txt'
    with open(output_path, 'w') as out_file:
        out_file.write(output_text)
    return output_text


# LLM speculation flag
with open('LLM_evaluation.txt', 'r') as file:
    text = file.read()

section = text.split('-' * 60)
sections = [section.strip() for section in section if section.strip()]

# Remove all lines containing "RIE CONFIDENCE:" from each section
sections = [
    '\n'.join(
        line for line in sec.splitlines() if "RIE CONFIDENCE:" not in line
    )
    for sec in sections
]


is_speculation(sections)
