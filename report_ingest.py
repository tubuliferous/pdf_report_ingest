#!/usr/bin/env python3
# NOTE - Relies on unix commandline tool pdftotext from poppler to do PDF conversion
import re
import subprocess
import pandas as pd
# import glob
import os
# import argparse
import shlex

class PDFParser:
    def __init__(self, pdf_file):
        self.pdf_file = shlex.quote(pdf_file) # Make path shell-safe
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
            # 'GENENAME_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            # 'CHROMOSOME_NON-FAMILIAL':    {'pattern':r'', 'value':''},
            # 'POSITION_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            # 'REFERENCE_NON-FAMILIAL':     {'pattern':r'', 'value':''},
            # 'ALTERNATE_NON-FAMILIAL':     {'pattern':r'', 'value':''},
            # 'TRANSCRIPT_NON-FAMILIAL':    {'pattern':r'', 'value':''},
            # 'C_SYNTAX_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            # 'P_SYNTAX_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            # 'ZYGOSITY_NON-FAMILIAL':      {'pattern':r'', 'value':''},
            'APOE_C130R_rs429358_STATUS': {'pattern':r'', 'value':''},
            'APOE_R176C_rs7412_STATUS':   {'pattern':r'', 'value':''},
            'BDNF_V66M_rs6265_STATUS':    {'pattern':r'', 'value':''}}
        self.df = pd.DataFrame()
    # Update annos with report-specific regex patterns
    def _update_patterns(self, pattern_dict):
        for k,v in pattern_dict.items():
            # print(k)
            self.annos[k]['pattern'] = v

    def _get_anno(self, anno_name, pattern_str):
        # pattern = re.compile(pattern_str, flags=re.IGNORECASE)
        pattern = re.compile(pattern_str, flags=re.S)
        # pattern = re.compile(pattern_str)
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
                print("        ERROR: Couldn't get {} from PDF".format(anno_key), end='\n')
    # Make single-line DataFrame from annotations of interest from reports
    def _generate_df(self):
        d = self.annos
        df = pd.DataFrame(
            {k: [v['value']] for k, v in d.items()},
            columns=d.keys()
        )
        self.df = df
    # Add information about revision 
    def _update_df_revision_col(self):
        pattern_str = '[Aa]mendment sign out'
        pattern = re.compile(pattern_str, flags=re.S)
        matches = re.findall(pattern, self.text)
        rev_count = len(matches)
        self.df['REVISIONS'] = rev_count

class GNXParser(ReportParser):
    def __init__(self, pdf_file):
        super().__init__(pdf_file)
        self.gnx_patterns = {
            'PROTOCOL':                   r'CLINICAL GENOMICS REPORT\n+.+\n+(\w+)',
            'SUBJECTID':                  r'CLINICAL GENOMICS REPORT\n+.+\n+\w+[,|\s+]\s+(\d+)',
            'LGMID':                      r'Accession:\s+(\w+.+?\w*)\s',
            'SEX':                        r'Sex:\s+(\w+)',
            'YEAROFBIRTH':                r'DOB: \d+\/\d+\/(\d+)',
            'GENENAME_FAMILIAL':          r'for the familial variant.+?([A-Z0-9][A-Z0-9]+).+APOE Genotype Status',
            'CHROMOSOME_FAMILIAL':        r'Level 1.+(chr\w)+.+Level 2',
            'POSITION_FAMILIAL':          r'Level 1.+chr\w+:(\d+).+Level 2',
            'REFERENCE_FAMILIAL':         r'Level 1.+?\s(\w)>\w.+Level 2',
            'ALTERNATE_FAMILIAL':         r'Level 1.+?\s\w>(\w).+Level 2',
            'TRANSCRIPT_FAMILIAL':        r'Level 1.+(NM_\S+).+Level 2',
            'C_SYNTAX_FAMILIAL':          r'Level 1.+(c\..+?)\s.+Level 2',
            'P_SYNTAX_FAMILIAL':          r'Level 1.+(p\..+?)\s.+Level 2',
            'ZYGOSITY_FAMILIAL':          r'Level 1.+([Hh]etero\w+|[Hh]omo\w+).+Level\s+2',
            'APOE_C130R_rs429358_STATUS': r'APOE Genotype Status.*([Hh]etero\w+|[Hh]omo\w+).*C130R',
            'APOE_R176C_rs7412_STATUS':   r'C130R \(chr19.+([Hh]etero\w+|[Hh]omo\w+).+ variant p\.R',
            'BDNF_V66M_rs6265_STATUS':    r'BDNF Genotype Status.+([Hh]etero\w+|[Hh]omo\w+).+was\s+detected'}
        self._update_patterns(self.gnx_patterns)
        self._loop_get_anno()
        self._generate_df()
        self._update_df_revision_col()

