"""Send a single support ticket to Claude and get back its category, priority and effort.

Step 2 of the pipeline: Claude gets instructions (a system prompt) and must
answer in a fixed structure instead of free text.

Can also be run directly to classify every ticket in a CSV with a `message` column:

    python src/claude_client.py data/tickets.csv [-o output.csv]
"""
import argparse
from pathlib import Path
from typing import Literal

import anthropic
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

MODEL = "claude-haiku-5-5"

load_dotenv()

client = anthropic.Anthropic()

class TicketAssessment(BaseModel):
    category: Literal["technical", "billing", "account", "feature_request", "general_question", "other"]
    priority: Literal["low", "medium", "high", "critical"]
    effort: Literal["low", "medium", "high"]

SYSTEM_PROMPT = """Je bent een triage-assistent voor het klantenserviceteam van Pippify, een softwarebedrijf dat bedrijfssoftware levert aan middelgrote organisaties in de
zakelijke dienstverlening.
Je krijgt één supportticket van een klant en beoordeelt dit.

Voor elk van de volgende classificaties geldt: loop de regels van boven naar beneden; de eerste die past bepaalt de klasse.

Category: waar gaat het ticket over?
- technical: iets in de software werkt niet (crash, foutmelding, bug, traagheid, synchronisatie, uploaden, exporteren, API, storing).
- feature_request: een wens of suggestie voor nieuwe of verbeterde functionaliteit.
- billing: facturen, betalingen, kosten, btw, abonnementskosten.
- account: inloggen, wachtwoorden, tweestapsverificatie, geblokkeerde accounts, gebruikersrechten, profielinstellingen.
- general_question: een vraag om informatie of uitleg (handleidingen, integraties, beveiliging, webinars) zonder dat er iets kapot is.
- other: al het overige, zoals complimenten, algemene feedback of berichten die te vaag zijn om in te delen.

Priority: hoe snel moet support op dit ticket reageren?
- critical: De klant kan niet meer werken of er staat iets groots op het spel: het systeem ligt eruit, het werk of de productie ligt stil, er gaat data verloren, er is een beveiligingsprobleem, of de klant dreigt te vertrekken.
- high: De klant kan niet inloggen, óf de klant zegt zelf dat het dringend is (bijv. "dringend", "spoed", "urgent", "zo snel mogelijk", "per direct").
- medium: Een functie van de software werkt niet goed (foutmelding, crash, vastlopen, synchronisatie, uploaden, exporteren), maar de klant meldt het rustig.
- low: Al het overige: vragen, wensen, feedback, complimenten, af en toe wat traagheid, en factuurvragen of -fouten zonder haast.

Effort: hoeveel werk is het voor het supportteam om dit op te lossen?
- low: Support kan het zelf afhandelen met een antwoord, uitleg of kleine correctie: vragen, uitleg over functies, instellingen of accountgegevens wijzigen
- medium: Support moet uitzoeken wat er misgaat of overleggen met een andere afdeling: Inlog- en toegangsproblemen, foutmeldingen en factuurzaken.
- high: De oplossing vraagt werk van ontwikkelaars: iets in de software werkt niet (bug, crash, foutmelding, storing, traagheid, synchronisatie), of de klant wil nieuwe of verbeterde functionaliteit.

Baseer je beoordeling alleen op de inhoud van het ticket.
Gebruik voor elk veld exact één van de bovenstaande Engelse waarden."""


def send_ticket(message: str) -> TicketAssessment:
    """Send one ticket message to Claude and return its category, priority and effort."""
    response = client.messages.parse(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
        output_format=TicketAssessment,
    )

    return response.parsed_output


def classify_csv(input_file: Path, output_file: Path) -> None:
    """Classify every message in input_file and write the results to output_file.

    The output keeps all input columns and adds category_claude, priority_claude
    and effort_claude.
    """
    tickets = pd.read_csv(input_file, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
    if "message" not in tickets.columns:
        raise SystemExit(f"{input_file} has no 'message' column (found: {', '.join(tickets.columns)})")

    fields = list(TicketAssessment.model_fields)
    results = {field: [] for field in fields}
    print(f"Classifying {len(tickets)} tickets from {input_file}...")
    for i, message in enumerate(tickets["message"].fillna(""), start=1):
        answer = send_ticket(message)
        for field in fields:
            results[field].append(getattr(answer, field))
        print(f"  {i}/{len(tickets)} done")

    for field in fields:
        tickets[f"{field}_claude"] = results[field]
    tickets.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"Results written to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify support tickets in a CSV with Claude.")
    parser.add_argument("input", type=Path, help="CSV file with a 'message' column")
  
    args = parser.parse_args()

    output = args.input.with_name(f"{args.input.stem}_classified.csv")
    classify_csv(args.input, output)