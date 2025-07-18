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
        self.state_tax_rates = {}
        self.units = set()
        
    def process_files(self):
        """Main method to process the files and generate the result Excel file"""
        try:
            # Load state tax rates
            self._load_state_tax_rates()
            
            # Process fuel Excel file
            self.fuel_data = self._process_fuel_file()
            
            # Process mile CSV file
            self.mile_data = self._process_mile_file()
            
            # Extract all units from both files
            self._extract_units()
            
            # Generate result Excel file
            result_file = self._generate_result_excel()
            
            # Save result file to model
            self.ifta_report.result_file = result_file
            self.ifta_report.save()
            
            return True
            
        except Exception as e:
            print(f"Error processing files: {str(e)}")
            raise e
    
    def _load_state_tax_rates(self):
        """Load state tax rates from the database"""
        from your_app.models import StateTaxRate  # Replace 'your_app' with actual app name
        
        rates = StateTaxRate.objects.all()
        self.state_tax_rates = {rate.state: float(rate.tax_rate) for rate in rates}
    
    def _process_fuel_file(self):
        """Process the fuel Excel file and extract required data"""
        # Read Excel file
        fuel_df = pd.read_excel(self.ifta_report.fuel.path)
        
        # Extract required columns
        required_columns = ['Unit', 'Quantity', 'LocationState']
        
        # Check if required columns exist
        for col in required_columns:
            if col not in fuel_df.columns:
                raise ValueError(f"Required column '{col}' not found in fuel Excel file")
        
        # Clean data - remove any null values
        fuel_df = fuel_df.dropna(subset=required_columns)
        
        # Convert Unit to string for consistency
        fuel_df['Unit'] = fuel_df['Unit'].astype(str)
        
        # Group by LocationState and sum Quantity
        state_quantity = fuel_df.groupby('LocationState')['Quantity'].sum().to_dict()
        
        # Group by Unit and LocationState, sum Quantity
        unit_state_quantity = fuel_df.groupby(['Unit', 'LocationState'])['Quantity'].sum().reset_index()
        
        # Get unique units
        unique_units = set(fuel_df['Unit'].unique())
        
        return {
            'state_quantity': state_quantity,
            'unit_state_quantity': unit_state_quantity,
            'unique_units': unique_units,
            'total_quantity': fuel_df['Quantity'].sum(),
            'raw_data': fuel_df
        }
    
    def _process_mile_file(self):
        """Process the mile CSV file and extract required data"""
        # Read CSV file
        mile_df = pd.read_csv(self.ifta_report.mile.path)
        
        # Find State and Miles column pairs dynamically
        state_columns = {}
        miles_columns = {}
        
        # Extract units from column names
        for col in mile_df.columns:
            # Look for State[unit] pattern
            state_match = re.search(r'State(\d+)', col, re.IGNORECASE)
            if state_match:
                unit = state_match.group(1)
                state_columns[unit] = col
            
            # Look for Miles[unit] pattern
            miles_match = re.search(r'Miles(\d+)', col, re.IGNORECASE)
            if miles_match:
                unit = miles_match.group(1)
                miles_columns[unit] = col
        
        # Process data for each unit
        unit_miles_data = {}
        state_miles_totals = defaultdict(float)
        
        # Get units that have both state and miles columns
        available_units = set(state_columns.keys()) & set(miles_columns.keys())
        
        for unit in available_units:
            state_col = state_columns[unit]
            miles_col = miles_columns[unit]
            
            # Remove null values and group by state
            valid_data = mile_df.dropna(subset=[state_col, miles_col])
            unit_data = valid_data.groupby(state_col)[miles_col].sum().to_dict()
            unit_miles_data[unit] = unit_data
            
            # Add to overall state totals
            for state, miles in unit_data.items():
                state_miles_totals[state] += miles
        
        return {
            'unit_miles_data': unit_miles_data,
            'state_miles_totals': dict(state_miles_totals),
            'total_miles': sum(state_miles_totals.values()),
            'available_units': available_units
        }
    
    def _extract_units(self):
        """Extract all units from both fuel and mile data"""
        fuel_units = self.fuel_data['unique_units']
        mile_units = self.mile_data['available_units']
        
        # Convert mile units to strings for consistency
        mile_units = set(str(unit) for unit in mile_units)
        
        # Get intersection of units (units that exist in both files)
        self.units = fuel_units & mile_units
        
        if not self.units:
            raise ValueError("No matching units found between fuel and mile files")
    
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
        
        # Table 1: State Summary with Tax Calculations
        current_row = self._add_state_summary_table(ws, current_row, header_font, header_fill, border)
        current_row += 2
        
        # Table 2: Unit Performance Summary
        current_row = self._add_unit_performance_table(ws, current_row, header_font, header_fill, border)
        current_row += 2
        
        # Table 3: Tax Summary by Unit and State
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
        """Add comprehensive state summary table with tax calculations"""
        # Title
        ws.merge_cells(f'A{start_row}:G{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value="STATE SUMMARY WITH TAX CALCULATIONS")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        start_row += 2
        
        # Headers
        headers = ['State', 'Tax Rate', 'Total Miles', 'Total Gallons', 'MPG', 'Taxable Gallons', 'Tax Due']
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
        
        # Get all states from both fuel and mile data
        all_states = set(self.fuel_data['state_quantity'].keys()) | set(self.mile_data['state_miles_totals'].keys())
        
        for state in sorted(all_states):
            state_miles = self.mile_data['state_miles_totals'].get(state, 0)
            state_gallons = self.fuel_data['state_quantity'].get(state, 0)
            tax_rate = self.state_tax_rates.get(state, 0)
            
            # Calculate MPG
            mpg = state_miles / state_gallons if state_gallons > 0 else 0
            
            # For tax calculation, we need to consider fuel purchased vs fuel consumed
            # Assuming taxable gallons = fuel purchased in state
            taxable_gallons = state_gallons
            tax_due = taxable_gallons * tax_rate
            
            ws.cell(row=start_row, column=1, value=state)
            ws.cell(row=start_row, column=2, value=f"${tax_rate:.3f}")
            ws.cell(row=start_row, column=3, value=f"{state_miles:,.0f}")
            ws.cell(row=start_row, column=4, value=f"{state_gallons:,.0f}")
            ws.cell(row=start_row, column=5, value=f"{mpg:.2f}")
            ws.cell(row=start_row, column=6, value=f"{taxable_gallons:,.0f}")
            ws.cell(row=start_row, column=7, value=f"${tax_due:,.2f}")
            
            # Apply borders and alignment
            for col in range(1, 8):
                cell = ws.cell(row=start_row, column=col)
                cell.border = border
                if col > 1:  # Right align numbers
                    cell.alignment = Alignment(horizontal='right')
            
            total_miles += state_miles
            total_gallons += state_gallons
            total_tax += tax_due
            start_row += 1
        
        # Total row
        overall_mpg = total_miles / total_gallons if total_gallons > 0 else 0
        ws.cell(row=start_row, column=1, value="TOTAL")
        ws.cell(row=start_row, column=2, value="")
        ws.cell(row=start_row, column=3, value=f"{total_miles:,.0f}")
        ws.cell(row=start_row, column=4, value=f"{total_gallons:,.0f}")
        ws.cell(row=start_row, column=5, value=f"{overall_mpg:.2f}")
        ws.cell(row=start_row, column=6, value=f"{total_gallons:,.0f}")
        ws.cell(row=start_row, column=7, value=f"${total_tax:,.2f}")
        
        for col in range(1, 8):
            cell = ws.cell(row=start_row, column=col)
            cell.font = Font(bold=True)
            cell.border = border
            cell.fill = PatternFill(start_color="E6E6FA", end_color="E6E6FA", fill_type="solid")
            if col > 1:
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
        headers = ['Unit', 'Total Miles', 'Total Gallons', 'MPG', 'Total Tax', 'Efficiency Rating']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        start_row += 1
        
        # Calculate unit totals
        unit_totals = {}
        
        for unit in sorted(self.units):
            total_miles = 0
            total_gallons = 0
            total_tax = 0
            
            # Get miles for this unit
            if unit in self.mile_data['unit_miles_data']:
                total_miles = sum(self.mile_data['unit_miles_data'][unit].values())
            
            # Get gallons for this unit
            unit_fuel = self.fuel_data['unit_state_quantity'][
                self.fuel_data['unit_state_quantity']['Unit'] == unit
            ]
            if not unit_fuel.empty:
                total_gallons = unit_fuel['Quantity'].sum()
                
                # Calculate tax for this unit
                for _, row in unit_fuel.iterrows():
                    state = row['LocationState']
                    quantity = row['Quantity']
                    tax_rate = self.state_tax_rates.get(state, 0)
                    total_tax += quantity * tax_rate
            
            unit_totals[unit] = {
                'miles': total_miles,
                'gallons': total_gallons,
                'tax': total_tax
            }
        
        # Data rows
        for unit in sorted(self.units):
            data = unit_totals[unit]
            mpg = data['miles'] / data['gallons'] if data['gallons'] > 0 else 0
            
            # Efficiency rating based on MPG
            if mpg >= 7:
                efficiency = "Excellent"
            elif mpg >= 6:
                efficiency = "Good"
            elif mpg >= 5:
                efficiency = "Average"
            else:
                efficiency = "Poor"
            
            ws.cell(row=start_row, column=1, value=unit)
            ws.cell(row=start_row, column=2, value=f"{data['miles']:,.0f}")
            ws.cell(row=start_row, column=3, value=f"{data['gallons']:,.0f}")
            ws.cell(row=start_row, column=4, value=f"{mpg:.2f}")
            ws.cell(row=start_row, column=5, value=f"${data['tax']:,.2f}")
            ws.cell(row=start_row, column=6, value=efficiency)
            
            for col in range(1, 7):
                cell = ws.cell(row=start_row, column=col)
                cell.border = border
                if col in [2, 3, 4, 5]:  # Right align numbers
                    cell.alignment = Alignment(horizontal='right')
                elif col == 6:  # Center align efficiency
                    cell.alignment = Alignment(horizontal='center')
            
            start_row += 1
        
        return start_row + 1
    
    def _add_tax_summary_table(self, ws, start_row, header_font, header_fill, border):
        """Add tax summary table by unit and state"""
        # Title
        ws.merge_cells(f'A{start_row}:F{start_row}')
        title_cell = ws.cell(row=start_row, column=1, value="TAX SUMMARY BY UNIT AND STATE")
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = Alignment(horizontal='center')
        start_row += 2
        
        # Dynamic headers based on available units
        headers = ['State'] + [f'Unit {unit}' for unit in sorted(self.units)] + ['Total Tax']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        start_row += 1
        
        # Data rows
        total_by_unit = {unit: 0 for unit in self.units}
        grand_total = 0
        
        # Get all states
        all_states = set(self.fuel_data['state_quantity'].keys()) | set(self.mile_data['state_miles_totals'].keys())
        
        for state in sorted(all_states):
            ws.cell(row=start_row, column=1, value=state)
            
            state_total = 0
            col_idx = 2
            
            for unit in sorted(self.units):
                # Get fuel quantity for this unit in this state
                unit_fuel = self.fuel_data['unit_state_quantity'][
                    (self.fuel_data['unit_state_quantity']['Unit'] == unit) &
                    (self.fuel_data['unit_state_quantity']['LocationState'] == state)
                ]
                
                if not unit_fuel.empty:
                    quantity = unit_fuel['Quantity'].sum()
                    tax_rate = self.state_tax_rates.get(state, 0)
                    tax_amount = quantity * tax_rate
                else:
                    tax_amount = 0
                
                ws.cell(row=start_row, column=col_idx, value=f"${tax_amount:,.2f}")
                total_by_unit[unit] += tax_amount
                state_total += tax_amount
                col_idx += 1
            
            ws.cell(row=start_row, column=col_idx, value=f"${state_total:,.2f}")
            
            # Apply borders
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=start_row, column=col)
                cell.border = border
                if col > 1:
                    cell.alignment = Alignment(horizontal='right')
            
            grand_total += state_total
            start_row += 1
        
        # Total row
        ws.cell(row=start_row, column=1, value="TOTAL")
        col_idx = 2
        for unit in sorted(self.units):
            ws.cell(row=start_row, column=col_idx, value=f"${total_by_unit[unit]:,.2f}")
            col_idx += 1
        ws.cell(row=start_row, column=col_idx, value=f"${grand_total:,.2f}")
        
        for col in range(1, len(headers) + 1):
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
        for unit in sorted(self.units):
            total_miles = 0
            total_gallons = 0
            state_mpgs = []
            
            # Get miles data for this unit
            if unit in self.mile_data['unit_miles_data']:
                unit_miles = self.mile_data['unit_miles_data'][unit]
                total_miles = sum(unit_miles.values())
            
            # Get gallons data for this unit
            unit_fuel = self.fuel_data['unit_state_quantity'][
                self.fuel_data['unit_state_quantity']['Unit'] == unit
            ]
            if not unit_fuel.empty:
                total_gallons = unit_fuel['Quantity'].sum()
                
                # Calculate MPG for each state for this unit
                for _, row in unit_fuel.iterrows():
                    state = row['LocationState']
                    gallons = row['Quantity']
                    miles = unit_miles.get(state, 0) if unit in self.mile_data['unit_miles_data'] else 0
                    
                    if gallons > 0:
                        mpg = miles / gallons
                        state_mpgs.append(mpg)
            
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
    Call this after both fuel and mile files are uploaded
    """
    processor = IFTAReportProcessor(ifta_report_instance)
    return processor.process_files()