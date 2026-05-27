from pathlib import Path

root = Path(r"c:\Users\S06C2~1.PAN\AppData\Local\Temp")
needles = ["маневич", "реактив", "северная", "втб", "сбер"]
found = []
for p in root.glob("*.pdf"):
    name = p.name.casefold()
    score = sum(1 for n in needles if n in name)
    if score >= 2 or any(k in name for k in ["маневич", "реактив", "северная"]):
        found.append((score, p))

for score, p in sorted(found, reverse=True):
    out = Path("_pdf_check_result.txt")
    with out.open("a", encoding="utf-8") as f:
        f.write(f"{score}\t{p}\n")
