"""Generate a presentation-friendly animated architecture flow diagram."""

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


OUTPUT_PATH = Path(__file__).with_name("architecture-flow.gif")
WIDTH, HEIGHT = 1600, 900

BACKGROUND = "#F5F7FB"
NAVY = "#172033"
MUTED = "#5D6878"
PENDING_FILL = "#FFFFFF"
PENDING_BORDER = "#CAD2DF"
ACTIVE_FILL = "#E8F0FF"
ACTIVE_BORDER = "#3563E9"
COMPLETE_FILL = "#EAF7EF"
COMPLETE_BORDER = "#238653"
ARROW_PENDING = "#B8C1CE"
ARROW_COMPLETE = "#238653"
WHITE = "#FFFFFF"

FONT_DIR = Path("C:/Windows/Fonts")
REGULAR = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 25)
SMALL = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 21)
TITLE = ImageFont.truetype(str(FONT_DIR / "seguisb.ttf"), 48)
SUBTITLE = ImageFont.truetype(str(FONT_DIR / "segoeui.ttf"), 25)
NODE_TITLE = ImageFont.truetype(str(FONT_DIR / "seguisb.ttf"), 27)
STEP_TITLE = ImageFont.truetype(str(FONT_DIR / "seguisb.ttf"), 29)
BADGE = ImageFont.truetype(str(FONT_DIR / "seguisb.ttf"), 21)


NODES = [
    {
        "number": "1",
        "title": "User question",
        "detail": "Employee asks a policy question",
        "position": (90, 245, 390, 410),
    },
    {
        "number": "2",
        "title": "Streamlit UI",
        "detail": "Captures the question and displays evidence",
        "position": (470, 245, 770, 410),
    },
    {
        "number": "3",
        "title": "Retriever Agent",
        "detail": "LangGraph starts controlled retrieval",
        "position": (850, 245, 1150, 410),
    },
    {
        "number": "4",
        "title": "MCP knowledge access",
        "detail": "Reads only approved source documents",
        "position": (1230, 245, 1530, 410),
    },
    {
        "number": "5",
        "title": "Vector search",
        "detail": "Chroma returns the most relevant chunks",
        "position": (1230, 510, 1530, 675),
    },
    {
        "number": "6",
        "title": "Response Agent",
        "detail": "Ollama creates a grounded answer",
        "position": (850, 510, 1150, 675),
    },
    {
        "number": "7",
        "title": "Evaluator Agent",
        "detail": "RAGAS scores grounding and relevance",
        "position": (470, 510, 770, 675),
    },
    {
        "number": "8",
        "title": "Decision and result",
        "detail": "Retry low scores or return the answer",
        "position": (90, 510, 390, 675),
    },
]

STEP_MESSAGES = [
    "The user asks a question through the browser or command line.",
    "The interface submits the question to the LangGraph workflow.",
    "The Retriever Agent coordinates controlled knowledge retrieval.",
    "The MCP server securely reads the approved enterprise documents.",
    "Embeddings and Chroma identify the most relevant context.",
    "The Response Agent asks Ollama to answer only from that context.",
    "The Evaluator Agent uses RAGAS to measure answer quality.",
    "Good scores return the answer; low scores trigger another retrieval.",
]


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def centered_text(
    draw: ImageDraw.ImageDraw,
    area: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    max_chars: int,
    line_gap: int = 5,
) -> None:
    lines = wrap(text, width=max_chars)
    heights = [text_size(draw, line, font)[1] for line in lines]
    total_height = sum(heights) + line_gap * (len(lines) - 1)
    y = area[1] + (area[3] - area[1] - total_height) / 2
    for line, height in zip(lines, heights, strict=True):
        width, _ = text_size(draw, line, font)
        x = area[0] + (area[2] - area[0] - width) / 2
        draw.text((x, y), line, font=font, fill=fill)
        y += height + line_gap


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    fill: str,
) -> None:
    draw.line((start, end), fill=fill, width=7)
    if start[0] == end[0]:
        direction = 1 if end[1] > start[1] else -1
        points = [
            (end[0], end[1]),
            (end[0] - 12, end[1] - direction * 18),
            (end[0] + 12, end[1] - direction * 18),
        ]
    else:
        direction = 1 if end[0] > start[0] else -1
        points = [
            (end[0], end[1]),
            (end[0] - direction * 18, end[1] - 12),
            (end[0] - direction * 18, end[1] + 12),
        ]
    draw.polygon(points, fill=fill)


