#!/usr/bin/env python3
# NOTE - Relies on unix commandline tool pdftotext from poppler to do PDF conversion
# NOTE - Relies on pip-installable "openpyxl" and "xlwt" for Excel 
import re
import subprocess
import pandas as pd
# import glob
import os
# import argparse

class PDFParser:

    def __init__(self, pdf_file):
        self.pdf_file = pdf_file
        # self.pdf_reader = PyPDF2.PdfReader(self.pdf_file)
        self.text = self._extract_text()

    def _extract_text(self):
        cmd = 'pdftotext -layout {} -'.format(self.pdf_file)
        # print (cmd)
        shell_capture = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
        # print(shell_capture)
        return shell_capture.stdout

class ReportParser(PDFParser):
    def __init__(self, pdf_file):
        super().__init__(pdf_file)
        self.annos = {
            'PROTOCOL':                   {'pattern':r'', 'value':''},
            'SUBJECTID':                  {'pattern':r'', 'value':''},
            'LGMID':                      {'pattern':r'', 'value':''},
            'SEX':                        {'pattern':r'', 'value':''},
            'YEAROFBIRTH':                {'pattern':r'', 'value':''},
            'GENENAME_FAMILIAL':          {'pattern':r'', 'value':''},
            'CHROMOSOME_FAMILIAL':        {'pattern':r'', 'value':''},
            'POSITION_FAMILIAL':          {'pattern':r'', 'value':''},
            'REFERENCE_FAMILIAL':         {'pattern':r'', 'value':''},
            'ALTERNATE_FAMILIAL':         {'pattern':r'', 'value':''},
            'TRANSCRIPT_FAMILIAL':        {'pattern':r'', 'value':''},
            'C_SYNTAX_FAMILIAL':          {'pattern':r'', 'value':''},
            'P_SYNTAX_FAMILIAL':          {'pattern':r'', 'value':''},
            'ZYGOSITY_FAMILIAL':          {'pattern':r'', 'value':''},
            'GENENAME_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            'CHROMOSOME_NON-FAMILIAL':    {'pattern':r'', 'value':''},
            'POSITION_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            'REFERENCE_NON-FAMILIAL':     {'pattern':r'', 'value':''},
            'ALTERNATE_NON-FAMILIAL':     {'pattern':r'', 'value':''},
            'TRANSCRIPT_NON-FAMILIAL':    {'pattern':r'', 'value':''},
            'C_SYNTAX_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            'P_SYNTAX_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            'ZYGOSITY_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            'APOE_C130R_rs429358_STATUS': {'pattern':r'', 'value':''},
            'APOE_R176C_rs7412_STATUS':   {'pattern':r'', 'value':''},
            'BDNF_V66M_rs6265_STATUS':    {'pattern':r'', 'value':''}}
    
    # Update annos with report-specific regex patterns
    def _update_patterns(self, pattern_dict):
        for k,v in pattern_dict.items():
            # print(k)
            self.annos[k]['pattern'] = v

    def _get_anno(self, anno_name, pattern_str):

        pattern = re.compile(pattern_str, flags=re.IGNORECASE)
        result = re.search(pattern, self.text)
        extracted = result.group(1)
        # print(extracted)
        self.annos[anno_name]['value'] = extracted
    
    def _loop_get_anno(self):
        for anno_key, v in self.annos.items():
            # self._get_anno(anno_key, self.annos[anno_key]['pattern'])
            try: 
                # print(self.annos[anno_key]['pattern'])
                # print(anno_key)
                self._get_anno(anno_key, self.annos[anno_key]['pattern'])
                # print(self.annos[anno_key]['pattern'])
            except:
                print('        ERROR: Couldn\'t get {} from PDF'.format(anno_key), end='\n')

    def _generate_df(self):
        d = self.annos
        df = pd.DataFrame(
            {k: [v['value']] for k, v in d.items()},
            columns=d.keys()
        )
        # return df.to_string(index=False))
        return df



