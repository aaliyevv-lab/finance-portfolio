"""
Build output/Richter_Gedeon_DCF.xlsx: a 5-year DCF (free cash flow to the firm) of Gedeon Richter Plc.

All historical numbers come from the Gedeon Richter Annual Report 2025 (non-official draft),
consolidated IFRS statements, in HUF millions. Every forecast and valuation cell is written as
an Excel formula, so the workbook recalculates when you change a blue input on 'Assumptions'.

Run from the project folder:
    cd 05-richter-dcf
    python src/build_model.py
Then open output/Richter_Gedeon_DCF.xlsx in Excel (it calculates on open).
"""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.properties import PageSetupProperties

AR = "Richter Annual Report 2025, "
AR_URL = ("https://www.gedeonrichter.com/-/media/sites/hq/documents/investors/financial-reports/"
          "annual-report/en/2025/annual_report_2025_non_official_draft.pdf")

F = "Arial"
BLUE, BLACK, GREEN, WHITE, GREY = "0000FF", "000000", "008000", "FFFFFF", "666666"
NAVY = "1F3A5F"
f_in = Font(name=F, size=10, color=BLUE)
f_calc = Font(name=F, size=10, color=BLACK)
f_link = Font(name=F, size=10, color=GREEN)
f_bold = Font(name=F, size=10, bold=True)
f_note = Font(name=F, size=9, italic=True, color=GREY)
f_title = Font(name=F, size=14, bold=True, color=NAVY)
f_hdr = Font(name=F, size=10, bold=True, color=WHITE)
fill_hdr = PatternFill("solid", fgColor=NAVY)
fill_key = PatternFill("solid", fgColor="FFFF00")
fill_out = PatternFill("solid", fgColor="E8EEF6")
thin = Side(style="thin", color="999999")
top_border = Border(top=thin)

NUM = '#,##0;(#,##0);"-"'
NUM1 = '#,##0.0;(#,##0.0);"-"'
PCT = '0.0%;(0.0%);"-"'
MULT = '0.0"x"'
HUF = '#,##0" HUF";(#,##0" HUF")'
DF = '0.000'

wb = Workbook()


def setup(ws, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w
    ws.sheet_view.showGridLines = False


def put(ws, ref, value, font=f_calc, fmt=None, bold=False, fill=None, note=None):
    c = ws[ref]
    c.value = value
    c.font = Font(name=F, size=font.size, color=font.color, bold=bold or font.bold,
                  italic=font.italic)
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if note:
        c.comment = Comment(note, "Model")
    return c


def header_row(ws, row, labels, start_col=1):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=start_col + i, value=lab)
        c.font = f_hdr
        c.fill = fill_hdr
        c.alignment = Alignment(horizontal="left" if i == 0 else "right")


def section(ws, row, text, ncols):
    header_row(ws, row, [text] + [""] * (ncols - 1))


# ---------------------------------------------------------------- README
rd = wb.active
rd.title = "README"
setup(rd, {"A": 3, "B": 30, "C": 90})
put(rd, "B2", "Gedeon Richter Plc — DCF Valuation", f_title)
put(rd, "B3", "5-year unlevered free cash flow (FCFF) model · HUF millions unless stated · "
              "valuation date 31 Dec 2025", f_note)
