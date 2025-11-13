def clean_comments(text):
    text = text.replace("sprites", "objects")
    text = text.replace("sprite", "object")
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            comment = line[1:].strip()
            if comment:
                cleaned_lines.append(comment)
    return cleaned_lines

def clean_concepts(text):
    concepts = []
    text = ",".join(clean_comments(text))
    for concept in text.split(","):
        concept = concept.strip()
        if concept:
            concepts.append(concept)
    return concepts

def clean_description(text):
    return " ".join(clean_comments(text))

def clean_code(text):
    comments = clean_comments(text)
    # plan = ""
    # for i, comment in enumerate(comments):
    #     plan += f"{i + 1}. {comment}\n"
    # return plan.strip()
    return "\n".join(comments)