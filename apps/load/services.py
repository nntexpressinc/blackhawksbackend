import pandas as pd
import numpy as np
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from django.core.files.base import ContentFile
import io
from collections import defaultdict
import re


class IFTAReportProcessor:
    def __init__(self, ifta_report_instance):
        self.ifta_report = ifta_report_instance
        self.fuel_data = None
        self.mile_data = None
        self.state_data = {}
        
    def process_files(self):
        """Main method to process the CSV file and generate the result Excel file"""
        try:
            # Process the main CSV file (assuming it's uploaded as 'fuel' file)
            self.process_csv_file()
            
            # Generate result Excel file
            result_file = self._generate_result_excel()
            
            # Save result file to model
            self.ifta_report.result_file = result_file
            self.ifta_report.save()
            
            return True
            
        except Exception as e:
            print(f"Error processing files: {str(e)}")
            raise e
    
    def process_csv_file(self):
        """Process the CSV file and extract all required data"""
        # Read CSV file - try different file sources
        csv_path = None
        if hasattr(self.ifta_report, 'fuel') and self.ifta_report.fuel:
            csv_path = self.ifta_report.fuel.path
        elif hasattr(self.ifta_report, 'mile') and self.ifta_report.mile:
            csv_path = self.ifta_report.mile.path
        
        if not csv_path:
            raise ValueError("No CSV file found")
            
        # Read CSV with proper handling of headers
        df = pd.read_csv(csv_path, header=None)
        
        # Find the main data table (starts with "Rate" column)
        main_table_start = None
        for idx, row in df.iterrows():
            if row.iloc[0] == 'Rate':
                main_table_start = idx
                break
        
        if main_table_start is None:
            raise ValueError("Could not find main data table starting with 'Rate'")
        
        # Extract headers and data
        headers = df.iloc[main_table_start].fillna('').tolist()
        data_rows = df.iloc[main_table_start + 1:].copy()
        
        # Process each state row
        self.state_data = {}
        for idx, row in data_rows.iterrows():
            if pd.isna(row.iloc[1]) or row.iloc[1] == '':  # Skip empty state rows
                continue
                
            state = row.iloc[1]
            if state in ['TOTAL', 'MPG'] or pd.isna(state):  # Skip total/summary rows
                continue
                
            # Extract state data
            rate = self._clean_numeric(row.iloc[0])
            
            # Extract mileage data for different units (100, 103, 104, 105)
            mileage_100 = self._clean_numeric(row.iloc[2])
            mileage_100_miles = self._clean_numeric(row.iloc[3])
            mileage_103 = self._clean_numeric(row.iloc[4])
            mileage_103_miles = self._clean_numeric(row.iloc[5])
            mileage_104 = self._clean_numeric(row.iloc[6])
            mileage_104_miles = self._clean_numeric(row.iloc[7])
            mileage_105 = self._clean_numeric(row.iloc[8])
            mileage_105_miles = self._clean_numeric(row.iloc[9])
            
            # Extract gallon and mileage totals
            gallon_per_state = self._clean_numeric(row.iloc[10])
            mileage_per_state = self._clean_numeric(row.iloc[11])
            
            # Extract tax calculations for each unit
            tax_100_taxable = self._clean_numeric(row.iloc[13])
            tax_100_net = self._clean_numeric(row.iloc[14])
            tax_100_amount = self._clean_numeric(row.iloc[15])
            
            tax_103_taxable = self._clean_numeric(row.iloc[18])
            tax_103_net = self._clean_numeric(row.iloc[19])
            tax_103_amount = self._clean_numeric(row.iloc[20])
            
            tax_104_taxable = self._clean_numeric(row.iloc[21])
            tax_104_net = self._clean_numeric(row.iloc[22])
            tax_104_amount = self._clean_numeric(row.iloc[23])
            
            tax_105_taxable = self._clean_numeric(row.iloc[24])
            tax_105_net = self._clean_numeric(row.iloc[25])
            tax_105_amount = self._clean_numeric(row.iloc[26])
            
            self.state_data[state] = {
                'rate': rate,
                'units': {
                    '100': {
                        'fuel': mileage_100,
                        'miles': mileage_100_miles,
                        'taxable_gallon': tax_100_taxable,
                        'net_taxable_gallon': tax_100_net,
                        'tax_amount': tax_100_amount
                    },
                    '103': {
                        'fuel': mileage_103,
                        'miles': mileage_103_miles,
                        'taxable_gallon': tax_103_taxable,
                        'net_taxable_gallon': tax_103_net,
                        'tax_amount': tax_103_amount
                    },
                    '104': {
                        'fuel': mileage_104,
                        'miles': mileage_104_miles,
                        'taxable_gallon': tax_104_taxable,
                        'net_taxable_gallon': tax_104_net,
                        'tax_amount': tax_104_amount
                    },
                    '105': {
                        'fuel': mileage_105,
                        'miles': mileage_105_miles,
                        'taxable_gallon': tax_105_taxable,
                        'net_taxable_gallon': tax_105_net,
                        'tax_amount': tax_105_amount
                    }
                },
                'gallon_per_state': gallon_per_state,
                'mileage_per_state': mileage_per_state
            }
    
    def _clean_numeric(self, value):
        """Clean and convert numeric values"""
        if pd.isna(value) or value == '':
            return 0
        
        # Handle string values with commas, dollar signs, parentheses
        if isinstance(value, str):
            # Remove commas, dollar signs, and spaces
            cleaned = value.replace(',', '').replace('$', '').replace(' ', '')
            
            # Handle negative values in parentheses
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
            
            try:
                return float(cleaned)
            except:
                return 0
        
        return float(value) if not pd.isna(value) else 0
    
    def _generate_result_excel(self):
        """Generate the result Excel file with comprehensive IFTA report"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"IFTA Report - {self.ifta_report.quorter}"
        
        # Set up styles
        title_font = Font(bold=True, size=16, color="FFFFFF")
        header_font = Font(bold=True, size=12, color="FFFFFF")
        subheader_font = Font(bold=True, size=11)
        total_font = Font(bold=True, size=11, color="000080")
        
        # Colors
        title_fill = PatternFill(start_color="2F4F4F", end_color="2F4F4F", fill_type="solid")
        header_fill = PatternFill(start_color="4682B4", end_color="4682B4", fill_type="solid")
        total_fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
        
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        current_row = 1
        
        # Main title
        ws.merge_cells(f'A{current_row}:M{current_row}')
        title_cell = ws.cell(row=current_row, column=1, value=f"IFTA REPORT - {self.ifta_report.quorter.upper()}")
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = Alignment(horizontal='center', vertical='center')
        current_row += 2
        
        # Table 1: State Summary
        current_row = self._add_state_summary_table(ws, current_row, header_font, header_fill, border)
        current_row += 2
        
        # Table 2: Unit Performance Summary
        current_row = self._add_unit_performance_table(ws, current_row, header_font, header_fill, border)
        current_row += 2
        
        # Table 3: Tax Summary by State
        current_row = self._add_tax_summary_table(ws, current_row, header_font, header_fill, border)
        current_row += 2
        
        # Table 4: MPG Analysis by Unit
        current_row = self._add_mpg_analysis_table(ws, current_row, header_font, header_fill, border)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 25)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        # Create Django file
        filename = f"ifta_report_{self.ifta_report.quorter.replace(' ', '_').lower()}.xlsx"
        return ContentFile(excel_buffer.getvalue(), name=filename)
    
    def _add_state_summary_table(self, ws, start_row, header_font, header_fill, border):
        """Add comprehensive state summary table"""
        # Title
        ws.merge_cells(f'A{start_row}:F{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value="STATE SUMMARY")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        start_row += 2
        
        # Headers
        headers = ['State', 'Tax Rate', 'Total Miles', 'Total Gallons', 'MPG', 'Total Tax']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        start_row += 1
        
        # Data rows
        total_miles = 0
        total_gallons = 0
        total_tax = 0
        
        for state, data in sorted(self.state_data.items()):
            state_miles = data['mileage_per_state']
            state_gallons = data['gallon_per_state']
            state_tax = sum(unit_data['tax_amount'] for unit_data in data['units'].values())
            mpg = state_miles / state_gallons if state_gallons > 0 else 0
            
            ws.cell(row=start_row, column=1, value=state)
            ws.cell(row=start_row, column=2, value=f"${data['rate']:.2f}")
            ws.cell(row=start_row, column=3, value=f"{state_miles:,.0f}")
            ws.cell(row=start_row, column=4, value=f"{state_gallons:,.0f}")
            ws.cell(row=start_row, column=5, value=f"{mpg:.2f}")
            ws.cell(row=start_row, column=6, value=f"${state_tax:,.2f}")
            
            # Apply borders
            for col in range(1, 7):
                ws.cell(row=start_row, column=col).border = border
                if col in [3, 4, 5, 6]:  # Right align numbers
                    ws.cell(row=start_row, column=col).alignment = Alignment(horizontal='right')
            
            total_miles += state_miles
            total_gallons += state_gallons
            total_tax += state_tax
            start_row += 1
        
        # Total row
        overall_mpg = total_miles / total_gallons if total_gallons > 0 else 0
        ws.cell(row=start_row, column=1, value="TOTAL")
        ws.cell(row=start_row, column=2, value="")
        ws.cell(row=start_row, column=3, value=f"{total_miles:,.0f}")
        ws.cell(row=start_row, column=4, value=f"{total_gallons:,.0f}")
        ws.cell(row=start_row, column=5, value=f"{overall_mpg:.2f}")
        ws.cell(row=start_row, column=6, value=f"${total_tax:,.2f}")
        
        for col in range(1, 7):
            cell = ws.cell(row=start_row, column=col)
            cell.font = Font(bold=True)
            cell.border = border
            cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
            if col in [3, 4, 5, 6]:
                cell.alignment = Alignment(horizontal='right')
        
        return start_row + 1
    
    def _add_unit_performance_table(self, ws, start_row, header_font, header_fill, border):
        """Add unit performance analysis table"""
        # Title
        ws.merge_cells(f'A{start_row}:F{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value="UNIT PERFORMANCE ANALYSIS")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        start_row += 2
        
        # Headers
        headers = ['Unit', 'Total Miles', 'Total Gallons', 'MPG', 'Total Tax', 'Avg Tax Rate']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        start_row += 1
        
        # Calculate unit totals
        unit_totals = {}
        units = ['100', '103', '104', '105']
        
        for unit in units:
            total_miles = 0
            total_gallons = 0
            total_tax = 0
            
            for state, data in self.state_data.items():
                unit_data = data['units'][unit]
                total_miles += unit_data['miles']
                total_gallons += unit_data['fuel']
                total_tax += unit_data['tax_amount']
            
            unit_totals[unit] = {
                'miles': total_miles,
                'gallons': total_gallons,
                'tax': total_tax
            }
        
        # Data rows
        for unit in units:
            data = unit_totals[unit]
            mpg = data['miles'] / data['gallons'] if data['gallons'] > 0 else 0
            avg_tax_rate = data['tax'] / data['gallons'] if data['gallons'] > 0 else 0
            
            ws.cell(row=start_row, column=1, value=unit)
            ws.cell(row=start_row, column=2, value=f"{data['miles']:,.0f}")
            ws.cell(row=start_row, column=3, value=f"{data['gallons']:,.0f}")
            ws.cell(row=start_row, column=4, value=f"{mpg:.2f}")
            ws.cell(row=start_row, column=5, value=f"${data['tax']:,.2f}")
            ws.cell(row=start_row, column=6, value=f"${avg_tax_rate:.3f}")
            
            for col in range(1, 7):
                cell = ws.cell(row=start_row, column=col)
                cell.border = border
                if col > 1:
                    cell.alignment = Alignment(horizontal='right')
            
            start_row += 1
        
        return start_row + 1
    
    def _add_tax_summary_table(self, ws, start_row, header_font, header_fill, border):
        """Add tax summary table by state"""
        # Title
        ws.merge_cells(f'A{start_row}:G{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value="TAX SUMMARY BY STATE")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        start_row += 2
        
        # Headers
        headers = ['State', 'Unit 100', 'Unit 103', 'Unit 104', 'Unit 105', 'Total Tax', 'Tax Rate']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        start_row += 1
        
        # Data rows
        total_by_unit = {'100': 0, '103': 0, '104': 0, '105': 0}
        grand_total = 0
        
        for state, data in sorted(self.state_data.items()):
            ws.cell(row=start_row, column=1, value=state)
            
            state_total = 0
            for col, unit in enumerate(['100', '103', '104', '105'], 2):
                tax_amount = data['units'][unit]['tax_amount']
                ws.cell(row=start_row, column=col, value=f"${tax_amount:,.2f}")
                total_by_unit[unit] += tax_amount
                state_total += tax_amount
            
            ws.cell(row=start_row, column=6, value=f"${state_total:,.2f}")
            ws.cell(row=start_row, column=7, value=f"${data['rate']:.2f}")
            
            for col in range(1, 8):
                cell = ws.cell(row=start_row, column=col)
                cell.border = border
                if col > 1:
                    cell.alignment = Alignment(horizontal='right')
            
            grand_total += state_total
            start_row += 1
        
        # Total row
        ws.cell(row=start_row, column=1, value="TOTAL")
        for col, unit in enumerate(['100', '103', '104', '105'], 2):
            ws.cell(row=start_row, column=col, value=f"${total_by_unit[unit]:,.2f}")
        ws.cell(row=start_row, column=6, value=f"${grand_total:,.2f}")
        ws.cell(row=start_row, column=7, value="")
        
        for col in range(1, 8):
            cell = ws.cell(row=start_row, column=col)
            cell.font = Font(bold=True)
            cell.border = border
            cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
            if col > 1:
                cell.alignment = Alignment(horizontal='right')
        
        return start_row + 1
    
    def _add_mpg_analysis_table(self, ws, start_row, header_font, header_fill, border):
        """Add detailed MPG analysis table"""
        # Title
        ws.merge_cells(f'A{start_row}:F{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value="MPG ANALYSIS BY UNIT")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        start_row += 2
        
        # Headers
        headers = ['Unit', 'Total Miles', 'Total Gallons', 'MPG', 'Best State MPG', 'Worst State MPG']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        start_row += 1
        
        # Calculate detailed MPG data
        units = ['100', '103', '104', '105']
        
        for unit in units:
            total_miles = 0
            total_gallons = 0
            state_mpgs = []
            
            for state, data in self.state_data.items():
                unit_data = data['units'][unit]
                miles = unit_data['miles']
                gallons = unit_data['fuel']
                
                if gallons > 0:
                    mpg = miles / gallons
                    state_mpgs.append(mpg)
                    total_miles += miles
                    total_gallons += gallons
            
            overall_mpg = total_miles / total_gallons if total_gallons > 0 else 0
            best_mpg = max(state_mpgs) if state_mpgs else 0
            worst_mpg = min(state_mpgs) if state_mpgs else 0
            
            ws.cell(row=start_row, column=1, value=unit)
            ws.cell(row=start_row, column=2, value=f"{total_miles:,.0f}")
            ws.cell(row=start_row, column=3, value=f"{total_gallons:,.0f}")
            ws.cell(row=start_row, column=4, value=f"{overall_mpg:.2f}")
            ws.cell(row=start_row, column=5, value=f"{best_mpg:.2f}")
            ws.cell(row=start_row, column=6, value=f"{worst_mpg:.2f}")
            
            for col in range(1, 7):
                cell = ws.cell(row=start_row, column=col)
                cell.border = border
                if col > 1:
                    cell.alignment = Alignment(horizontal='right')
            
            start_row += 1
        
        return start_row + 1


def process_ifta_report(ifta_report_instance):
    """
    Function to process IFTA report files
    Call this after the CSV file is uploaded
    """
    processor = IFTAReportProcessor(ifta_report_instance)
    return processor.process_files()