class GNXParser(ReportParser):
    def __init__(self, pdf_file):
        super().__init__(pdf_file)
        self.gnx_patterns = {
            'PROTOCOL':                   r'CLINICAL GENOMICS REPORT\n+.+\n+(\w+)',
            'SUBJECTID':                  r'CLINICAL GENOMICS REPORT\n+.+\n+\w+[,|\s+]\s+(\d+)',
            'LGMID':                      r'Accession:\s+(\w+.+?\w*)\s',
            'SEX':                        r'Sex:\s+(\w+)',
            'YEAROFBIRTH':                r'DOB: \d+\/\d+\/(\d+)',
            'GENENAME_FAMILIAL':          r'Genomic location .+\nTranscript\n+(\w+)',
            'CHROMOSOME_FAMILIAL':        r'Level 1.+\n.+Genomic location .+\nTranscript\n\n.+\n\s+.+p\.\w+\s+\w+\s+(chr\w+)',
            'POSITION_FAMILIAL':          r'Level 1.+\n.+Genomic location .+\nTranscript\n\n.+\n\s+.+p\.\w+\s+\w+\s+chr\w+:(\d+)',
            'REFERENCE_FAMILIAL':         r'Level 1.+\n.+Genomic location .+\nTranscript\n\n.+\n\s+.+p\.\w+\s+\w+\s+chr\w+:\d+\s+(\w)',
            'ALTERNATE_FAMILIAL':         r'Level 1.+\n.+Genomic location .+\nTranscript\n\n.+\n\s+.+p\.\w+\s+\w+\s+chr\w+:\d+\s+\w>(\w)',
            'TRANSCRIPT_FAMILIAL':        r'Level 1.+\n.+Genomic location .+\nTranscript\n\n.+\n\s+.+p\.\w+\s+\w+\s+chr\w+:\d+\s+\w>\w\n(\w+.+)',
            'C_SYNTAX_FAMILIAL':          r'Level 1.+\n.+Genomic location .+\nTranscript\n+\w+\n\s+(c.+?)\s',
            'P_SYNTAX_FAMILIAL':          r'Level 1.+\n.+Genomic location .+\nTranscript\n+\w+\n\s+c.+?\s+(p\.\w+)',
            'ZYGOSITY_FAMILIAL':          r'Level 1.+\n.+Genomic location .+\nTranscript\n\n.+\n\s+.+p\.\w+\s+(\w+)',
            'APOE_C130R_rs429358_STATUS': r'(homo\w*|hetero\w*).*rs429358',
            'APOE_R176C_rs7412_STATUS':   r'(homo\w*|hetero\w*).*45412079C',
            'BDNF_V66M_rs6265_STATUS':    r'(homo\w*|hetero\w*).*v66M'}
        self._update_patterns(self.gnx_patterns)
        self._loop_get_anno()
        self.df = self._generate_df()

