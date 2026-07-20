import spacy
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from google import genai
import fitz
from collections import Counter
import re
import pymupdf4llm
from api_key import MY_API_KEY


def extract_sections_from_pdf(PAPER_PDF):

    with fitz.open(PAPER_PDF) as doc:
        # tables = separate_tables(doc)
        headers = extract_headers_by_size(doc)
        # raw_text = extract_text_from_pdf(doc)

    # re.findall(pattern, raw_text)

    md_text = pymupdf4llm.to_markdown(PAPER_PDF)

    sections = {}
    for header in headers[1:]:
        sections[header] = {}

        try:
            pattern = r"\*\*" + header + r"\*\*"
            sections[header]["start_index"] = [
                match.start() for match in re.finditer(pattern, md_text)
            ][0]

        except:
            pattern = header
            sections[header]["start_index"] = [
                match.start() for match in re.finditer(pattern, md_text)
            ][0]

    end_index = len(md_text) - 1
    for header in reversed(headers[1:]):
        start_index = sections[header]["start_index"]
        sections[header]["text"] = md_text[start_index:end_index]
        end_index = start_index

    return sections


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
                    if text == "Figure":
                        break
                    size = span["size"]
                    if "Nimbus" not in span["font"]:
                        continue

                    if text and size >= header_threshold:
                        headers.append(text)
                        current_header = text

    return headers


def summarise_sections_using_gemini(sections):

    client = genai.Client(api_key=MY_API_KEY)

    previous_interaction_id = None

    ## Gemini Queries
    for section in sections:
        query = "Summarise the following text:\n\n" + sections[section]["text"]

        interaction = client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=query,
            previous_interaction_id=previous_interaction_id,
        )
        previous_interaction_id = interaction.id

        sections[section]["gemini_summary"] = interaction.output_text

    return sections


def check_sections_for_contradictions(sections):

    nlp = spacy.load("en_core_web_md")
    model_name = "cross-encoder/nli-deberta-v3-large"
    # model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    def check_contradiction(premise, hypothesis):
        # Encode the premise and hypothesis
        inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True)

        # Get model prediction scores
        with torch.no_grad():
            logits = model(**inputs).logits

        # The model outputs logits for [Contradiction, Neutral, Entailment]
        predicted_class_id = logits.argmax().item()
        labels = ["Contradiction", "Neutral", "Entailment"]

        return labels[predicted_class_id]

    for section in sections:

        if section == "References":
            continue

        ref_doc = nlp(sections[section]["text"])
        llm_doc = nlp(sections[section]["gemini_summary"])

        ref_sentences = ref_doc.sents
        llm_sentences = llm_doc.sents

        for ref_sentence in ref_sentences:
            for llm_sentence in llm_sentences:
                ref_word_count = len(
                    [token for token in ref_sentence if not token.is_punct]
                )
                llm_word_count = len(
                    [token for token in llm_sentence if not token.is_punct]
                )

                if ref_word_count < 5:
                    continue
                if llm_word_count < 5:
                    continue

                similarity = ref_sentence.similarity(llm_sentence)
                if similarity > 0.75:
                    result = check_contradiction(ref_sentence.text, llm_sentence.text)
                else:
                    continue

                if result == "Contradiction":
                    print(
                        "REFERENCE:"
                        + ref_sentence.text
                        + "\n\n CONTRADICTS?\n\n "
                        + "LLM: "
                        + llm_sentence.text
                        + "\n----------------------------------------------------------------------------------\n"
                    )
