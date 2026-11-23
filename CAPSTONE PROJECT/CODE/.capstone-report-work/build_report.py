from pathlib import Path
import json
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

work = Path(__file__).resolve().parent
root = work.parent
details_file = work / "details.json"
info = json.loads(details_file.read_text(encoding="utf-8-sig")) if details_file.exists() else {}
title = "E-Commerce Marketplace Orders & Delivery Dashboard"
github = "https://github.com/MONISH-067/DBMS/tree/codex/csa0504-capstone-submission/CAPSTONE%20PROJECT/CODE"
students = ("Monish L", "Prasannakumar S")
ids = ("1972260035", "1924260253")
degree = info.get("degree", "[DEGREE]")
branch = info.get("branch", "[BRANCH / DEPARTMENT]")
month = info.get("month", "[SUBMISSION MONTH AND YEAR]")
inst = "Saveetha Institute of Medical and Technical Sciences"
doc = Document()
doc.core_properties.title = title
doc.core_properties.subject = "CSA0504 - Database Management System"
doc.core_properties.author = "Monish L and Prasannakumar S"
doc.core_properties.keywords = "Olist, MySQL, relational database, dashboard, delivery analytics"

for name, size in {"Normal":12, "Heading 1":16, "Heading 2":13, "Heading 3":12, "Caption":10}.items():
    style = doc.styles[name]
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0,0,0)
    style.paragraph_format.space_before = Pt(7 if name.startswith("Heading") else 0)
    style.paragraph_format.space_after = Pt(5)
    style.paragraph_format.line_spacing = 1.14
    fonts = style._element.get_or_add_rPr().rFonts
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        fonts.attrib.pop(qn("w:" + attr), None)
    fonts.set(qn("w:eastAsia"), "Times New Roman")
doc.styles["Normal"].paragraph_format.widow_control = True
doc.styles["Heading 1"].font.bold = True
doc.styles["Heading 2"].font.bold = True
doc.styles["Heading 3"].font.bold = True

def section(sec, fmt=None, start=None):
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.left_margin = sec.right_margin = Inches(1)
    sec.top_margin, sec.bottom_margin = Inches(0.88), Inches(0.79)
    sec.footer_distance = Inches(0.37)
    sec.footer.is_linked_to_previous = False
    if fmt is None:
        return
    n = OxmlElement("w:pgNumType")
    n.set(qn("w:fmt"), fmt)
    n.set(qn("w:start"), str(start))
    sec._sectPr.insert_element_before(n, "w:cols", "w:docGrid")
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    p._p.append(field)

def p(text="", *, style=None):
    q = doc.add_paragraph(text, style)
    apply_break(q)
    if style is None:
        q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return q

def centered(text, size=12, bold=True, before=0, after=7, italic=False):
    q = doc.add_paragraph()
    apply_break(q)
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_before = Pt(before)
    q.paragraph_format.space_after = Pt(after)
    r = q.add_run(text)
    r.font.size, r.bold, r.italic = Pt(size), bold, italic
    return q

def head(text):
    q = p(text, style="Heading 1")
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(14)

def h(text):
    p(text, style="Heading 2")

def institution():
    centered("SIMATS ENGINEERING", 19)
    centered(inst, 13)
    centered("Chennai-602105", 12, after=24)

def img(path, width, alt, container=None, top_fraction=None):
    q = doc.add_paragraph() if container is None else container.paragraphs[0]
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    q.paragraph_format.space_after = Pt(3)
    q.paragraph_format.keep_with_next = True
    shape = q.add_run().add_picture(str(path), width=Inches(width))
    shape._inline.docPr.set("descr", alt)
    if top_fraction is not None:
        pic = shape._inline.graphic.graphicData.pic
        crop = OxmlElement("a:srcRect")
        crop.set("b",str(round(100000*(1-top_fraction))))
        pic.blipFill.insert(1,crop)
        shape.height = int(shape.height * top_fraction)
        pic.spPr.xfrm.ext.cy = shape.height

def caption(text, where=False):
    q = p(text,style="Caption")
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER if where else WD_ALIGN_PARAGRAPH.LEFT
    q.paragraph_format.keep_with_next = not where

def table(headers, data, widths=None, compact=False, borders=True):
    t = doc.add_table(rows=1,cols=len(headers))
    if borders:
        t.style = "Table Grid"
    t.autofit = False
    widths = widths or [6.27/len(headers)]*len(headers)
    for col,w in zip(t.columns,widths):
        col.width=Inches(w)
    for index, row in enumerate([headers,*data]):
        rr = t.rows[0] if index == 0 else t.add_row()
        if index == 0:
            rr._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        rr._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell,value,w in zip(rr.cells,row,widths):
            cell.width=Inches(w)
            q = cell.paragraphs[0]
            q.paragraph_format.space_before = Pt(3)
            q.paragraph_format.space_after = Pt(3)
            q.paragraph_format.line_spacing = 1.13
            r=q.add_run(str(value))
            r.bold = index == 0
            r.font.size=Pt(10 if compact else 11)
            if index == 0 and borders:
                shade=OxmlElement("w:shd")
                shade.set(qn("w:fill"),"EFEFEF")
                cell._tc.get_or_add_tcPr().append(shade)
    return t

def numbered(name, headers, rows, widths=None, compact=False):
    caption(name)
    return table(headers, rows, widths, compact)

def fig(number, label, filename, width, top_fraction=None):
    img(work/filename,width,label,top_fraction=top_fraction)
    caption(f"Figure {number}. {label}",True)

def link(q, label, url):
    a = OxmlElement("w:hyperlink")
    a.set(qn("r:id"),q.part.relate_to(url,RT.HYPERLINK,is_external=True))
    run = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    style = OxmlElement("w:rStyle")
    style.set(qn("w:val"),"Hyperlink")
    props.append(style)
    run.append(props)
    label_node = OxmlElement("w:t")
    label_node.text = label
    run.append(label_node)
    a.append(run)
    q._p.append(a)

