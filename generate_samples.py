"""Generate synthetic PDF fixtures for plagiarism detection."""

import json
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "sample_submissions"
OUT.mkdir(exist_ok=True)

PROMPT = (
    "Describe your proposed strategy and explain "
    "the expected measurable outcomes."
)

HEALTH = (
    "Community clinics can reduce diagnostic delays by using "
    "remote consultations. Patients receive early screening "
    "through mobile health applications. Local nurses coordinate "
    "follow-up appointments with specialist doctors. The proposed "
    "pilot tracks waiting time and patient satisfaction."
)

MARKET = (
    "A neighborhood retailer can improve customer retention "
    "through a membership program. Reward points encourage "
    "repeat purchases and personalized offers. Weekly sales "
    "analysis identifies which campaigns generate sustainable demand."
)

PARA = (
    "A local shop can retain shoppers by launching a loyalty "
    "scheme. Incentive credits motivate returning customers "
    "and tailored promotions. Reviewing revenue each week "
    "reveals which marketing efforts create lasting demand."
)

EXT = (
    "Rainwater harvesting captures rooftop runoff in storage tanks. "
    "Filtration removes debris before water enters the reservoir. "
    "Schools can use collected water to irrigate gardens and "
    "reduce municipal consumption."
)


def pdf(name, text):
    with fitz.open() as document:
        page = document.new_page()

        remaining = page.insert_textbox(
            fitz.Rect(50, 50, 540, 780),
            text,
            fontsize=12
        )

        if remaining < 0:
            raise ValueError("Text does not fit: " + name)

        document.save(OUT / name)


if __name__ == "__main__":

    pdf("01_health.pdf", PROMPT + "\n" + HEALTH)

    pdf("02_copy.pdf", PROMPT + "\n" + HEALTH)

    pdf(
        "03_transit.pdf",
        PROMPT + "\n"
        "Bus routes should connect peripheral neighborhoods "
        "with railway stations. Passenger counts determine peak "
        "service frequency. Electric buses reduce local exhaust emissions."
    )

    pdf(
        "04_farming.pdf",
        PROMPT + "\n"
        "Soil moisture sensors guide drip irrigation. Farmers compare "
        "crop yield across treatment plots. Seasonal rainfall "
        "informs planting schedules."
    )

    (OUT / "05_empty.pdf").write_bytes(b"")

    pdf("06_retail.pdf", PROMPT + "\n" + MARKET)

    pdf("07_paraphrase.pdf", PROMPT + "\n" + PARA)

    pdf(
        "08_ai.pdf",
        "Digital transformation enables organizations to improve "
        "operational efficiency. Strategic implementation requires "
        "collaboration across diverse business functions. Continuous "
        "evaluation supports sustainable growth and organizational "
        "adaptability. Effective leadership promotes innovation "
        "through structured change management."
    )

    pdf("09_external.pdf", EXT)

    pdf(
        "10_library.pdf",
        "Libraries can loan science kits to rural classrooms. "
        "Teachers record student experiments in notebooks. "
        "Volunteers repair broken components during monthly workshops."
    )

    reference_dir = ROOT / "reference_data"
    reference_dir.mkdir(exist_ok=True)

    (reference_dir / "rainwater.txt").write_text(EXT)

    manifest = {
        "peer_positive_pairs": [
            ["01_health.pdf", "02_copy.pdf"],
            ["06_retail.pdf", "07_paraphrase.pdf"]
        ],
        "external_positive": ["09_external.pdf"],
        "ai_generated": ["08_ai.pdf"],
        "invalid": ["05_empty.pdf"],
        "notes": (
            "All content is synthetic. The AI sample contains "
            "ChatGPT-generated text. Six PDFs contain a shared prompt."
        )
    }

    (OUT / "dataset_manifest.json").write_text(
        json.dumps(manifest, indent=2)
    )

    print("Successfully generated 10 PDF test submissions.")
