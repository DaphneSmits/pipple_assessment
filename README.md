# Pippify ticket classification

## Oplossing en aanpak

Supporttickets van Pippify worden automatisch beoordeeld door Claude (`claude-haiku-5-5`) op drie velden:

- **category**: `technical`, `billing`, `account`, `feature_request`, `general_question`, `other`
- **priority**: `low`, `medium`, `high`, `critical`
- **effort**: `low`, `medium`, `high`

Aanpak:

1. **Classificatie** ([src/claude_client.py](src/claude_client.py)): een Nederlandse systeemprompt beschrijft per veld beslisregels die van boven naar beneden worden doorlopen. Via structured output (Pydantic-model `TicketAssessment`) geeft Claude altijd een geldige, vaste structuur terug in plaats van vrije tekst.
2. **Evaluatie** ([src/evaluate.py](src/evaluate.py)): een handmatig gelabelde set van 50 tickets ([data/eval_set.csv](data/eval_set.csv)) wordt door Claude geclassificeerd. Het script toont per veld de nauwkeurigheid en alle tickets waarop Claude afwijkt van het label. 

## Installatie

Vereisten: Python 3.12 en een Anthropic API-key.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

Maak een `.env` aan op basis van het voorbeeld en vul je API-key in:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Draaien

### Tickets uit een CSV classificeren (het bestand moet een kolom `message` hebben):

```bash
python src/claude_client.py data/tickets.csv
```

Genereert het bestand `data/tickets_classified.csv`, dat alle oorspronkelijke kolommen bevat plus `category_claude`, `priority_claude` en `effort_claude`.

### De evaluatie tegen de handmatig gelabelde set draaien:

```bash
python src/evaluate.py
```

### Een los bericht classificeren:

```bash
cd src
python -c "from claude_client import send_ticket; print(send_ticket('Ik kan niet meer inloggen, dringend!'))"
```