def next_page():
    global pending_break
    pending_break = True

def apply_break(q):
    global pending_break
    if pending_break:
        q.paragraph_format.page_break_before = True
        pending_break = False

pending_break = False

def page(title):
    next_page()
    head(title)

def chapter(number,text):
    centered(f"CHAPTER {number}",14,after=6)
    head(text)

charts = [
("Monthly orders","Line chart. Counts orders by purchase month."),
("Order status share","Donut chart. Shows the order count in each status."),
("Top ten states by orders","Ranked horizontal bars. Compares order volumes across destination states."),
("Payment type share","Waffle chart. Area represents the share of payment value, with counts in the detail."),
("Average delivery days by month","Line chart. Groups delivered orders by purchase month."),
("On-time versus late deliveries by state","Grouped bars. Includes states with at least 500 qualifying deliveries."),
("Top product categories by item revenue","Treemap. Area represents item revenue for categories ranked in the top ten."),
("Average freight value by state","Lollipop chart. Each mark represents average freight per item."),
("Delivery time distribution","Histogram. Counts orders within the defined day ranges."),
("Average review score by delivery outcome","Star ratings. Compares review row averages on a five-point scale."),
]

section(doc.sections[0])
img(work/"logo-0.png",6.23,"SIMATS Engineering and Saveetha Institute of Medical and Technical Sciences logos")
centered(title.upper(),17,before=17,after=15)
centered("A CAPSTONE PROJECT REPORT",13,after=18)
centered("A Capstone Project Report submitted in partial fulfilment of the requirements for the course",12,italic=True,after=11)
centered("CSA0504 - Database Management System",14,after=16)
centered("towards the award of the degree of",12,italic=True,after=9)
centered(degree.upper(),13)
centered("IN",12,after=5)
centered(branch.upper(),13,after=15)
centered("Submitted by",12)
for name, reg in zip(students,ids):
    centered(f"{name} ({reg})",13)
centered("Under the Supervision of",12,before=12)
centered("Dr S Sankar, Professor",13,after=18)
centered("SIMATS ENGINEERING",15)
centered(inst,12)
centered("Chennai-602105",12)
centered(month.upper(),13,before=14)

section(doc.add_section(WD_SECTION.NEW_PAGE),"lowerRoman",2)
institution()
head("BONAFIDE CERTIFICATE")
p(f'This is to certify that the Capstone Project entitled “{title}” has been carried out by Monish L (1972260035) and Prasannakumar S (1924260253) under the supervision of Dr S Sankar, Professor. The work is submitted in partial fulfilment of the requirements for CSA0504 - Database Management System in the {degree} programme in {branch} at {inst}, Chennai.')
centered("",before=77)
table(["COURSE COORDINATOR","COURSE FACULTY"],[
    (info.get("coordinator","[Name and designation]"),info.get("faculty","[Name and designation]")),
    (info.get("coordinator_department",branch),info.get("faculty_department",branch)),
    ("SIMATS Engineering\nSIMATS, Chennai-602105","SIMATS Engineering\nSIMATS, Chennai-602105"),
],borders=False)

next_page()
institution()
head("DECLARATION")
p(f'We, Monish L and Prasannakumar S of {branch}, SIMATS Engineering, hereby declare that the capstone project entitled “{title}” is the result of our own work under the supervision of Dr S Sankar.')
p("To the best of our knowledge, the report accurately describes the work completed. The dataset, software, technical references, and assistance used in preparing this report are acknowledged. We will review the evidence and disclosures before signing this declaration.")
p("Place ________________________")
p(f'Date {info.get("date", "_________________________")}')
centered("",before=45)
table(["Student","Signature"],[(f"Monish L ({ids[0]})","________________________"),(f"Prasannakumar S ({ids[1]})","________________________")],borders=False)

next_page()
institution()
head("INDIVIDUAL CONTRIBUTION STATEMENT")
numbered("Table P.1. Individual contribution statement",["Student / Reg. No.","Responsibilities","Design and development","Testing and analysis","Report areas¹","Share"],[
    (f"Monish L\n{ids[0]}","Data preparation, database schema, dashboard workflows","CSV cleaning, import order, keys, Overview, Orders and Database","Source counts, key relationships and monthly dashboard behavior","Data design, ETL and interface","50%"),
    (f"Prasannakumar S\n{ids[1]}","SQL reports, service and visualization","Joins, query filters, Python HTTP service, charts and exports","Report query results, delivery outcomes and output consistency","Report engine, results and delivery analysis","50%"),
    ("Total","","","","","100%"),
],[1.11,1.03,1.26,1.25,1.06,.56],True)
p("¹ Report areas follow the documented module split and can be confirmed by both students before submission.")

page("ABSTRACT")
p("Marketplace order analysis requires data from orders, order items, customers, payments, shipments, reviews and related reference files. In the Olist dataset, the information is distributed across nine CSV files at different levels of detail. Joining them without explicit keys can multiply item totals, while repeated postal prefixes and missing delivery dates complicate regional and delivery comparisons. This project builds a relational database and browser dashboard so that an operations user can investigate the figures and a reviewer can trace them back to SQL.")
p("The extract, transform and load process converts identifiers, dates and monetary values, groups geolocation records by postal prefix and loads related entities in foreign key order. The MySQL schema contains nine base tables and two views for delivery performance and order summaries. A read-only Python HTTP service queries the database with bound parameter values. Four dashboard sections provide an overview, a paginated order search, ten operational reports and a database explorer. Chart selections reveal exact values, and monthly charts support range zoom. Report results can be downloaded as CSV, Excel or PDF.")
p("The project dataset contains 99,441 orders and 112,650 item rows between September 2016 and October 2018. The item prices total R$13,591,643.70, and orders with a recorded delivery date took 12.5 calendar days on average. On-time deliveries received 4.29 out of five across 88,658 review rows, compared with 2.57 across 7,701 review rows for late deliveries. These results identify a difference within the historical dataset and can support further investigation of delivery performance. The dashboard provides a repeatable method for producing and checking the operational measures.")
p("Keywords: relational database, MySQL, ETL, e-commerce, delivery analytics, dashboard.")

