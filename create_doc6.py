from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

TITLE = "Reflection on Dr. Dharmendra Mishra's Lecture on Commercial Food Manufacturing"

SECTIONS = [
    (
        "Implications for Education",
        [
            "I left this lecture convinced that the hardest knowledge in food manufacturing "
            "cannot be handed over in a classroom. Dr. Mishra described the aseptic particulate "
            "line he worked on at Gerber, which reached commercial production in 2014 after six "
            "years of pilot validation and FDA approvals. He could drop a thermocouple into "
            "flowing chocolate milk and know its "
            "temperature, but once a solid particle moves through the tube there is no way to "
            "measure the temperature inside it. So the team had to invent a different way of "
            "proving the process was safe. Nobody reads their way to that. You learn it next to "
            "a pilot plant with a regulator asking questions.",

            "That changes what I think a food science department is for. The teaching that struck "
            "me most was not the degree programs. It was the four day aseptic processing course "
            "capped at roughly 75 industry professionals a year, the Better Process Control "
            "School, and the more than 100 FDA inspectors the department trains each year. "
            "The people being educated are already employed, and some of them are the "
            "regulators. The department sits between industry and government and supplies both.",

            "The capacity still bothers me. Dr. Mishra named workforce as one of five forces "
            "reshaping the field, and said plants lose trained people every two or three years. "
            "If training really is the only answer to that churn, 75 seats a year is triage, not "
            "a solution. I also wonder what a short intensive course produces: "
            "someone who understands why a process holds, or someone who follows a procedure "
            "correctly until something unusual happens. The difference only shows up during a "
            "deviation. We were told undergraduates from this program reach full job placement, "
            "which tells me the real limit is training capacity.",
        ],
    ),
    (
        "Implications for Work, Business, and the Economy",
        [
            "The cost figures reframed the economics for me. Dr. Mishra said a retort plant can be "
            "stood up for roughly a million dollars, while a small aseptic system runs upward of "
            "40 to 50 million, and an aseptic bottle filling machine alone costs around 10 "
            "million. His slides put the aseptic packaging market near 71 billion dollars in "
            "2024, with projections approaching 179 billion by 2033. The fastest growing part of "
            "the category is also the part almost no newcomer can enter. That tells me where the "
            "power sits, and it is not with the person holding a great formulation.",

            "It also explains why his entrepreneurship work looks the way it does. The route he "
            "laid out runs from business plan to co manufacturer, with a first run of maybe "
            "50,000 units for a local Walmart or Sam's Club. Almost none of that involves owning "
            "equipment. The entrepreneur rents capability, and the Food Entrepreneurship and "
            "Manufacturing Institute exists to make that renting possible. He agreed "
            "that food startups follow the medical device pattern of being built to be acquired, "
            "and pointed to Olipop, which grew on its own and was then bought by a large "
            "beverage company.",

            "I found that honest and slightly uneasy at once. The department also connects "
            "entrepreneurs with manufacturers like Nestle, Coke, and Pepsi, who watch what comes "
            "through. Calling this entrepreneurship support is accurate, but it also works as an "
            "outsourced research pipeline for incumbents, and everyone involved seems to know "
            "it. Dr. Mishra called the food industry traditional "
            "and said a new technology usually spends 30 to 40 years in research and "
            "commercialization before it reaches a shelf. No venture fund waits that long, and "
            "that mismatch may decide which food technologies arrive more than any technical "
            "barrier.",
        ],
    ),
    (
        "Implications for Me, Other People, and Society",
        [
            "What stayed with me is that the industry does not aim for sterility. Complete "
            "sterility, Dr. Mishra said, would mean burning the product, so the target is "
            "commercial sterility: safe to eat, and stable through its stated shelf life. Risk "
            "is not eliminated. It is quantified and then accepted. In a shelf stable low acid "
            "product the organism he worried about is Clostridium botulinum, and the amount of "
            "its toxin needed to paralyze a person is measured in nanograms. Liquid infant "
            "formula sits in the highest risk tier because microorganisms need water to grow, "
            "which a powder denies them. Most of us buy these products with no idea that "
            "calculation is underneath.",

            "He asked us to hold the ultra processed food question in mind, and it did "
            "complicate my thinking. The same milk pasteurized at 72 degrees Celsius "
            "for 15 seconds keeps about two weeks, while sterilizing it at 138 degrees for two "
            "seconds buys two to three months with no preservatives added. Retort processing, he "
            "said, can cost 30 to 40 percent of a product's vitamin C where aseptic might cost "
            "5 percent. By that logic more processing can mean safer and more "
            "nutritious food, the reverse of how the word gets used publicly. I am not fully "
            "persuaded, because what people object to is usually formulation rather than thermal "
            "treatment, and he noted the rush to push protein into everything without going into "
            "it. Those two questions get argued as if they were one.",
        ],
    ),
    (
        "Personal Takeaways and Highlights",
        [
            "This lecture landed differently because I worked in human resources at Nestle. When "
            "Dr. Mishra held up a bottle of Boost and said it was a Nestle product, I realized I "
            "had spent my time inside a food company without once thinking about how its food "
            "was made. My work was people, policy, and hiring, and manufacturing was sites on an "
            "org chart and employees with shift patterns. Listening to him "
            "walk through pH thresholds, fillers, validation, and the scrutiny applied to an "
            "infant product, I saw that I had treated the technical core of the business as "
            "scenery.",

            "My analytics training gives me a second way in. He said modern plants are heavily "
            "digitized, and that you can walk into one and find two people watching an entire "
            "production run. That is a lot of judgment resting on instrumentation, which is also "
            "why he raised a recent ransomware attack at a beverage plant. What I keep returning "
            "to is measurement. In talent analytics I was usually inferring something I could "
            "not observe directly from data that was merely close enough. Process validation is "
            "the same exercise with much less room to be approximately right.",

            "The takeaway I will keep is about what a large company takes for granted. A "
            "multinational has validated processes, regulatory staff, co manufacturing "
            "relationships, and the capital for a 10 million dollar filler. Someone with a "
            "recipe their family loves has the recipe. Everything in between is the gap this "
            "institute tries to close, and until this lecture I had only seen it from the side "
            "that already had all of it.",
        ],
    ),
]

FORBIDDEN = ["-", "\u2010", "\u2011", "\u2012", "\u2013", "\u2014", "\u2015", "\u2212"]


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

    doc.save("Reflection_Paper_Oct1_Dharmendra_Mishra.docx")


def verify():
    doc = Document("Reflection_Paper_Oct1_Dharmendra_Mishra.docx")
    texts = [p.text for p in doc.paragraphs]
    joined = "\n".join(texts)

    for char in FORBIDDEN:
        assert char not in joined, "found forbidden character %r" % char

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
