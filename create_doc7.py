import re
import unicodedata
import zipfile

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUTPUT = "Reflection_Paper_Schiff_GRAIL.docx"

TITLE = "Reflection on Drs. Daniel and Kaylyn Schiff's Lecture on AI Governance"

SECTIONS = [
    (
        "Implications for Education",
        [
            "The result I keep thinking about is the one that failed. Kaylyn Schiff said they "
            "showed half their respondents a video explaining what AI auditing involves, "
            "expecting a low information space to shift once people knew more. The "
            "videos, in English and German, changed almost nothing. She offered that against an "
            "objection some policymakers might raise, that the public is not informed enough to join "
            "these decisions. I think it cuts at educators too. We assume "
            "teaching people about a technology changes what they want from it. Here it did not.",

            "So what is education for? Not forming public preferences, I think, but "
            "training the people who act on them. Daniel Schiff mentioned in "
            "passing that they are building AI auditing courses, the piece my "
            "program is missing. I am taught to build and evaluate models. Policy courses "
            "teach regulation. Almost nothing teaches the middle. Three of the six attributes in "
            "their audit experiment are choices "
            "somebody has to make: who conducts the audit, what it examines, and whether it is "
            "completed. They said no set standard exists yet.",

            "I am not comfortable with the generous reading of that null result. One of "
            "them described students worrying about their jobs and majors and AI "
            "in classrooms, and said there is more precarity now. Stable survey "
            "preferences and anxious students are not the same public. Maybe the videos moved "
            "nobody because people had settled into positions they would not revisit, which is less flattering than principled consistency.",
        ],
    ),
    (
        "Implications for Work, Business, and the Economy",
        [
            "The headline was good news, and mostly it is. Across 3,002 adults in the "
            "United States and Germany, all three commitments they tested, public principles, an "
            "internal responsible AI team, and an independent audit, raised trust, perceived "
            "ethicality, safety, and willingness to use their products. The largest effects "
            "neared half a standard deviation, larger than they expected. "
            "What should worry anyone spending money is which signal earned the return. "
            "Teams and audits did not outperform a public statement of principles, their own "
            "caveat that cheap signaling might still work. If I am "
            "the analyst arguing for a governance budget, the market pays for the press "
            "release, not the work behind it. Their own next line answers me: signals are not "
            "actual ethicality or safety, which indicts the market, not the work. Support for regulation barely "
            "moved either, so self governing your way out of oversight does not pay.",

            "Their interviews, coded a couple of years back, say what practitioners think drives "
            "the work. Among 34 auditors and governance leads in seven countries, "
            "regulatory motives and risks topped the list at "
            "104, reputational at 69, other risks at 38, financial motives at only 22. Those "
            "are stated motives, not budgets, but I read the ordering as effort following "
            "regulation. So when one of them described Anthropic rolling out text "
            "watermarks only in the European Union to satisfy its transparency code of practice, "
            "with an opt in elsewhere, it read like a pattern. The phrase "
            "strategic adjustment came up in the same conversation. Compliance is a "
            "map, and firms draw it as narrowly as definitions allow.",

            "Ethics did move money once. After Anthropic rejected the Pentagon's terms on "
            "February 27, 2026, Claude visits rose about 30 percent on desktop and 38 percent on "
            "mobile in their conservative estimate, while ChatGPT use held steady. "
            "But frontier firms are not ordinary "
            "companies, and they called the evidence suggestive, not definitive.",
        ],
    ),
    (
        "Implications for Me, Other People, and Society",
        [
            "Two findings sit oddly together. The public rewarded commitments as much in "
            "manufacturing and ecommerce as in finance and health care, ignoring the "
            "risk distinction regulators built their structure around. Yet when the audits "
            "experiment varied the use case, concern ran highest for layoffs and lowest for spam "
            "filtering. People do have a line; it is not sector but whether the system is "
            "pointed at someone's livelihood. "
            "That makes me doubt consumer pressure as a governance mechanism. Lining up the two effects "
            "they priced, a recent scandal cost a company about 25 points, while a government "
            "auditor over a self audit was worth about 9. That 9 buys independence, not the "
            "audit itself; the largest audit effect was simply completing one, which got no "
            "point value. Still, the only penalty with a number on it is for getting caught, which a rational firm reads as a reputation problem before an "
            "engineering one.",

            "The public does know which auditor it wants: external "
            "auditors over self audits, with government agencies ranked highest. Whether "
            "one arrives is another matter, and the nearest the session came to it was a treaty "
            "question. Asked whether AI governance would ever get serious enough for a "
            "global pact, one presenter said they were cautiously pessimistic about strong "
            "international governance, likening it to climate change, where committees and voluntary "
            "agreements pile up while emissions rise. Pressed later on whether regulation "
            "works, the same presenter was more constructive: they think in layers, where "
            "international agreements may not fix everything but do something, and regulations "
            "help if they are well designed. My own read is narrower now: consumers can want an "
            "independent audit and have no way to supply one.",
        ],
    ),
    (
        "Personal Takeaways and Highlights",
        [
            "I came expecting a policy talk and left thinking about my work history. The use "
            "case the public worried about most, AI for workforce layoffs, is where I have "
            "worked. I was in human resources at Nestle and then talent analytics at "
            "Cloudflare, so the models I worked near were pointed at people: who gets "
            "hired, who gets considered, how a workforce is described to those deciding its "
            "future. I knew that was sensitive. I had not seen it top a "
            "ranked list of public concern.",

            "A backup slide they never reached sharpened that. Public "
            "sector human resources managers weighted transparency, privacy, and "
            "human oversight more heavily, while managers in both sectors cared about cost, integration, "
            "bias, and consent. That second list is the conversation I remember from talent work.",

            "The highlight was Daniel Schiff describing his responsible "
            "AI work at JPMorgan, where much of it was case making: talking to teams, building "
            "momentum, sometimes starting from a data scientist worried about algorithmic "
            "bias. That is my likely position: not the person writing regulation, not "
            "the executive announcing principles, but the analyst who notices something and decides "
            "whether to raise it. I once thought governance happened to a model after it "
            "was built. This moved it into the building, and left one question. "
            "The first experiment measured willingness to use, not actual use. Commitments "
            "changed what people said; one sharp event changed what they did. Since I "
            "will be building the thing being judged, I want to know which is the real signal.",
        ],
    ),
]