rows = [
    ("Purpose", "Estimate the intrinsic value per share of Gedeon Richter (BSE: RICHTER) and "
                "compare it with the market price."),
    ("Method", "Forecast FCFF = EBIT × (1 – tax) + D&A – Capex – ΔNWC for 2026–2030, discount at "
               "WACC, add a Gordon-growth terminal value, then bridge enterprise value to equity "
               "value per share."),
    ("Key driver", "Revenue is split into Vraylar (cariprazine) royalties from AbbVie and the "
                   "core business. Royalties are high-margin but face US generics from ~Sep 2029, "
                   "so group EBIT margin falls from ~32% to ~20% by 2030 and the terminal value "
                   "excludes royalties. This patent cliff is why Richter trades at only ~7x EBIT."),
    ("Tabs", "Assumptions → all editable drivers · Historicals → 2023–2025 reported figures and "
             "ratios · DCF → forecast and valuation · Sensitivity → value per share across WACC "
             "and terminal growth."),
    ("How to use", "Change only blue cells on 'Assumptions'. Everything else recalculates."),
    ("Colour code", "Blue text = hard-coded input · Black = formula · Green = link to another "
                    "sheet · Yellow fill = key assumption · Shaded blue = key output."),
    ("Data source", "Gedeon Richter Annual Report 2025 (non-official draft), consolidated IFRS "
                    "statements, pp. 146–152: " + AR_URL),
    ("", "2023 revenue and EBIT: Richter Q4/FY2024 earnings report (28 Feb 2025). 2026 "
         "guidance: Richter FY2025 results release, 27 Feb 2026 — 'high-single-digit growth in "
         "both revenues and Clean EBIT'."),
    ("Share price", "HUF 13,600: approximate Budapest Stock Exchange price, mid-November 2026 "
                    "(Investing.com / BSE). Update before use."),
    ("Limitations", "WACC inputs (risk-free rate, beta, ERP) are author assumptions, not market "
                    "quotes — check them. Valuation is as of 31 Dec 2025 while the share price is "
                    "Nov 2026, so the upside figure ignores ~11 months of time value. "
                    "EBIT includes one-offs; Richter's 'Clean EBIT' is higher."),
    ("Author", "Aliheydar Aliyev, Nov 2026"),
]
r = 5
for k, v in rows:
    put(rd, f"B{r}", k, f_bold)
    c = put(rd, f"C{r}", v)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    rd[f"B{r}"].alignment = Alignment(vertical="top")
    rd.row_dimensions[r].height = 15 * max(1, len(v) // 95 + 1)
    r += 1

# ---------------------------------------------------------------- Historicals
hs = wb.create_sheet("Historicals")
setup(hs, {"A": 46, "B": 12, "C": 12, "D": 12, "E": 62})
put(hs, "A1", "Historical financials (HUF m)", f_title)
put(hs, "A2", "Consolidated IFRS. Expenses and cash outflows shown as positive numbers.", f_note)
header_row(hs, 3, ["Income statement", "2023", "2024", "2025", "Source"])

def hrow(row, label, vals, fmt=NUM, note="", bold=False):
    put(hs, f"A{row}", label, f_bold if bold else f_calc)
    for col, v in zip("BCD", vals):
        if v is None:
            continue
        is_formula = isinstance(v, str) and v.startswith("=") and not v[1:].replace("+", "").isdigit()
        put(hs, f"{col}{row}", v, f_calc if is_formula else f_in, fmt, bold=bold)
    if note:
        put(hs, f"E{row}", note, f_note)

hrow(4, "Revenue", [805158, 857545, 928962], note=AR + "Income Statement p.146; 2023 from Q4/FY2024 report", bold=True)
hrow(5, "  Revenue growth", [None, "=C4/B4-1", "=D4/C4-1"], PCT)
hrow(6, "Gross profit", [None, 590738, 640911], note=AR + "Income Statement p.146")
hrow(7, "  Gross margin", [None, "=C6/C4", "=D6/D4"], PCT)
hrow(8, "EBIT (profit from operations)", [189364, 261157, 292851], note=AR + "Income Statement p.146; 2023 from Q4/FY2024 report", bold=True)
hrow(9, "  EBIT margin", ["=B8/B4", "=C8/C4", "=D8/D4"], PCT)
hrow(10, "Profit before income tax", [None, 281077, 284747], note=AR + "Income Statement p.146")
hrow(11, "Income tax", [None, 41553, 52519], note=AR + "Income Statement p.146")
hrow(12, "  Effective tax rate", [None, "=C11/C10", "=D11/D10"], PCT)
hrow(13, "Net profit attributable to owners", [None, 239244, 232335], note=AR + "Income Statement p.146")

header_row(hs, 15, ["Cash flow items", "2023", "2024", "2025", "Source"])
hrow(16, "Depreciation, amortisation & impairment", [None, 52760, 60463], note=AR + "Cash Flow Statement p.152")
hrow(17, "  D&A % of revenue", [None, "=C16/C4", "=D16/D4"], PCT)
hrow(18, "Purchase of PP&E", [None, 52927, 42579], note=AR + "Cash Flow Statement p.152")
hrow(19, "Purchase of intangible assets", [None, 10791, 23825], note=AR + "Cash Flow Statement p.152")
hrow(20, "Total capex", [None, "=C18+C19", "=D18+D19"], bold=True)
hrow(21, "  Capex % of revenue", [None, "=C20/C4", "=D20/D4"], PCT)
hrow(22, "EBITDA (EBIT + D&A)", [None, "=C8+C16", "=D8+D16"])

header_row(hs, 24, ["Balance sheet (31 Dec)", "2023", "2024", "2025", "Source"])
hrow(25, "Inventories", [None, 214151, 214114], note=AR + "Balance Sheet p.148 (2024 restated)")
hrow(26, "Trade receivables", [None, 240327, 244395], note=AR + "Balance Sheet p.148")
hrow(27, "Trade payables", [None, 72331, 55636], note=AR + "Balance Sheet p.149")
hrow(28, "Operating net working capital", [None, "=C25+C26-C27", "=D25+D26-D27"], bold=True)
hrow(29, "  NWC % of revenue", [None, "=C28/C4", "=D28/D4"], PCT)
hrow(31, "Cash and cash equivalents", [None, 135627, 211817], note=AR + "Balance Sheet p.148")
hrow(32, "Current financial assets", [None, 994, "=44049+773+1523"], note="Amortised cost + FVTPL + FVOCI, Balance Sheet p.148")
hrow(33, "Associates & non-current financial assets", [None, "=16378+1335+71531+79879", "=17516+6156+73656+43344"], note="Associates/JVs + non-current fin. assets (amortised cost, FVTPL, FVOCI), p.148")
hrow(34, "Borrowings (current + non-current)", [None, "=1253+365", "=1015+194"], note=AR + "Balance Sheet p.149")
hrow(35, "Lease liabilities (current + non-current)", [None, "=14624+5501", "=14128+5808"], note=AR + "Balance Sheet p.149")
hrow(36, "Financial liabilities at fair value (P&L)", [None, "=61132+9346", "=61123+6306"], note="Current + non-current, p.149; mainly deferred deal payments (Note 24) — treated as debt-like")
hrow(37, "Non-controlling interest", [None, 3400, 2495], note=AR + "Balance Sheet p.149")
# formulas that only add hard-coded source numbers are inputs → blue
for ref in ["D32", "C33", "D33", "C34", "D34", "C35", "D35", "C36", "D36"]:
    hs[ref].font = f_in
hs.freeze_panes = "B4"

# ---------------------------------------------------------------- Assumptions
asn = wb.create_sheet("Assumptions", 1)
setup(asn, {"A": 40, "B": 13, "C": 13, "D": 13, "E": 13, "F": 13, "G": 70})
put(asn, "A1", "Assumptions", f_title)
put(asn, "A2", "Edit blue cells only. Yellow = key valuation drivers.", f_note)

section(asn, 3, "Market & share data", 7)
put(asn, "A4", "Valuation date"); put(asn, "B4", "31 Dec 2025", f_in)
put(asn, "A5", "Current share price (HUF)"); put(asn, "B5", 13600, f_in, NUM, fill=fill_key)
put(asn, "G5", "Approx. BSE price mid-Nov 2026 (Investing.com / BSE) — update before use", f_note)
put(asn, "A6", "Shares issued"); put(asn, "B6", 186374860, f_in, NUM)
put(asn, "G6", AR + "p.2 / Note 21", f_note)
put(asn, "A7", "Treasury shares"); put(asn, "B7", 3507006, f_in, NUM)
put(asn, "G7", AR + "Treasury shares section (31 Dec 2025)", f_note)
put(asn, "A8", "Shares outstanding", f_bold); put(asn, "B8", "=B6-B7", f_calc, NUM, bold=True)

section(asn, 10, "Cost of capital (WACC)", 7)
put(asn, "A11", "Risk-free rate (HUF)"); put(asn, "B11", 0.068, f_in, PCT, fill=fill_key)
put(asn, "G11", "Assumption: approx. 10-year Hungarian government bond yield — verify on akk.hu", f_note)
put(asn, "A12", "Equity beta"); put(asn, "B12", 0.75, f_in, "0.00", fill=fill_key)
put(asn, "G12", "Assumption: large-cap pharma is defensive (beta below 1)", f_note)
put(asn, "A13", "Equity risk premium"); put(asn, "B13", 0.05, f_in, PCT)
put(asn, "G13", "Assumption: mature-market ERP; Hungarian country risk already in the HUF risk-free rate", f_note)
put(asn, "A14", "Cost of equity (CAPM)", f_bold); put(asn, "B14", "=B11+B12*B13", fmt=PCT, bold=True)
put(asn, "A15", "Pre-tax cost of debt"); put(asn, "B15", 0.07, f_in, PCT)
put(asn, "G15", "Assumption: debt is tiny, so this barely affects WACC", f_note)
put(asn, "A16", "Tax rate"); put(asn, "B16", 0.18, f_in, PCT, fill=fill_key)
put(asn, "G16", "2024–2025 effective rate was 14.8%–18.4% (see Historicals row 12)", f_note)
put(asn, "A17", "After-tax cost of debt"); put(asn, "B17", "=B15*(1-B16)", fmt=PCT)
put(asn, "A18", "Market value of equity (HUF m)"); put(asn, "B18", "=B5*B8/1000000", fmt=NUM)
put(asn, "A19", "Gross debt incl. leases (HUF m)")
put(asn, "B19", "=Historicals!D34+Historicals!D35", f_link, NUM)
put(asn, "A20", "Equity weight E/(D+E)"); put(asn, "B20", "=B18/(B18+B19)", fmt=PCT)
put(asn, "A21", "Debt weight D/(D+E)"); put(asn, "B21", "=1-B20", fmt=PCT)
put(asn, "A22", "WACC", f_bold); put(asn, "B22", "=B20*B14+B21*B17", fmt=PCT, bold=True, fill=fill_out)

section(asn, 24, "Terminal value", 7)
put(asn, "A25", "Terminal growth rate (nominal HUF)"); put(asn, "B25", 0.03, f_in, PCT, fill=fill_key)
put(asn, "G25", "Assumption: around the MNB's 3% inflation target; must stay below WACC", f_note)

section(asn, 27, "Vraylar (cariprazine) royalties — US loss of exclusivity ~Sep 2029", 7)
put(asn, "A28", "Vraylar royalty share of 2025 revenue"); put(asn, "B28", 0.27, f_in, PCT, fill=fill_key)
put(asn, "G28", "Estimate: ~HUF 250bn of royalties (iocharts.io analysis); Richter does not disclose it exactly — check the Annual Report segment notes", f_note)
put(asn, "A29", "EBIT margin on royalty revenue"); put(asn, "B29", 0.80, f_in, PCT, fill=fill_key)
put(asn, "G29", "Assumption: royalties carry almost no cost of sales or marketing", f_note)
put(asn, "A30", "Implied core (non-Vraylar) EBIT margin 2025")
put(asn, "B30", "=(Historicals!D8-Historicals!D4*B28*B29)/(Historicals!D4*(1-B28))", f_link, PCT)
put(asn, "G30", "Backed out of 2025 group EBIT: what the rest of the business earns", f_note)

header_row(asn, 32, ["Operating drivers", "2026E", "2027E", "2028E", "2029E", "2030E", "Basis"])
drivers = [
    (33, "Vraylar royalty growth", [0.10, 0.10, 0.08, -0.25, -0.60],
     "Growing to 2028; US generics from ~Sep 2029 (Richter investor materials) erode royalties"),
    (34, "Core revenue growth", [0.08, 0.08, 0.07, 0.07, 0.06],
     "2026 guidance: high-single-digit group growth; women's health, neurology, biosimilars"),
    (36, "D&A % of revenue", [0.06, 0.06, 0.06, 0.06, 0.06],
     "2024 6.2%, 2025 6.5% incl. impairment"),
    (37, "Capex % of revenue", [0.07, 0.07, 0.07, 0.07, 0.07],
     "2024 7.4%, 2025 7.1% (PP&E + intangibles)"),
    (38, "Operating NWC % of revenue", [0.43, 0.43, 0.43, 0.43, 0.43],
     "2024 44.6%, 2025 43.4%"),
]
for row, label, vals, basis in drivers:
    put(asn, f"A{row}", label)
    for col, v in zip("BCDEF", vals):
        put(asn, f"{col}{row}", v, f_in, PCT)
    put(asn, f"G{row}", basis, f_note)
put(asn, "A35", "Core EBIT margin")
for col in "BCDEF":
    put(asn, f"{col}35", "=$B$30", fmt=PCT)
put(asn, "G35", "Held at 2025 level; type a value over any year to model margin expansion", f_note)
asn.freeze_panes = "B3"

# ---------------------------------------------------------------- DCF
d = wb.create_sheet("DCF", 2)
setup(d, {"A": 44, "B": 13, "C": 13, "D": 13, "E": 13, "F": 13, "G": 13})
put(d, "A1", "DCF — free cash flow to the firm (HUF m)", f_title)
put(d, "A2", "2025A = reported base year. Cash flows discounted to 31 Dec 2025 (end-of-year convention).", f_note)
header_row(d, 4, ["", "2025A", "2026E", "2027E", "2028E", "2029E", "2030E"])
FC = "CDEFG"            # forecast columns on DCF
AC = "BCDEF"            # matching driver columns on Assumptions
R = dict(per=5, roy=6, core=7, rev=8, gr=9, ebit=10, mgn=11, tax=12, nopat=13, da=14,
         capex=15, nwc=16, dnwc=17, fcf=18, df=19, pv=20)

put(d, f"A{R['per']}", "Discount period (years)")
put(d, f"B{R['per']}", 0, f_in, "0")
labels = {
    "roy": ("Vraylar royalty revenue", False), "core": ("Core revenue", False),
    "rev": ("Total revenue", True), "gr": ("  Growth", False),
    "ebit": ("EBIT", True), "mgn": ("  EBIT margin", False),
    "tax": ("Less: taxes on EBIT", False), "nopat": ("NOPAT", True),
    "da": ("Plus: D&A", False), "capex": ("Less: capex", False),
    "nwc": ("Operating NWC (level)", False), "dnwc": ("Less: increase in NWC", False),
    "fcf": ("Free cash flow to firm (FCFF)", True), "df": ("Discount factor", False),
    "pv": ("PV of FCFF", True),
}
for k, (lab, b) in labels.items():
    put(d, f"A{R[k]}", lab, f_bold if b else f_calc)

# base year
put(d, f"B{R['roy']}", f"=Historicals!D4*Assumptions!B28", f_link, NUM)
put(d, f"B{R['core']}", f"=Historicals!D4-B{R['roy']}", f_link, NUM)
put(d, f"B{R['rev']}", f"=B{R['roy']}+B{R['core']}", fmt=NUM, bold=True)
put(d, f"B{R['gr']}", "=Historicals!D5", f_link, PCT)
put(d, f"B{R['ebit']}", "=Historicals!D8", f_link, NUM, bold=True)
put(d, f"B{R['mgn']}", f"=B{R['ebit']}/B{R['rev']}", fmt=PCT)
put(d, f"B{R['da']}", "=Historicals!D16", f_link, NUM)
put(d, f"B{R['capex']}", "=-Historicals!D20", f_link, NUM)
put(d, f"B{R['nwc']}", "=Historicals!D28", f_link, NUM)

for i, c in enumerate(FC):
    p, a = "BCDEF"[i], AC[i]
    put(d, f"{c}{R['per']}", f"={p}{R['per']}+1", fmt="0")
    put(d, f"{c}{R['roy']}", f"={p}{R['roy']}*(1+Assumptions!{a}33)", fmt=NUM)
    put(d, f"{c}{R['core']}", f"={p}{R['core']}*(1+Assumptions!{a}34)", fmt=NUM)
    put(d, f"{c}{R['rev']}", f"={c}{R['roy']}+{c}{R['core']}", fmt=NUM, bold=True)
    put(d, f"{c}{R['gr']}", f"={c}{R['rev']}/{p}{R['rev']}-1", fmt=PCT)
    put(d, f"{c}{R['ebit']}", f"={c}{R['roy']}*Assumptions!$B$29+{c}{R['core']}*Assumptions!{a}35",
        fmt=NUM, bold=True)
    put(d, f"{c}{R['mgn']}", f"={c}{R['ebit']}/{c}{R['rev']}", fmt=PCT)
    put(d, f"{c}{R['tax']}", f"=-{c}{R['ebit']}*Assumptions!$B$16", fmt=NUM)
    put(d, f"{c}{R['nopat']}", f"={c}{R['ebit']}+{c}{R['tax']}", fmt=NUM, bold=True)
    put(d, f"{c}{R['da']}", f"={c}{R['rev']}*Assumptions!{a}36", fmt=NUM)
    put(d, f"{c}{R['capex']}", f"=-{c}{R['rev']}*Assumptions!{a}37", fmt=NUM)
    put(d, f"{c}{R['nwc']}", f"={c}{R['rev']}*Assumptions!{a}38", fmt=NUM)
    put(d, f"{c}{R['dnwc']}", f"=-({c}{R['nwc']}-{p}{R['nwc']})", fmt=NUM)
    put(d, f"{c}{R['fcf']}", f"={c}{R['nopat']}+{c}{R['da']}+{c}{R['capex']}+{c}{R['dnwc']}",
        fmt=NUM, bold=True)
    put(d, f"{c}{R['df']}", f"=1/(1+$C$23)^{c}{R['per']}", fmt=DF)
    put(d, f"{c}{R['pv']}", f"={c}{R['fcf']}*{c}{R['df']}", fmt=NUM, bold=True)
for c in "BCDEFG":
    for k in ("rev", "nopat", "fcf"):
        d[f"{c}{R[k]}"].border = top_border

header_row(d, 22, ["Valuation", "", "HUF m", "", "", "", ""])
val = [
    (23, "WACC", "=Assumptions!B22", PCT, f_link),
    (24, "Terminal growth", "=Assumptions!B25", PCT, f_link),
    (25, "Sum of PV of FCFF 2026–2030", "=SUM(C20:G20)", NUM, f_calc),
    (26, "Terminal-year FCFF excl. Vraylar royalties", "=G18-G6*Assumptions!B29*(1-Assumptions!B16)", NUM, f_calc),
    (27, "Terminal value at 2030 (Gordon growth)", "=C26*(1+C24)/(C23-C24)", NUM, f_calc),
    (28, "PV of terminal value", "=C27*G19", NUM, f_calc),
    (29, "Enterprise value", "=C25+C28", NUM, f_bold),
    (30, "  Terminal value as % of EV", "=C28/C29", PCT, f_calc),
    (31, "Plus: cash and equivalents", "=Historicals!D31", NUM, f_link),
    (32, "Plus: current financial assets", "=Historicals!D32", NUM, f_link),
    (33, "Plus: associates & non-current financial assets", "=Historicals!D33", NUM, f_link),
    (34, "Less: borrowings", "=-Historicals!D34", NUM, f_link),
    (35, "Less: lease liabilities", "=-Historicals!D35", NUM, f_link),
    (36, "Less: fair-value financial liabilities", "=-Historicals!D36", NUM, f_link),
    (37, "Less: non-controlling interest", "=-Historicals!D37", NUM, f_link),
    (38, "Equity value", "=C29+SUM(C31:C37)", NUM, f_bold),
    (39, "Shares outstanding (m)", "=Assumptions!B8/1000000", NUM1, f_link),
    (40, "Implied value per share (HUF)", "=C38/C39", NUM, f_bold),
    (41, "Current share price (HUF)", "=Assumptions!B5", NUM, f_link),
    (42, "Upside / (downside)", "=C40/C41-1", PCT, f_bold),
    (44, "Implied EV / 2025 EBIT", "=C29/B10", MULT, f_calc),
    (45, "Implied EV / 2025 EBITDA", "=C29/Historicals!D22", MULT, f_link),
    (46, "Implied P/E on 2025 earnings", "=C38/Historicals!D13", MULT, f_link),
    (47, "Market EV / 2025 EBIT (at current price)", "=(Assumptions!B18-SUM(C31:C37))/B10", MULT, f_link),
]
for row, label, formula, fmt, font in val:
    put(d, f"A{row}", label, f_bold if font is f_bold else f_calc)
    put(d, f"C{row}", formula, font, fmt)
put(d, "D26", "Royalties assumed gone after 2030, so they are excluded from the perpetuity", f_note)
for row in (29, 38):
    d[f"C{row}"].border = top_border
for row in (40, 42):
    d[f"A{row}"].fill = fill_out
    d[f"C{row}"].fill = fill_out
d.freeze_panes = "B5"

# ---------------------------------------------------------------- Sensitivity
s = wb.create_sheet("Sensitivity", 3)
setup(s, {"A": 3, "B": 16, "C": 12, "D": 12, "E": 12, "F": 12, "G": 12})
put(s, "B1", "Sensitivity analysis", f_title)
put(s, "B2", "Each cell re-runs the full DCF with that WACC and terminal growth rate.", f_note)

steps = [-0.01, -0.005, 0, 0.005, 0.01]

def grid(top, title, upside):
    put(s, f"B{top}", title, f_bold)
    put(s, f"B{top+1}", "WACC ↓ / g →", f_note)
    for j, st in enumerate(steps):
        put(s, f"{'CDEFG'[j]}{top+1}", f"=DCF!$C$24+({st})", f_link, PCT, bold=True)
    for i, st in enumerate(steps):
        r = top + 2 + i
        put(s, f"B{r}", f"=DCF!$C$23+({st})", f_link, PCT, bold=True)
        for j in range(5):
            col = "CDEFG"[j]
            w, g = f"$B{r}", f"{col}${top+1}"
            value = (f"(SUMPRODUCT(DCF!$C$18:$G$18,1/(1+{w})^DCF!$C$5:$G$5)"
                     f"+DCF!$C$26*(1+{g})/({w}-{g})/(1+{w})^DCF!$G$5"
                     f"+SUM(DCF!$C$31:$C$37))/DCF!$C$39")
            formula = f"={value}/DCF!$C$41-1" if upside else f"={value}"
            c = put(s, f"{col}{r}", formula, fmt=PCT if upside else NUM)
            if i == 2 and j == 2:
                c.fill = fill_out
                c.font = Font(name=F, size=10, bold=True)

grid(4, "Implied value per share (HUF)", upside=False)
grid(13, "Upside / (downside) vs current price", upside=True)
put(s, "B21", "Base case shaded. WACC and growth steps are ±0.5 and ±1.0 percentage points.", f_note)

for ws in wb.worksheets:
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToHeight = 0

wb.calculation.fullCalcOnLoad = True
OUT = Path(__file__).resolve().parent.parent / "output" / "Richter_Gedeon_DCF.xlsx"
wb.save(OUT)
print("saved", OUT)
