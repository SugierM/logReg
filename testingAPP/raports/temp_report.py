from fpdf import FPDF
from fpdf.outline import TableOfContents
import os

global CHAPTER
global SUBCHAPTER
CHAPTER = 1
SUBCHAPTER = 1
# Custom parts
def insert_section(pdf: FPDF, name, text):
    """
    Function to write section of report
    """
    global CHAPTER
    global SUBCHAPTER
    SUBCHAPTER = 1

    name = name + f" {CHAPTER}"
    pdf.add_page()
    pdf.start_section(name, level=0)
    pdf.set_font('helvetica', 'B', 22)
    pdf.cell(0, 16, name)
    pdf.ln()
    pdf.set_font('helvetica', '', 16)
    pdf.multi_cell(0, None, text=text)
    pdf.ln()
    CHAPTER += 1



def insert_subsection(pdf: FPDF, name, text, level):
    """
    Function to write subsection of report
    """
    global SUBCHAPTER
    global CHAPTER

    if level == 0:
        # For my better experience in the future
        raise Exception("For chapter level section use insert_section() function")
    
    elif level == 1:
        SUBCHAPTER += 1
        name = name + f" {CHAPTER - 1}.{SUBCHAPTER - 1}"

    else:
        name = name + f" {CHAPTER - 1}.{SUBCHAPTER - 1}" 
    
    pdf.start_section(name, level=level)
    pdf.set_font('helvetica', 'B', 20)
    pdf.cell(0, 16, name)
    pdf.ln()
    pdf.set_font('helvetica', '', 16)
    pdf.multi_cell(0, None, text=text)
    pdf.ln()

# Add custom header and footer
class PDF(FPDF):
    def header(self):
        pdf.set_font('helvetica', 'B', 16)
        pdf.cell(0, 10, "Header", align='L')
        self.ln(10)


    def footer(self):
        self.set_y(-15) # 15 units from the bottom (15 mm)
        pdf.set_font('helvetica', 'B', 10)
        page_num = f"Page {self.page_no()}"
        self.cell(0, 10, page_num, align="R")


# Config
pdf = PDF(orientation='P', unit='mm', format='A4')
pdf.set_author(author="logReg not even an industry")
pdf.set_font('helvetica', '', 16)
pdf.set_auto_page_break(auto=True, margin=15) # 15 units - 15 mm
pdf.alias_nb_pages()

# Title page
pdf.add_page()
pdf.cell(0, 10, f"Author: {pdf.author}")

# Table Page with Table of contents
pdf.add_page()
toc = TableOfContents()
pdf.insert_toc_placeholder(toc.render_toc, allow_extra_pages=False)

# First meaningful page
insert_section(pdf, "Chapter", "None")
texcik = """
None BOBN
EHOSD
daslkdhajkl
edalskjhda9s8dya9sf6asd87f6sd89f6ds780f6ds
adoisuyd89as76f8a7s6dakjsdhALJ|
"""
# Subsection
insert_subsection(pdf, "Chapter", "None", 1)
insert_subsection(pdf, "Chapter", "None", 2)

insert_subsection(pdf, "Chapter", texcik, 1)
insert_subsection(pdf, "Chapter", "None", 2)
insert_subsection(pdf, "Chapter", texcik, 3)

insert_subsection(pdf, "Chapter", "None", 1)
insert_subsection(pdf, "Chapter", "None", 2)
# 2 Chapter
insert_section(pdf, "Chapter", "None")



# Save file 
# FOR NOW IT WILL BE HERE
current_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(current_dir, "out_1.pdf")
pdf.output(output_path) 