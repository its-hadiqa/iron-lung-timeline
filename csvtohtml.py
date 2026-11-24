# script to turn timelines.csv into a webpage
# the csv is assembled from Simon's Injuries Masterlist and Iron Lung Timestamp Breakdown
# both from Iron Lung Master Reference https://drive.google.com/drive/folders/1oTalXMdAi_uw0995qGEgebZnRjqnfHJE

import csv, html, pathlib

# popup for displaying captures upon clicking their name
popup = """<dialog id="viewer">
<form method="dialog"><button class="close" aria-label="Close">&#10005;</button></form>
<h3 id="viewer-title"></h3>
<img id="viewer-img" alt="">
</dialog>"""

# header with description and credits
header = """<header>
<img src="iron-lung-logo.webp" alt="Iron Lung">
<h1>TIMELINE OF MARKIPLIER’S MOVIE</h1>
<p>unofficial / created by <b><a href="https://www.tumblr.com/the-hadiqa">the-hadiqa</a></b></p>
<p>assembled from the timestamp breakdown by <b><a href="https://www.tumblr.com/negative-pressure-ventilator">negative-pressure-ventilator</a></b> and the injuries masterlist by <b><a href="https://www.tumblr.com/ctrl-shift-alt-9">ctrl-shift-alt-9</a>, <a href="https://www.tumblr.com/tabletoptime">tabletoptime</a></b>, ji, dusty and <b><a href="https://www.tumblr.com/water-activated-light">water-activated-light</a></b>. all materials are from <b><a href="https://drive.google.com/drive/folders/1oTalXMdAi_uw0995qGEgebZnRjqnfHJE">the master reference</a></b> curated by ctrl-shift-alt-9. thanks y’all.</p>
<p>not finished yet, excuse the mess ;)</p>
</header>"""

csvpath = "timeline.csv" # input csv
outpath = pathlib.Path("timeline.html") # output html
capturespath = "captures" # folder with images

# names of the files that really exist in the captures folder
# some filenames in csv don't actually have associated files
existing = {p.name for p in pathlib.Path(capturespath).iterdir()}

# these keep their linebreaks, but Context: doesn't bc it has them after just a few words (=very short lines)
listlabels = {"Symptoms:", "Complications:", "Contributor:"}

# converts text as it was in the csv to text with basic html sectioning
def texttohtml(text, injury=False):
    # replace weird windows newlines with plain ones, remove empty paragraphs
    paragraphs = [p for p in text.replace("\r\n", "\n").split("\n\n") if p.strip()]
    out = []
    for p in paragraphs:
        lines = p.strip().split("\n")
        # the injury masterlist was hard-wrapped every ~40 characters
        # so outside of the real lists, glue the lines back together into running text
        if injury and lines[0].strip() not in listlabels:
            label = [lines.pop(0)] if lines[0].strip().endswith(":") else [] # "Treatment:" stays on its own line
            lines = label + [" ".join(l.strip() for l in lines).replace("/ ", "/")] # "liver/spleen/" + "pancreas" has no space
        # <br> = linebreak inside cell
        # <p> = blank line inside cell
        out.append("<p>" + "<br>\n".join(html.escape(line) for line in lines) + "</p>")
    return "\n".join(out)

# turns lists of captures in the csv into links that display a popup with that image
def pictureshtml(cell, capturespath):
    parts = []
    # some cells have multiple images, joined with -
    for name in (n.strip() for n in cell.split("-")):
        label = html.escape(name)
        image = name + ".png"
        # ???.DCM = original timestamp breakdown didnt have the file name, or there is no file for this number = no link
        if "?" in name or image not in existing: parts.append(f'<span class="nofile">{label}</span>')
        # link to popup
        else: parts.append(f'<a class="capture" href="{capturespath}/{html.escape(image)}" data-title="{label}">{label}</a>')
    return " ".join(parts)


def tagshtml(cell):
    # tags are comma separated bc some have hyphens (SM-13)
    tags = [t.strip() for t in cell.split(",") if t.strip()]
    if not tags: return ""
    # list of tags at timestamp
    return '<ul class="tags" aria-label="Tags">\n' + "\n".join(f"<li>{html.escape(t)}</li>" for t in tags) + "\n</ul>" 



def entryhtml(row, entryid, capturespath):
    # output html
    # <article> = a self contained section (ie one timestamp and all its associated material)
    # stylesheet hooks onto class names
    out = [f'<article id="{entryid}">', f'<h3><a href="#{entryid}">{html.escape(row["Timestamp"])}</a></h3>']
    # subsections of timestamp
    if row["Event"].strip(): out.append(f'<div class="event">{texttohtml(row["Event"])}</div>')
    if row["Sub-Event"].strip():
        # injury cards get an extra class so css can style them in red
        injury = row["Sub-Event"].strip().startswith("Context:")
        kind = "subevent injury" if injury else "subevent"
        out.append(f'<div class="{kind}">{texttohtml(row["Sub-Event"], injury)}</div>')
    if row["Dialogue"].strip():
        speaker = f'<strong class="who">{html.escape(row["Speaker"].strip())} /</strong> ' if row["Speaker"].strip() else ""
        out.append(f'<p class="line">{speaker}{html.escape(row["Dialogue"].strip())}</p>')
    elif row["Speaker"].strip(): out.append(f'<p class="line"><strong class="who">{html.escape(row["Speaker"].strip())}</strong></p>')
    if row["Picture"].strip(): out.append(f'<div class="pics">{pictureshtml(row["Picture"], capturespath)}</div>')
    # tags for each timstamp
    tags = tagshtml(row["Tags"])
    if tags: out.append(tags)
    out.append("</article>")
    return "\n".join(out)

# opens the input csv
# excel's "CSV UTF-8" = byte order mark + ; as delimiter
# newline="" keeps line breaks inside cells (descriptions of injuries etc have multiple lines)
with open(csvpath, encoding="utf-8-sig", newline="") as f: rows = list(csv.DictReader(f, delimiter=";"))

# elements of webpage, count of how often each timestamp appears (there are duplicates)
body, seen = [], {}
for row in rows:
    ts = row["Timestamp"].strip()
    row["Timestamp"] = ts
    n = seen.get(ts, 0) + 1 
    seen[ts] = n # how many times this timestamp appeared
    # 01:02:03 -> t01-02-03, if the same time repeats, add -2, -3, so every id on the page is unique
    entry_id = "t" + ts.replace(":", "-") + ("" if n == 1 else f"-{n}")
    body.append(entryhtml(row, entry_id, capturespath))

# assemble page and write as file
page = "\n".join([
    "<!DOCTYPE html>",
    '<html lang="en">',
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "<title>Iron Lung Timeline</title>",
    '<link rel="stylesheet" href="style.css">',
    '<link rel="icon" href="favicon.ico" sizes="48x48">',
    "</head>",
    "<body>",
    header,
    *body,
    popup,
    '<script src="script.js"></script>',
    "</body>",
    "</html>",
    "",
    ])
outpath.write_text(page, encoding="utf-8")