class CGWParser(ReportParser):
    def __init__(self, pdf_file):
        super().__init__(pdf_file   )
        self.cgw_patterns = {
            'PROTOCOL':                   r'Name:\s+(\w+.+?)[,|\s]',
            'SUBJECTID':                  r'Name:\s+\w+.+?[,|\s]\s+(\w+)',
            'LGMID':                      r'Accession\nName.+\s+\d+\s+(.+)',
            'SEX':                        r'Gender:\s+(\w+)',
            'YEAROFBIRTH':                r'DOB:\s+\d+/\d+/(\d+)',
            'GENENAME_FAMILIAL':          r'for the Familial Variant:\s\w+[,]\s*(\w+)',
            'CHROMOSOME_FAMILIAL':        r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\((chr\w+)',
            'POSITION_FAMILIAL':          r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\(chr\w+:\w+\.(\d+)',
            'REFERENCE_FAMILIAL':         r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\(chr\w+:\w+\.\d+\w>(\w)',
            'ALTERNATE_FAMILIAL':         r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\(chr\w+:\w+\.\d+(\w)>',
            'TRANSCRIPT_FAMILIAL':        r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\(chr.+\n\s+(\w+.+?):',
            'C_SYNTAX_FAMILIAL':          r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\(chr.+\n\s+\w+.+?\:(c.+?)\s',
            'P_SYNTAX_FAMILIAL':          r'CLINICAL GENOMICS REPORT.+\n+\s+\w+\s+\(chr.+\n\s+\w+.+?\:c.+?\s+.+\:(p.+)',
            'ZYGOSITY_FAMILIAL':          r'for the Familial Variant:\s(\w+)',
            'APOE_C130R_rs429358_STATUS': r'(hetero\w+|homo\w+).*C130R',
            'APOE_R176C_rs7412_STATUS':   r'(hetero\w+|homo\w+).+R176C',
            'BDNF_V66M_rs6265_STATUS':    r'(hetero\w+|homo\w+).+V66'}
        self._update_patterns(self.cgw_patterns)
        self._loop_get_anno()
        self.df = self._generate_df() 

def main():
    import argparse

    # Create the parser
    parser = argparse.ArgumentParser(description='A utility to pull information from CGW and GNX study report PDFs')

    # Add arguments to the parser
    parser.add_argument('-d', '--dir', help='Directory containing PDFs')
    parser.add_argument('-e', '--excel', help='Specify Excel output path')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Function to output list of summary DataFrame rows from directory of PDFs
    def get_pdf_dfs(pdf_dir):
        pdf_df_list = []
        for pdf_path in os.listdir(pdf_dir):
            full_pdf_path = os.path.join(pdf_dir, pdf_path)
            print ('\n  -> Reading {}'.format(full_pdf_path))
            if "CGW" in pdf_path and ".pdf" in pdf_path:
                pdf_df_list.append(CGWParser(full_pdf_path).df)
            elif "GNX" in pdf_path and ".pdf" in pdf_path:
                pdf_df_list.append(GNXParser(full_pdf_path).df)
            else:
                print("\nWarning: Couldn't parse file {}\n".format(pdf_path))
        return pdf_df_list
    
    # Get PDF DataFrames list
    df_list = get_pdf_dfs(args.dir)
    # Concatenate list of DataFrames int a single DataFrame
    collapsed_df = pd.concat(df_list)
    # Write to Excel spreadsheet
    collapsed_df.to_excel(args.excel, index=False, engine='openpyxl')

if __name__ == "__main__":
    main()

# # --- Testing Cruft ---
# def get_pdf_dfs(pdf_dir):
#     pdf_df_list = []
#     for pdf_path in os.listdir(pdf_dir):
#         full_pdf_path = os.path.join(pdf_dir, pdf_path)
#         print ('\n  -> Reading {}'.format(full_pdf_path))
#         if "CGW" in pdf_path and ".pdf" in pdf_path:
#             pdf_df_list.append(CGWParser(full_pdf_path).df)
#         elif "GNX" in pdf_path and ".pdf" in pdf_path:
#             pdf_df_list.append(GNXParser(full_pdf_path).df)
#         else:
#             print("\nWarning: Couldn't parse file {}\n".format(pdf_path))
#     return pdf_df_list
# this_report = GNXParser(full_pdf_path)
# this_report.text
# this_report.cgw_patterns
# this_report.annos

# pattern_str = 'APOE Genotype.+$\n.*(hetero\w+|homo\w+).+C130R.*$'
# pattern_str = '(BDNF Genotype Status)'
            #   'BDNF Genotype Status.*\n\s*(hetero\w+|homo\w+)'
# pattern_str = '^.*(homo\w*|hetero\w*).*v66M'
# pattern_str = '(homo\w*|hetero\w*).*v66M'
# pattern = re.compile(pattern_str, flags=re.IGNORECASE)
# result = re.search(pattern, this_report.text)
# result.group(1)
# extracted = result.group(1)
# extracted