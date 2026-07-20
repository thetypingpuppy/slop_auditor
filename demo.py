import json
import pathlib

from section_functions import *

PAPER_PDF = "workspace_constraints.pdf"
paper_json = pathlib.Path(PAPER_PDF).with_suffix(".json")

if paper_json.exists():

    with open(paper_json) as f:
        sections = json.load(f)

else:

    sections = extract_sections_from_pdf(PAPER_PDF)
    sections = summarise_sections_using_gemini(sections)

    # Cache results to avoid unnecessary queries
    with open(paper_json, "w") as f:
        json.dump(sections, f, indent=4)

## Check for contradictions
check_sections_for_contradictions(sections)
print("DONE")