def draw_node(
    draw: ImageDraw.ImageDraw,
    node: dict,
    state: str,
) -> None:
    x1, y1, x2, y2 = node["position"]
    if state == "active":
        fill, border = ACTIVE_FILL, ACTIVE_BORDER
        badge_fill = ACTIVE_BORDER
    elif state == "complete":
        fill, border = COMPLETE_FILL, COMPLETE_BORDER
        badge_fill = COMPLETE_BORDER
    else:
        fill, border = PENDING_FILL, PENDING_BORDER
        badge_fill = PENDING_BORDER

    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=22,
        fill=fill,
        outline=border,
        width=5 if state == "active" else 3,
    )
    draw.ellipse((x1 + 18, y1 + 18, x1 + 62, y1 + 62), fill=badge_fill)
    number_width, number_height = text_size(draw, node["number"], BADGE)
    draw.text(
        (
            x1 + 40 - number_width / 2,
            y1 + 40 - number_height / 2 - 2,
        ),
        node["number"],
        font=BADGE,
        fill=WHITE,
    )
    centered_text(
        draw,
        (x1 + 22, y1 + 62, x2 - 22, y1 + 112),
        node["title"],
        NODE_TITLE,
        NAVY,
        25,
    )
    centered_text(
        draw,
        (x1 + 24, y1 + 108, x2 - 24, y2 - 16),
        node["detail"],
        SMALL,
        MUTED,
        34,
    )


def build_frame(active_index: int) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.text((90, 62), "Enterprise Knowledge Assistant", font=TITLE, fill=NAVY)
    draw.text(
        (92, 127),
        "Simplified end-to-end flow",
        font=SUBTITLE,
        fill=MUTED,
    )

    progress_x1, progress_y = 92, 190
    progress_width = 1438
    draw.rounded_rectangle(
        (progress_x1, progress_y, progress_x1 + progress_width, progress_y + 12),
        radius=6,
        fill="#DDE3EC",
    )
    completed_width = int(progress_width * (active_index + 1) / len(NODES))
    draw.rounded_rectangle(
        (progress_x1, progress_y, progress_x1 + completed_width, progress_y + 12),
        radius=6,
        fill=ACTIVE_BORDER,
    )

    connections = [
        ((390, 327), (456, 327)),
        ((770, 327), (836, 327)),
        ((1150, 327), (1216, 327)),
        ((1380, 410), (1380, 496)),
        ((1230, 592), (1164, 592)),
        ((850, 592), (784, 592)),
        ((470, 592), (404, 592)),
    ]
    for index, (start, end) in enumerate(connections):
        color = ARROW_COMPLETE if index < active_index else ARROW_PENDING
        arrow(draw, start, end, color)

    for index, node in enumerate(NODES):
        if index < active_index:
            state = "complete"
        elif index == active_index:
            state = "active"
        else:
            state = "pending"
        draw_node(draw, node, state)

    draw.rounded_rectangle(
        (90, 735, 1530, 840),
        radius=20,
        fill=WHITE,
        outline=ACTIVE_BORDER,
        width=3,
    )
    draw.text(
        (122, 758),
        f"Step {active_index + 1} of {len(NODES)}",
        font=STEP_TITLE,
        fill=ACTIVE_BORDER,
    )
    draw.text(
        (122, 801),
        STEP_MESSAGES[active_index],
        font=REGULAR,
        fill=NAVY,
    )
    return image


def main() -> None:
    frames = [build_frame(index) for index in range(len(NODES))]
    durations = [1300] * (len(frames) - 1) + [2500]
    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