FORBIDDEN = [
    "-",
    "\u2010",
    "\u2011",
    "\u2012",
    "\u2013",
    "\u2014",
    "\u2015",
    "\u2212",
    "\u00ad",
    "\uff0d",
]


def style_run(run):
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)


def configure(paragraph, indent=True):
    pf = paragraph.paragraph_format
    pf.line_spacing = 1.15
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    if indent:
        pf.first_line_indent = Inches(0.5)


def build():
    doc = Document()

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)

    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    configure(title, indent=False)
    run = title.add_run(TITLE)
    run.bold = True
    style_run(run)

    for heading, paragraphs in SECTIONS:
        head = doc.add_paragraph()
        configure(head, indent=False)
        run = head.add_run(heading)
        run.bold = True
        style_run(run)

        for text in paragraphs:
            body = doc.add_paragraph()
            configure(body)
            style_run(body.add_run(text))

    doc.save(OUTPUT)


def scan_dashes(label, text):
    for char in FORBIDDEN:
        assert char not in text, "found forbidden character %r in %s" % (char, label)
    for char in set(text):
        assert unicodedata.category(char) != "Pd", (
            "found Unicode dash punctuation %r (U+%04X) in %s"
            % (char, ord(char), label)
        )


def verify():
    doc = Document(OUTPUT)
    texts = [p.text for p in doc.paragraphs]
    scan_dashes("extracted paragraph text", "\n".join(texts))

    with zipfile.ZipFile(OUTPUT) as archive:
        xml = archive.read("word/document.xml").decode("utf8")
    nodes = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, re.S))
    scan_dashes("word/document.xml text nodes", nodes)

    body_words = 0
    headings = {h for h, _ in SECTIONS}
    for text in texts:
        if text and text != TITLE and text not in headings:
            body_words += len(text.split())

    print("no hyphen or dash check: PASSED")
    print("body word count:", body_words)


if __name__ == "__main__":
    build()
    verify()
