#!/usr/bin/env python3
"""
medical-literature-ai — PubMed query or list of papers →
AI-synthesized evidence summary with consensus, conflicts, gaps, and quality scores
"""
import anthropic, json, re, sys, urllib.request, urllib.parse
from pathlib import Path

SYSTEM = """You are a systematic reviewer and clinical research methodologist.
Synthesize the provided medical literature into a structured evidence summary.

Focus on: strength of evidence, consensus vs controversy, clinical applicability, gaps.
Be scientifically rigorous — distinguish association from causation, note study limitations.

Return ONLY valid JSON — no markdown, no explanation.

{
  "query": "research question or topic",
  "papers_analyzed": number,
  "synthesis_date": "YYYY-MM or null",
  "clinical_question": "PICO-formatted question if possible",
  "executive_summary": "3-4 sentence summary of what the evidence shows",
  "evidence_quality": {
    "overall_grade": "A|B|C|D",
    "grade_explanation": "why this grade",
    "study_types_found": ["RCT","observational","meta-analysis","case_series","..."],
    "sample_sizes": "range or typical",
    "follow_up_durations": "typical follow-up across studies"
  },
  "key_findings": [
    {
      "finding": "specific finding",
      "evidence_strength": "strong|moderate|weak|conflicting",
      "papers_supporting": number,
      "clinical_significance": "high|medium|low",
      "effect_size": "string or null",
      "confidence_interval": "string or null"
    }
  ],
  "consensus": ["areas where evidence is consistent across studies"],
  "controversies": [
    {
      "topic": "contested area",
      "position_a": "one side of the debate",
      "position_b": "other side",
      "resolution": "current state of evidence"
    }
  ],
  "clinical_implications": [
    {
      "recommendation": "actionable clinical recommendation",
      "strength": "strong|conditional|weak",
      "evidence_basis": "what it's based on"
    }
  ],
  "limitations": ["key limitations across the literature"],
  "research_gaps": ["important unanswered questions"],
  "population_notes": ["which populations are under-studied or have different outcomes"],
  "safety_signals": ["any safety concerns raised across studies"],
  "key_papers": [
    {
      "citation": "Author et al., Journal, Year",
      "why_important": "what makes this paper key",
      "pmid": "string or null"
    }
  ],
  "plain_language_summary": "3-4 sentences a patient could understand",
  "confidence": 0.0
}"""

def search_pubmed(query: str, max_results: int = 10) -> list[dict]:
    """Fetch abstracts from PubMed E-utilities API."""
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    search_url = f"{base}/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}&retmode=json"
    req = urllib.request.Request(search_url, headers={"User-Agent":"medical-literature-ai/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        ids = json.loads(r.read())["esearchresult"]["idlist"]
    if not ids: return []
    fetch_url = f"{base}/efetch.fcgi?db=pubmed&id={','.join(ids)}&rettype=abstract&retmode=text"
    req2 = urllib.request.Request(fetch_url, headers={"User-Agent":"medical-literature-ai/1.0"})
    with urllib.request.urlopen(req2, timeout=20) as r:
        text = r.read().decode("utf-8", errors="replace")
    return [{"raw": text}]

def synthesize(source: str, query: str = "") -> dict:
    client = anthropic.Anthropic()

    if source.startswith("pubmed:") or (not Path(source).exists() and not source.startswith("http") and len(source) < 200):
        term = source.replace("pubmed:","") if source.startswith("pubmed:") else source
        print(f"Searching PubMed for: {term}", file=sys.stderr)
        papers = search_pubmed(term, max_results=15)
        if not papers:
            print("No papers found on PubMed. Proceeding with general knowledge synthesis.", file=sys.stderr)
            text = f"Synthesize evidence on: {term}"
        else:
            text = papers[0]["raw"][:50000]
        prompt = f"Research question: {term}\n\nPubMed abstracts:\n{text}"
    elif Path(source).exists():
        text = Path(source).read_text(encoding="utf-8",errors="replace")[:50000]
        prompt = f"Research question: {query or 'see abstracts'}\n\nAbstracts/papers:\n{text}"
    else:
        text = source[:50000]
        prompt = f"Research question: {query or 'see text'}\n\nLiterature:\n{text}"

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=4096, system=SYSTEM,
        messages=[{"role":"user","content":f"Synthesize this medical literature:\n\n{prompt}"}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

GRADE_C = {"A":"\033[92m","B":"\033[92m","C":"\033[93m","D":"\033[91m"}
R = "\033[0m"
STR_ICON = {"strong":"🟢","moderate":"🟡","weak":"🟠","conflicting":"🔴"}

def print_synthesis(r: dict):
    eq = r.get("evidence_quality",{})
    g = eq.get("overall_grade","?")
    print(f"\n{'═'*60}")
    print(f"  MEDICAL LITERATURE SYNTHESIS")
    print(f"  Topic: {r.get('query','?')}")
    print(f"  Papers: {r.get('papers_analyzed','?')} | Evidence grade: {GRADE_C.get(g,'')}{g}{R}")
    print(f"{'═'*60}")
    print(f"\n  {r.get('executive_summary','')}")

    findings = r.get("key_findings",[])
    if findings:
        print(f"\n  KEY FINDINGS")
        for f in findings:
            icon = STR_ICON.get(f.get("evidence_strength","weak"),"•")
            print(f"\n  {icon} {f.get('finding','')}")
            print(f"     Strength: {f.get('evidence_strength','')} | Significance: {f.get('clinical_significance','')}")
            if f.get("effect_size"): print(f"     Effect size: {f['effect_size']}")

    consensus = r.get("consensus",[])
    if consensus:
        print(f"\n{'─'*60}\n  CONSENSUS (consistent evidence)")
        for c in consensus: print(f"  ✓ {c}")

    controversies = r.get("controversies",[])
    if controversies:
        print(f"\n{'─'*60}\n  CONTROVERSIES")
        for c in controversies:
            print(f"\n  ⚡ {c.get('topic','')}")
            print(f"     A: {c.get('position_a','')}")
            print(f"     B: {c.get('position_b','')}")
            print(f"     Current view: {c.get('resolution','')}")

    recs = r.get("clinical_implications",[])
    if recs:
        print(f"\n{'─'*60}\n  CLINICAL RECOMMENDATIONS")
        for rec in recs:
            strength = {"strong":"🟢","conditional":"🟡","weak":"🟠"}.get(rec.get("strength","weak"),"•")
            print(f"  {strength} {rec.get('recommendation','')}")
            print(f"     Basis: {rec.get('evidence_basis','')}")

    gaps = r.get("research_gaps",[])
    if gaps:
        print(f"\n  Research gaps:")
        for g2 in gaps[:4]: print(f"  ○ {g2}")

    print(f"\n  Plain language: {r.get('plain_language_summary','')}")

    safety = r.get("safety_signals",[])
    if safety:
        print(f"\n  ⚠ Safety signals:")
        for s in safety: print(f"  ! {s}")

    print(f"\n  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Synthesize medical literature from PubMed or files")
    p.add_argument("source", help="PubMed search query, file path, or 'pubmed:query'")
    p.add_argument("--query","-q",default="",help="Explicit research question")
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    r = synthesize(a.source, a.query)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_synthesis(r)