page("TABLE OF CONTENTS")
table(["No.","Title","Page"],[
    ("i","Bonafide certificate","ii"),("ii","Declaration","iii"),("iii","Individual contribution statement","iv"),
    ("iv","Abstract","v"),("v","List of figures","vii"),("vi","List of tables","viii"),("vii","List of abbreviations / symbols","ix"),
    ("1","Introduction and Engineering Problem","1"),("2","Literature Review and Existing Solutions","2"),
    ("3","Engineering Design & Trade-offs, Sustainability, Ethics, Safety, Risk & Security","3"),
    ("4","Implementation, Testing & Results, Project Management","7"),
    ("5","Conclusion, Future Work and Reflection","12"),
    ("","References","13"),("","Appendices","14"),("","Capstone Project Outcome Mapping Sheet","24"),
],[.65,4.82,.8])

page("LIST OF FIGURES")
table(["No.","Figure","Page"],[
    ("3.1","Architecture of the Olist dashboard","4"),
    ("4.1","Overview page of the local Marketplace Operations Dashboard","7"),
    ("4.2","SQL display and report implementation evidence","8"),
    ("B.1","Database explorer showing views and foreign keys","15"),
    *((f"E.{j}",lab,str(16+(j-1)//2)) for j,(lab,_) in enumerate(charts,1)),
    ("J.1","Overview metrics and monthly orders","22"),
    ("J.2","Database views and relationships","22"),
    ("J.3","Orders search and filters","22"),
    ("J.4","SQL trace and bound filters","23"),
    ("J.5","Review score report with star ratings","23"),
],[.65,4.82,.8])

page("LIST OF TABLES")
table(["No.","Table","Page"],[
    ("P.1","Individual contribution statement","iv"),
    ("2.1","Comparison of existing approaches","2"),
    ("3.1","Stakeholder requirements","3"),("3.2","Functional and non-functional requirements","3"),
    ("3.3","Applicable specifications and guidance","3"),("3.4","Design specifications","4"),
    ("3.5","Weighted alternative assessment","4"),("3.6","Design trade-offs","5"),
    ("3.7","Sustainability, ethics, safety and security","5"),("3.8","Risk register","6"),
    ("4.1","Tools used for implementation","7"),("4.2","Verification plan and acceptance criteria","8"),
    ("4.3","Achieved results and evidence","9"),("4.4","Review score by delivery outcome","9"),
    ("4.5","Achievement of objectives","10"),("4.6","Milestones","11"),
    ("4.7","Roles and contributions","11"),("4.8","Project cost record","11"),
    ("B.1","Base tables, row identity and parent links","15"),("G.1","Project progress evidence","21"),
    ("J.1","Individual contribution evidence","22"),
],[.65,4.82,.8],True)

page("LIST OF ABBREVIATIONS / SYMBOLS")
table(["Symbol","Description","Unit"],[
    ("API","Application programming interface","—"),("BRL","Brazilian real","R$"),("CSV","Comma-separated values","—"),
    ("DBMS","Database management system","—"),("ETL","Extract, transform and load","—"),("FK","Foreign key","—"),
    ("HTTP","Hypertext Transfer Protocol","—"),("JSON","JavaScript Object Notation","—"),("PK","Primary key","—"),
    ("SQL","Structured Query Language","—"),("TTL","Time to live","s"),("n","Number of records in a group","rows"),
],[1.0,4.25,1.02])

section(doc.add_section(WD_SECTION.NEW_PAGE),"decimal",1)
chapter(1,"INTRODUCTION AND ENGINEERING PROBLEM")
h("1.1 Background")
p("Olist is a Brazilian e-commerce marketplace. Its public dataset records purchases, sellers, products, payment methods, shipping events and customer reviews from 2016 to 2018 [1]. Each file describes a different entity or event. An order can include several items and payment entries, and a postal prefix can occur in many source geolocation rows.")
h("1.2 Need for the Project")
p("Operations users need to compare order trends, freight and delivery outcomes by period and state. Reviewers also need to see how keys, joins and filters produce each result. Manual CSV analysis requires repeated cleaning and joins, which makes it difficult for another user to reproduce the same figures.")
h("1.3 Problem Statement")
p("Design a local database and reporting system that imports nine source files, preserves relationships at their correct level of detail, handles missing delivery data and repeated identifiers, and returns traceable analytics through a browser. It must support useful filtering while constraining database access to read-only operations.")
h("1.4 Project Aim")
p("Deliver an integrated Marketplace Operations Dashboard for historical order and delivery analysis using a normalized MySQL database.")
h("1.5 Project Objectives")
for t in (
    "Build a repeatable importer for nine files and load nine related base tables and two views.",
    "Implement Overview, Orders, Reports and Database workflows with documented filters.",
    "Produce ten SQL reports with exact values and provide CSV, XLSX and PDF exports.",
    "Reconcile headline metrics against the source records and document the limits of the analysis.",
):
    p(t,style="List Bullet")
h("1.6 Scope")
p("The project covers the historical Brazilian dataset, local MySQL storage, a Python service and a browser user interface. Checkout, payment processing, live order ingestion, delivery prediction and permanent public hosting are outside the scope.")
h("1.7 Expected Engineering Outcome")
p("A working local prototype with a documented schema, repeatable import, interactive analysis and reproducible results.")

next_page()
chapter(2,"LITERATURE REVIEW AND EXISTING SOLUTIONS")
h("2.1 Review Method")
p("The review used the Olist dataset description, Codd’s relational model, MySQL documentation, the Connector/Python API and the IETF description of CSV [1]–[5]. The selection focused on file parsing, relational integrity, parameter binding, and how to present results for independent review.")
h("2.2 Review of Existing Work")
p("Codd’s relational model separates the logical representation of relations from their physical storage [2]. Applied here, this supports storing order headers, items, payments and reviews in relations with explicit keys. Foreign key constraints connect child rows with their parent records [3]. Connector/Python supports binding values at execution time [4], which fits reusable reports with date and state filters.")
p("Quoted CSV fields can contain separators and line breaks, as some review comments do [5]. A spreadsheet can summarize a single extract quickly. A database client can inspect joins and queries, but requires the user to locate or compose the SQL.")
h("2.3 Comparative Analysis")
numbered("Table 2.1. Comparison of existing approaches",["Approach","Advantages","Limitations","Project relevance"],[
    ("Spreadsheet and CSV","Quick inspection and pivoting","Keys and refresh depend on operator discipline","Source inspection and independent checks"),
    ("SQL client and normalized schema","Enforced keys and repeatable query scripts","Technical interface for routine comparisons","Development and schema verification"),
    ("Dashboard over MySQL","Reusable filters, visuals and raw values","Additional code and service to maintain","Operational analysis and demonstrations"),
],[1.15,1.55,1.62,1.95])
h("2.4 Engineering Gap")
p("A dataset browser and a SQL client each solve part of the problem. Neither alone gives the intended workflow of selecting a report, inspecting the exact result and checking the SQL and bound filters together.")
h("2.5 Proposed Contribution")
p("The project combines a normalized local data model with an interface that exposes the evidence behind each result. A user can move from a summary chart to a specific order or a report export while a reviewer can inspect the relevant keys and queries.")

next_page()
chapter(3,"ENGINEERING DESIGN & TRADE-OFFS, SUSTAINABILITY, ETHICS, SAFETY, RISK & SECURITY")
h("3.1 Requirements")
numbered("Table 3.1. Stakeholder requirements",["Stakeholder","Requirement"],[
    ("Marketplace operations user","Compare orders, time, freight and ratings with practical date and outcome controls."),
    ("Capstone reviewer","Trace figures to SQL, inspect keys and views, and reproduce the import."),
    ("Project maintainer","Run the application locally and update reports without spreadsheet reassembly."),
],[2.06,4.21])
numbered("Table 3.2. Functional and non-functional requirements",["Requirement","Type","Measurable target"],[
    ("Relational storage","Functional","Nine base tables, two views, and declared parent keys."),
    ("Operational reporting","Functional","Ten visual reports and four dashboard sections."),
    ("Trace and export","Functional","Show SQL and parameters. Provide CSV, XLSX and PDF."),
    ("Access control","Non-functional","Run dashboard queries through the read-only account."),
    ("Repeat lookup efficiency","Non-functional","Cache repeated calls for up to 300 seconds per process."),
],[1.80,1.30,3.17])
h("3.2 Constraints & Applicable Standards")
p("The dashboard must operate on the available computer and historical data without a continuously hosted service. SQL definitions depend on the MySQL dialect. The design uses a format specification and vendor guidance as implementation references.")
numbered("Table 3.3. Applicable specifications and guidance",["Reference","Requirement or guidance","Application"],[
    ("RFC 4180 [5]","Parse separators and quoted fields correctly.","Read CSV with a parser and export structured CSV."),
    ("MySQL 8.0 manual [3]","Declare foreign keys and reference compatible columns.","Use InnoDB keys and order the import by dependency."),
    ("Connector/Python guide [4]","Bind application values using cursor.execute parameters.","Bind date, state, status and identifier filters."),
],[1.62,2.1,2.55])

page("ENGINEERING DESIGN AND ALTERNATIVE EVALUATION")
h("3.3 Design Specifications")
numbered("Table 3.4. Design specifications",["Parameter","Target","Unit","Priority"],[
    ("Source input","Nine files","files","High"),("Delivery date window","2016–2018 order purchases","calendar years","High"),
    ("Order pagination","25 result records per page","orders","Medium"),("Cache limits","300-second TTL and 64 entries","s / entries","Medium"),
],[1.81,2.62,1.08,.76])
h("3.4 Alternative Solutions & Evaluation")
p("A. CSV and spreadsheets provide a direct way to inspect extracts. B. A MySQL database and custom browser dashboard support relational constraints and interactive analysis. C. A hosted SQL database and dashboard enable remote access with ongoing service dependencies.")
numbered("Table 3.5. Weighted alternative assessment",["Criterion","Weight","A. CSV","B. Local","C. Hosted"],[
    ("Integrity and traceability","35%","2","5","5"),("Usability for a demo","25%","3","5","4"),
    ("Cost and setup","20%","5","4","2"),("Offline repeatability","20%","4","5","1"),("Weighted score (/5)","100%","3.25","4.80","3.35"),
],[2.39,.8,.94,1.04,1.10])
p("Scores are an engineering assessment on a scale from 1 (weak) to 5 (strong) against the capstone requirements.")
h("3.5 Selected Design & Detailed Design")
p("The local MySQL design scored highest because it supports referential integrity, provides an interactive interface and works without a remote database connection. The importer writes with an administrative role. The dashboard reads from the same schema through a separate account.")
architecture = Image.new("RGB",(1400,155),"white")
draw = ImageDraw.Draw(architecture)
bold_font = ImageFont.truetype("C:/Windows/Fonts/timesbd.ttf",30)
text_font = ImageFont.truetype("C:/Windows/Fonts/times.ttf",26)
for j,(name,line1,line2) in enumerate([
    ("Source","Olist","9 CSV files"),
    ("ETL importer","Clean records","Load by key order"),
    ("MySQL","9 base tables","2 SQL views"),
    ("Python service","Read-only queries","Result cache"),
    ("Browser","Four sections","Charts and exports"),
]):
    left = 287*j + 3
    draw.rectangle((left,10,left+246,143),outline="#222222",width=3,fill="#f4f4f4")
    for y,label,font in [(36,name,bold_font),(80,line1,text_font),(111,line2,text_font)]:
        draw.text((left+123,y),label,font=font,fill="#111111",anchor="mm")
    if j<4:
        draw.line((left+250,77,left+279,77),fill="#222222",width=4)
        draw.polygon([(left+279,69),(left+289,77),(left+279,85)],fill="#222222")
architecture.save(work/"architecture.png")
fig("3.1","Architecture of the Olist dashboard. Data flows from left to right.","architecture.png",6.26)
p("The browser sends filters to the service, which binds them to the relevant query and returns results with a query trace. Chart rendering and range selection happen in the browser. Export requests reuse the report query and selected filters.")

page("DESIGN TRADE-OFFS AND RESPONSIBILITIES")
h("3.6 Trade-off Analysis")
numbered("Table 3.6. Design trade-offs",["Decision","Alternative","Benefit","Cost and justification"],[
    ("Normalize source entities","One wide reporting table","Keys preserve each entity’s level of detail","More joins. Database views simplify repeated logic."),
    ("Use local MySQL","Hosted database","Stable local demo and fewer service dependencies","Remote access depends on the host. Local operation meets the capstone goal."),
    ("Cache by filter values","Rerun every query","Avoids repeat reads with unchanged filters","Results may be stale for up to five minutes after a reload."),
    ("Use ZIP-prefix reference rows","Drop unmatched entities","Preserves linked customer or seller records","Unknown state or coordinates have limited analytical value."),
],[1.35,1.22,1.56,2.14])
h("3.7 Sustainability, Ethics, Safety, Risk & Security")
numbered("Table 3.7. Sustainability, ethics, safety and security",["Domain","Consideration","Evidence evaluated","Design impact"],[
    ("Sustainability","Repeated local query work","Historical inputs and repeated report/filter requests","Use an existing computer and a bounded cache. No claim about energy savings."),
    ("Ethics","Historical data and identifiable-looking records","Public dataset terms and detailed order/review fields","Cite Olist. Present aggregates and avoid republishing raw review text in the report."),
    ("Health and safety","Nature of project activity","Local software prototype with no physical actuation","Use normal computer lab procedures. Results have no safety-critical decision role."),
    ("Security","Credentials and input boundaries","Separate ETL and dashboard accounts and HTTP filters","Store local secrets outside published code. Use bound filters and read-only database access."),
],[1.14,1.24,1.80,2.09],True)
p("The optional tunnel depends on the computer and local server staying online. Access to a public demonstration should be controlled and time limited because the dashboard exposes order-level data and SQL traces.")

page("RISK REGISTER")
numbered("Table 3.8. Risk register",["Risk","Likelihood","Severity","Level","Mitigation","Residual"],[
    ("Join multiplies monetary values","Medium","High","High","Aggregate at the item level and reconcile total price to the source.","Low"),
    ("Missing delivery dates distort averages","Medium","High","High","Keep missing dates as NULL and exclude them from delivery-day averages.","Low"),
    ("Unmatched ZIP prefix or duplicate source ID","High","Medium","High","Normalize ZIP prefixes, create explicit unknown reference rows and use composite keys for reviews.","Medium"),
    ("Dashboard obtains write access","Low","High","Medium","Separate application reads from administrative import and schema setup.","Low"),
    ("Cached result outlives reload","Medium","Medium","Medium","Use a bounded TTL and restart the local service after a major refresh.","Low"),
    ("Demo interrupted by sleep or network loss","Medium","Medium","Medium","Run on localhost for assessment and use the tunnel only when remote access is needed.","Medium"),
    ("Detailed records exposed through a public tunnel","Medium","High","High","Restrict audience and duration, and use aggregate screenshots for distribution.","Medium"),
],[1.51,.68,.63,.61,2.18,.66],True)
p("The ratings are qualitative. Likelihood concerns the capstone demonstration and severity concerns the impact on the integrity, availability or privacy of the reported data.")

next_page()
chapter(4,"IMPLEMENTATION, TESTING & RESULTS, PROJECT MANAGEMENT")
h("4.1 Development Approach & Resources")
p("Development started with inspecting the nine files and identifying each table’s row identity. The team implemented the schema and importer, added shared views and report queries, and then connected the dashboard. Source CSVs, SQL scripts, the application and the review presentation provide the project evidence [1], [6], [7].")
h("4.2 Software Implementation & Modern Tools Used")
p("The importer loads parent tables before dependent tables. It trims text, converts dates and values, groups source geolocation rows by ZIP prefix and adds explicit unknown records for missing prefixes. Order item and payment sequence numbers are part of their keys. Review records use a compound key so that a review identifier shared by different orders can be retained.")
numbered("Table 4.1. Tools used for implementation",["Tool","Purpose","Stage"],[
    ("Python and CSV processing","Clean and batch load the nine inputs.","Data preparation"),
    ("MySQL / Connector/Python","Enforce keys, run reports and bind filters.","Storage and query service"),
    ("HTML, CSS and JavaScript","Present views, charts, selection and zoom.","Dashboard"),
    ("pandas, openpyxl and ReportLab","Structure results and produce exports.","Reporting"),
],[1.76,2.95,1.56])
fig("4.1","Overview page of the local Marketplace Operations Dashboard (review slide 11).","figure-11.png",3.87)

page("IMPLEMENTATION EVIDENCE AND VERIFICATION PLAN")
p("The Overview page displays key metrics and monthly orders. Orders uses a 25-row page size and supports lookup by order ID prefix, date, state and delivery outcome. Reports exposes ten case-specific SQL queries, with exact values and exports. Database displays table metadata, foreign keys and views.")
p("Identical read requests can reuse in-process results for up to five minutes. A new filter set uses a separate cache entry. Monthly zoom is a browser operation on the loaded series and is available on Overview, R01 and R05.")
fig("4.2","SQL display and report implementation evidence (review slide 14).","figure-14.png",3.95)
h("4.3 Test Plan & Verification")
numbered("Table 4.2. Verification plan and acceptance criteria",["Requirement","Method","Acceptance criterion"],[
    ("Import and row identity","Count source rows and distinct IDs. Check database table inventory.","Nine expected tables and two views. No count mismatch for the reconciled headline entities."),
    ("Revenue and delivery measures","Calculate item sum and elapsed calendar days from CSV.","Matches the presentation at its stated precision."),
    ("Report engine and visual output","Inspect roster, source query definitions and review figures.","R01 through R10 present with matching subject matter."),
    ("Read-only access and safe filters","Inspect grants, parameter binding and validation. Confirm with database account in a live run.","SELECT is allowed and writes are denied. Malformed inputs produce a controlled error."),
    ("Filter, zoom and export behavior","Compare output across a known filter; exercise zoom and obtain exports.","Zoom stays within loaded months. Export and report use matching rows."),
],[1.41,2.22,2.64],True)

page("VERIFICATION RESULTS")
numbered("Table 4.3. Achieved results and evidence",["Specification","Required value","Achieved value / evidence","Status"],[
    ("Schema inventory","9 tables, 2 views","Nine CREATE TABLE and two CREATE VIEW definitions [6].","Pass (source)"),
    ("Order and item counts","Match input records","99,441 orders and 112,650 items in source data and project evidence.","Pass (reconciled)"),
    ("Item revenue","Match decimal sum","R$13,591,643.70, independently summed from source item prices.","Pass (reconciled)"),
    ("Average delivery time","Match slide precision","12.4973 calendar days over 96,476 recorded delivery dates, displayed as 12.5.","Pass (reconciled)"),
    ("Report coverage","10 visual reports","Ten report definitions and corresponding captured figures.","Pass (evidence)"),
    ("Read access, filters, zoom and exports","Functional checks on a live instance","Source and demonstration support these features. No fresh live acceptance run is reported here.","Partial (evidence)"),
],[1.49,1.15,2.63,1.0],True)
h("4.4 Results")
p("The source files contain 99,441 order rows, 112,650 item rows, 103,886 payment rows and 32,951 product rows. Purchases span 4 September 2016 to 17 October 2018. The Overview shows a review average of 4.1 out of five across all applicable review rows. Table 4.4 focuses on review rows joined to recorded delivery outcomes.")
numbered("Table 4.4. Review score by delivery outcome",["Delivery outcome","Review rows","Mean score (/5)"],[
    ("On time or early","88,658","4.29"),
    ("Late","7,701","2.57"),
],[2.64,1.67,1.96])
p("Appendix E contains captures of all ten figures from the review presentation, including the R10 star plot.")
h("4.5 Data Analysis & Engineering Judgment")
p("The difference between on-time and late review groups is about 1.73 points using unrounded averages. The counts represent review rows. The result describes an association in the historical sample. Differences in product category, seller and customer geography could also contribute to the scores.")
p("The headline item total is the sum of item prices in Brazilian reais. Freight and payment value are separate measures. Geographic reports use the stored ZIP-prefix mapping, and monthly comparisons should account for partial months at both dataset boundaries.")

page("OBJECTIVE ACHIEVEMENT AND LIMITATIONS")
h("4.6 Comparison with Existing Solutions & Achievement of Objectives")
numbered("Table 4.5. Achievement of objectives",["Objective","Evidence","Achievement"],[
    ("Build a repeatable relational import","Nine CSV inputs, importer, schema with nine tables and two reusable views.","Fully achieved"),
    ("Implement dashboard workflows","Four sections with order search, filters and metadata inspection in the implementation.","Fully achieved"),
    ("Provide traceable report output","Ten captured reports, SQL traces and export implementation. The review slides show the report workflow.","Fully achieved"),
    ("Reconcile headline metrics","Order counts, item price totals, delivery average and outcome reviews cross-checked against CSVs.","Fully achieved"),
    ("Measure service behavior under load","Cache implementation is documented. A controlled load benchmark was outside this analysis.","Not assessed"),
],[1.81,3.15,1.31])
p("The SQL and dashboard workflow replaces repeated manual joins with reusable views and parameterized queries. Compared with the SQL-client-only approach, the browser adds discoverable report controls and direct access to tabular values and exports.")
h("4.7 Strengths & Limitations")
for t in (
    "The schema defines the level of detail of each entity and avoids combining items, payments and reviews into a single reporting table.",
    "The SQL and bound values shown by the dashboard let users trace results back to the query definitions.",
    "The dataset represents a historical Brazilian marketplace. Results may not generalize to a current or different market.",
    "Postal-prefix lookup is less precise than an address-level record. Unknown prefixes and grouped locations limit geographic interpretation.",
    "Ratings depend on reviews present in the dataset. The scoring comparison cannot establish causality.",
    "The local service depends on the host computer. Cache entries can remain valid for five minutes after source changes.",
):
    p(t,style="List Bullet")

page("PROJECT PLANNING, ROLES & BUDGET")
h("4.8 Project Planning, Roles & Budget")
numbered("Table 4.6. Milestones",["Milestone","Output","Evidence"],[
    ("1. Inspect source files","Entity map and cleaning rules","CSV structure and importer"),
    ("2. Implement relational schema","Keys, constraints, base tables and views","SQL scripts and Database view"),
    ("3. Implement application modules","Dashboard screens and report query layer","Local application and report catalog"),
    ("4. Integrate and reconcile results","Ten visible reports and cross-checked totals","Review figures and results tables"),
    ("5. Prepare demonstration","Project slides, export workflow and documentation","Capstone presentation and report"),
],[1.83,2.33,2.11])
numbered("Table 4.7. Roles and contributions",["Student","Assigned responsibility","Documented contribution"],[
    ("Monish L","Module 1: Data preparation, schema and dashboard interface","Imports and relational design, Overview, Orders, Database and monthly interactions."),
    ("Prasannakumar S","Module 2: SQL reports, service and visualization","Report joins and views, query service, exact values, visuals and export workflow."),
],[1.36,2.20,2.71])
numbered("Table 4.8. Project cost record",["Item","Estimated cost","Actual direct cost"],[
    ("Local computer and lab facilities","Existing equipment","Existing asset. No purchase recorded."),
    ("Dataset and local software tools","₹0 additional purchase expected","Open/public resources used."),
    ("Cloud or demonstration services","Optional","No direct spending reported."),
    ("Confirmed project total","",info.get("cost","[Confirm actual spending]")),
],[2.1,2.07,2.1])
p("The cost table tracks direct project expenses. It excludes the value of existing equipment and student time.")

next_page()
chapter(5,"CONCLUSION, FUTURE WORK AND REFLECTION")
h("5.1 Conclusion")
p("The capstone consolidated nine historical e-commerce CSVs into a MySQL database and connected the records to a local operations dashboard. The two modules support traceable analysis through a normalized schema, read-only queries and ten graphical reports. Reconciliation confirmed the main counts, item revenue and delivery and review measures. The review comparison identifies a meaningful operational question for further investigation of late orders.")
h("5.2 Future Work")
for t in (
    "Add automated reconciliation queries and a reproducible cold-cache and warm-cache benchmark.",
    "Measure delivery outcomes within comparable cohorts by state, product category and seller.",
    "Add explicit authorization and restrict order-level review fields before any persistent remote deployment.",
    "Improve geographic analysis by distinguishing unknown postal prefixes from verified locations.",
):
    p(t,style="List Bullet")
h("5.3 Professional Learning & Individual Reflection")
p("The team applied relational modeling, composite keys, referential integrity, aggregate SQL and parameter binding. It also practised result reconciliation, web integration and communication through charts and query traces.")
for name, fallback in [
    ("Monish L","[Student reflection: describe the ZIP-prefix or import challenge you personally handled, explain the evidence for your design choice, and identify one improvement.]"),
    ("Prasannakumar S","[Student reflection: describe a delivery-query or report-service challenge you personally handled, explain the evidence for your design choice, and identify one improvement.]"),
]:
    p(name,style="Heading 3")
    p(info.get(name,fallback))

page("REFERENCES")
for ref in (
    "[1] Olist, “Brazilian E-Commerce Public Dataset by Olist,” Kaggle. https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
    "[2] E. F. Codd, “A relational model of data for large shared data banks,” Communications of the ACM, vol. 13, no. 6, pp. 377–387, 1970. doi:10.1145/362384.362685.",
    "[3] Oracle, “FOREIGN KEY Constraints,” MySQL 8.0 Reference Manual, sec. 15.1.20.5. https://dev.mysql.com/doc/refman/8.0/en/create-table-foreign-keys.html",
    "[4] Oracle, “MySQLCursor.execute() Method,” MySQL Connector/Python Developer Guide. https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-execute.html",
    "[5] Y. Shafranovich, “Common Format and MIME Type for Comma-Separated Values (CSV) Files,” RFC 4180, Oct. 2005. https://datatracker.ietf.org/doc/rfc4180/",
    "[6] Olist capstone project, local source repository. SQL/schema.sql, SQL/views.sql, SQL/etl/import_olist.py, WEBPAGE/app/reports.py and WEBPAGE/marketplace.",
    "[7] M. L and P. S, “E-Commerce Marketplace Orders & Delivery Dashboard,” CSA0504 capstone review presentation, SIMATS Engineering.",
    "[8] SIMATS Engineering, “Capstone Project Report - New Format - Sep 2026,” institutional report template.",
    "[9] OpenAI Codex, AI assistance used to organize and draft this report, reconcile selected metrics against local CSVs, and format the supplied visual evidence.",
):
    p(ref)

page("APPENDICES")
h("Appendix A. Detailed Calculations")
p("A.1 Order volume. Count one row per order identifier in the orders file. The historical period is determined by the minimum and maximum order purchase timestamps.")
p("A.2 Item revenue. Sum the decimal price values of all item rows. Freight is recorded separately, and total payments include a different set of components. The total from the CSV is R$13,591,643.70.")
p("A.3 Delivery duration. For each order with a recorded customer delivery date, subtract the calendar date of purchase from the calendar date of delivery. Divide the sum of calendar-day differences by 96,476. The average is 12.4973 days, displayed as 12.5 days.")
p("A.4 Grouped review scores. For each review linked to a recorded delivery, compare actual and estimated delivery timestamps. Actual delivery at or before the estimate is on time. Sum the scores in each outcome group and divide by that group’s review count. Round the resulting mean to two decimal places for R10.")
p("A.5 Weighted design assessment. Multiply each criterion score by its fractional weight and sum across criteria. For the local design, 0.35 × 5 + 0.25 × 5 + 0.20 × 4 + 0.20 × 5 = 4.80.")
p("A.6 Date filtering. An inclusive end date selected in the dashboard is converted to the start of the following calendar day, and the SQL uses a strict less-than comparison. This includes orders throughout the user’s selected last date.")

page("RELATIONAL DESIGN AND SOURCE CODE")
h("Appendix B. Relational Design")
numbered("Table B.1. Base tables, row identity and parent links",["Base table","Primary key","References"],[
    ("geolocation","zip_prefix","—"),("customers","customer_id","geolocation"),("sellers","seller_id","geolocation"),
    ("product_categories","category_name","—"),("products","product_id","product_categories"),
    ("orders","order_id","customers"),("order_items","order_id + order_item_id","orders, products, sellers"),
    ("order_payments","order_id + payment_sequential","orders"),("order_reviews","review_id + order_id","orders"),
],[1.63,2.62,2.02],True)
fig("B.1","Database explorer showing views and foreign keys (review slide 10).","figure-10.png",3.17)
h("Appendix C. Source Code and Repository Information")
repo_paragraph = p()
link(repo_paragraph,"GitHub: MONISH-067 / DBMS / CSA0504 capstone submission",github)
p("SQL/schema.sql defines the tables and keys. SQL/views.sql defines v_delivery_performance and v_order_summary. SQL/etl/import_olist.py handles CSV preparation and load. WEBPAGE/marketplace contains the custom application, and WEBPAGE/app/reports.py contains the runtime report queries.")
q = p()
q.alignment = WD_ALIGN_PARAGRAPH.LEFT
q.paragraph_format.line_spacing = 1.04
q.paragraph_format.keep_together = True
code = q.add_run("""SELECT vdp.delivery_outcome, ROUND(AVG(r.review_score), 2), COUNT(*)
FROM order_reviews r
JOIN v_delivery_performance vdp ON vdp.order_id = r.order_id
WHERE vdp.delivery_outcome IN ('on_time', 'late')
GROUP BY vdp.delivery_outcome""")
code.font.name = "Consolas"
code.font.size = Pt(9)
caption("R10 core aggregation. Optional date and state filters are in WEBPAGE/app/reports.py.",True)

for idx in range(0,10,2):
    page("APPENDIX E. REPORT VISUALIZATIONS")
    if idx == 0:
        p("The charts below are captured from the project dashboard. The figures preserve the filter context visible in the captured view.")
    for j in (idx,idx+1):
        label,desc=charts[j]
        h(f"R{j+1:02d}  {label}")
        fig(f"E.{j+1}",label+f" (review slide {16+j}).",f"figure-{16+j}.png",6.08)
        p(desc)

page("PROJECT PROGRESS RECORDS")
h("Appendix G. Project Meeting and Progress Records")
numbered("Table G.1. Project progress evidence",["Progress point","Evidence available"],[
    ("Source and data model defined","Presentation slides 5–10, SQL schema and importer."),
    ("Dashboard and reports integrated","Slides 11–27 and application source."),
    ("Results and project status summarized","Slides 28–32 and the reconciliation in Chapter 4."),
],[2.34,3.93])
p("Available evidence records project milestones. Signed meeting minutes and meeting dates can be annexed if maintained by the team.")

page("INDIVIDUAL CONTRIBUTION EVIDENCE")
h("Appendix J. Individual Contribution Evidence")
numbered("Table J.1. Individual contribution evidence",["Student","Assigned module","Implementation evidence"],[
    (f"{students[0]} ({ids[0]})","1. Data preparation, schema and dashboard interface","SQL/schema.sql, SQL/etl/import_olist.py and Figures J.1–J.3."),
    (f"{students[1]} ({ids[1]})","2. SQL reports, service and visualization","WEBPAGE/app/reports.py and Figures J.4–J.5. See Appendix E for all ten reports."),
],[1.47,2.30,2.50],True)
h("Module 1. Data Preparation, Schema and Dashboard Interface")
pair = doc.add_table(rows=1,cols=2)
pair.autofit = False
for col in pair.columns:
    col.width=Inches(3.135)
for cell,number,label,file in zip(pair.rows[0].cells,("J.1","J.2"),
    ("Overview metrics and monthly orders","Database views and relationships"),("figure-11.png","figure-10.png")):
    cell.width=Inches(3.135)
    img(work/file,3.00,label,container=cell)
    q=cell.add_paragraph(f"Figure {number}. {label}","Caption")
    q.alignment=WD_ALIGN_PARAGRAPH.CENTER
fig("J.3","Orders search and filters (archived dashboard capture).","figure-orders.jpg",5.57,top_fraction=.31)

page("INDIVIDUAL CONTRIBUTION EVIDENCE")
h("Module 2. SQL Reports, Service and Visualization")
fig("J.4","Report SQL trace and bound filters (review slide 14).","figure-14.png",4.38)
fig("J.5","Review score report with star ratings (review slide 25).","figure-25.png",6.08)
p("Figure J.4 documents how the report interface exposes its SQL and parameter values. Figure J.5 shows the chart and review counts produced by the report engine. Appendix E contains the complete report gallery.")

page("CAPSTONE PROJECT OUTCOME MAPPING SHEET")
p("For completion by the department or faculty assessor.")
table(["Outcome evidence","SO / area","Location in this report"],[
    ("Complex engineering problem formulation","SO1","Chapters 1 and 2"),
    ("Engineering design under constraints","SO2","Chapter 3"),
    ("Written and oral technical communication","SO3","Report and viva"),
    ("Ethics and professional responsibility","SO4","Section 3.7"),
    ("Teamwork and leadership","SO5","Section 4.8 and Appendix J"),
    ("Experimentation, analysis and engineering judgment","SO6","Sections 4.3–4.6"),
    ("Independent acquisition of new knowledge","SO7","Section 5.3"),
    ("Standards and specifications","SO2","Section 3.2"),
    ("Sustainability and societal or environmental impact","SO2 / SO4","Section 3.7"),
    ("Risk assessment and mitigation","SO2 / SO4","Section 3.7 and Table 3.8"),
    ("Security considerations","Relevant SO","Section 3.7"),
    ("Integrated engineering","SO1 / SO2","Section 3.5"),
    ("Project planning and management","SO5","Section 4.8"),
    ("Individual contribution","SO1–SO7","Contribution statement, Section 4.8, Appendix J"),
],[2.83,1.0,2.44],True)
p("Assessor name and signature ___________________________________")

if "--public" in sys.argv:
    for node in doc._element.iter(qn("w:t")):
        if node.text:
            for reg in ids:
                node.text = node.text.replace(reg,"withheld")
    doc.save(work/"CSA0504 Capstone Project Report.public.docx")
else:
    doc.save(root/"CSA0504 Capstone Project Report.docx")
