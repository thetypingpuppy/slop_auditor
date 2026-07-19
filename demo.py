import spacy
from nltk.corpus import wordnet
from spacy_layout import spaCyLayout
import fitz
import re

from collections import Counter


def extract_text_from_pdf(doc):
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_headers_by_size(doc, size_tolerance=1.5):

    headers = []
    contents = {}

    all_sizes = []

    # First pass: Gather all font sizes to find the body text baseline
    for page in doc:
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        # Round to smooth out tiny anti-aliasing variations
                        all_sizes.append(round(span["size"], 1))

    if not all_sizes:
        print("No text found in PDF.")
        return

    # Determine body text size (most common size used in the PDF)
    size_counts = Counter(all_sizes)
    body_size = size_counts.most_common(1)[0][0]
    header_threshold = body_size + size_tolerance

    print(f"Detected Body Text Size: {body_size} pt")
    print(f"Extracting headers larger than: {header_threshold} pt\n")

    # Second pass: Extract elements matching the header threshold
    current_header = None
    for page_num, page in enumerate(doc, start=1):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            txt = ""

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    size = span["size"]
                    if "Nimbus" not in span["font"]:
                        continue

                    if text and size >= header_threshold:
                        headers.append(text)
                        current_header = text

                    elif current_header:
                        if current_header not in contents:
                            contents[current_header] = []
                            # txt = ""
                        if txt:
                            if txt[-1] != " " and span["text"][0] != " ":
                                txt += " "
                        txt += span["text"]

            if current_header and current_header in contents and txt:
                contents[current_header].append(txt)  # += "\n\n"

    # This section fixes the issue of dashes being used to extent long words onto the next line
    for header in contents:

        pattern = r"([a-z])- ([a-z])"

        for header in contents:
            for i, paragraph in enumerate(contents[header]):

                contents[header][i] = re.sub(pattern, r"\1\2", contents[header][i])

    # doc.close()
    # Determine body text size (most common size used in the PDF)
    # size_counts = Counter(all_sizes)
    return headers, contents


def separate_tables(doc):

    all_tables = []

    for page in doc:  # Select the first page

        # Search for tables on the page
        tables = page.find_tables()

        for table in tables:
            # Get the first table found and convert it to a Pandas DataFrame
            all_tables.append(table)  # .to_pandas()

            bbox = table.bbox

            # 2. Add a redaction over the table area
            page.add_redact_annot(bbox)

            # 3. Apply the redactions to permanently clear the text layer
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

            # print(df)

    return all_tables


nlp = spacy.load("en_core_web_sm")


with fitz.open("HighShelfShort.pdf") as doc:
    tables = separate_tables(doc)
    headers, contents = extract_headers_by_size(doc)
    raw_text = extract_text_from_pdf(doc)


# re.findall(pattern, raw_text)
print("")
nlp_text = nlp(raw_text)
# def get_antonyms(word):
#     antonyms = []
#     for syn in wordnet.synsets(word):
#         for l in syn.lemmas():
#             if l.antonyms():
#                 antonyms.append(l.antonyms()[0].name())
#     return set(antonyms)


# def is_negated(token):
#     # Check if a token has a "neg" dependency (e.g., "not", "n't")
#     for child in token.children:
#         if child.dep_ == "neg":
#             return True
#     return False


# def simple_contradiction(text1, text2):
#     doc1 = nlp(text1)
#     doc2 = nlp(text2)

#     # Simple rule: if both share the same ROOT verb but one is negated and the other isn't
#     root1 = [token.lemma_ for token in doc1 if token.pos_ == "VERB"][0]
#     root2 = [token.lemma_ for token in doc2 if token.pos_ == "VERB"][0]

#     if root1 == root2:
#         n1 = any(is_negated(token) for token in doc1 if token.lemma_ == root1)
#         n2 = any(is_negated(token) for token in doc2 if token.lemma_ == root2)
#         if n1 != n2:
#             return True
#     return False


# print(simple_contradiction("The team won.", "The team did not win."))