class CGWParser(ReportParser):
    def __init__(self, pdf_file):
        super().__init__(pdf_file   )
        self.cgw_patterns = {
            'PROTOCOL':                   r'Name:\s+(DIAN.*?)[,|\s]',
            'SUBJECTID':                  r'Name:\s+DIAN.*?[,|\s]\s+(\w+)',
            'LGMID':                      r'Name:\s+DIAN.*?[,|\s]\s+\w+\s+(\w+[\-|.*]\w+)',
            'SEX':                        r'Gender:\s+(\w+)',
            'YEAROFBIRTH':                r'DOB:\s+\d+/\d+/(\d+)',
            'GENENAME_FAMILIAL':          r'for the Familial Variant.+?([A-Z0-9][A-Z0-9]+).+?APOE\s+Genotype',
            'CHROMOSOME_FAMILIAL':        r'The\sfollowing\sDNA\svariant.+?(chr\w+).+\n.+NM_.+NP',
            'POSITION_FAMILIAL':          r'The\sfollowing\sDNA\svariant.+?chr\w+:g.(\d+).+\n.+NM_.+NP',
            'REFERENCE_FAMILIAL':         r'The\sfollowing\sDNA\svariant.+?chr\w+:g\.\d+(\w)',
            'ALTERNATE_FAMILIAL':         r'The\sfollowing\sDNA\svariant.+?chr\w+:g\.\d+\w>(\w)',
            'TRANSCRIPT_FAMILIAL':        r'consistent with known familial variation.+?(NM_\w+[\.|\w]\w*)',
            'C_SYNTAX_FAMILIAL':          r'consistent with known familial variation.+?NM_\w+[\.|\w]\w*:(c\..+?)\s',
            'P_SYNTAX_FAMILIAL':          r'consistent with known familial variation.+?NM_.+?(p\.\w+)',
            'ZYGOSITY_FAMILIAL':          r'for the Familial Variant.+?([Hh]etero\w+|[Hh]omo\w+).+APOE\sGenotype Status',
            'APOE_C130R_rs429358_STATUS': r'APOE Genotype Status.*([Hh]etero\w+|[Hh]omo\w+).*C130R',
            'APOE_R176C_rs7412_STATUS':   r'C130R \(chr19.+([Hh]etero\w+|[Hh]omo\w+).+ variant p\.R',
            'BDNF_V66M_rs6265_STATUS':    r'BDNF Genotype Status.+([Hh]etero\w+|[Hh]omo\w+).+was\s+detected'}
        self._update_patterns(self.cgw_patterns)
        self._loop_get_anno()
        self._generate_df() 
        self._update_df_revision_col()

def main():
    import argparse

    # Create the parser
    parser = argparse.ArgumentParser(description='A utility to pull information from CGW and GNX study report PDFs')

    # Add arguments to the parser
    parser.add_argument('-d', '--dir', help='Directory containing PDFs')
    parser.add_argument('-o', '--out', help='Specify output file path')

    # Parse the command-line arguments
    args = parser.parse_args()

    # Function to recursively find PDFs in all subdirectories
    def find_files(extension, directory):
        file_paths = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(extension):
                    file_paths.append(os.path.join(root, file))
        return file_paths

    # Function to identify PDF types of interest
    def get_pdf_type(pdf_path):
        # print(pdf_path)
        this_pdf = PDFParser(pdf_path)
        cmd = 'pdftotext -layout {} -'.format(pdf_path)
        # Check for GNX distinguisher
        gnx_pattern_str = r'genoox'
        gnx_pattern = re.compile(gnx_pattern_str, flags=re.IGNORECASE | re.S)
        gnx_match = re.search(gnx_pattern, this_pdf.text)
        # Check for cgw distinguisher
        cgw_color_pattern_str = r'Page 1.*version CGW'
        cgw_color_pattern = re.compile(cgw_color_pattern_str, flags=re.IGNORECASE | re.S)
        cgw_color_match = re.search(cgw_color_pattern, this_pdf.text)
        pdf_type = ''
        if gnx_match:
            pdf_type = 'gnx'
        elif cgw_color_match:
            pdf_type = 'cgw_color'
        else:
            pdf_type = 'other'
        return pdf_type

    # Function to output list of summary DataFrame rows from directory of PDFs
    def get_pdf_dfs(pdf_dir):
        pdf_paths = find_files('pdf', pdf_dir)
        pdf_df_list = []
        for pdf_path in pdf_paths:
            print ('\n  -> Reading {}'.format(pdf_path))
            pdf_type = get_pdf_type(pdf_path)
            if pdf_type == 'cgw_color':
                pdf_df_list.append(CGWParser(pdf_path).df)
            elif pdf_type == 'gnx':
                pdf_df_list.append(GNXParser(pdf_path).df)
            else:
                print("\nWarning: Couldn't parse file {}\n".format(pdf_path))
        return pdf_df_list
        
    # Get PDF DataFrames list
    df_list = get_pdf_dfs(args.dir)
    # Concatenate list of DataFrames int a single DataFrame
    collapsed_df = pd.concat(df_list)
    # Write to Excel spreadsheet
    collapsed_df.to_csv(args.out, index=False, sep='\t')

if __name__ == '__main__':
    main()
