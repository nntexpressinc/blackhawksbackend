import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from django.core.files.base import ContentFile
import io
from collections import defaultdict
import re


class IFTAReportProcessor:
    def __init__(self, ifta_report_instance):
        self.ifta_report = ifta_report_instance
        self.fuel_data = None
        self.mile_data = None
        
    def process_files(self):
        """Main method to process both files and generate the result Excel file"""
        try:
            # Process fuel Excel file
            self.fuel_data = self._process_fuel_file()
            
            # Process mile CSV file
            self.mile_data = self._process_mile_file()
            
            # Generate result Excel file
            result_file = self._generate_result_excel()
            
            # Save result file to model
            self.ifta_report.result_file = result_file
            self.ifta_report.save()
            
            return True
            
        except Exception as e:
            print(f"Error processing files: {str(e)}")
            raise e  # Re-raise for proper error handling in API
    
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
        
        # Group by LocationState and sum Quantity
        state_quantity = fuel_df.groupby('LocationState')['Quantity'].sum().to_dict()
        
        # Group by Unit and LocationState, sum Quantity
        unit_state_quantity = fuel_df.groupby(['Unit', 'LocationState'])['Quantity'].sum().reset_index()
        
        # Get unique units
        unique_units = fuel_df['Unit'].unique()
        
        return {
            'state_quantity': state_quantity,
            'unit_state_quantity': unit_state_quantity,
            'unique_units': unique_units,
            'total_quantity': fuel_df['Quantity'].sum()
        }
    
    def _process_mile_file(self):
        """Process the mile CSV file and extract required data"""
        # Read CSV file
        mile_df = pd.read_csv(self.ifta_report.mile.path)
        
        # Find State and Miles column pairs
        state_columns = [col for col in mile_df.columns if col.startswith('State')]
        miles_columns = [col for col in mile_df.columns if col.startswith('Miles')]
        
        # Extract unit numbers from column names
        state_units = {}
        miles_units = {}
        
        for col in state_columns:
            unit_match = re.search(r'State(\d+)', col)
            if unit_match:
                unit = int(unit_match.group(1))
                state_units[unit] = col
        
        for col in miles_columns:
            unit_match = re.search(r'Miles(\d+)', col)
            if unit_match:
                unit = int(unit_match.group(1))
                miles_units[unit] = col
        
        # Process data for each unit
        unit_miles_data = {}
        state_miles_totals = defaultdict(float)
        
        for unit in state_units.keys():
            if unit in miles_units:
                state_col = state_units[unit]
                miles_col = miles_units[unit]
                
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
            'total_miles': sum(state_miles_totals.values())
        }
    
    def _generate_result_excel(self):
        """Generate the result Excel file with three tables"""
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"IFTA Report - {self.ifta_report.quorter}"
        
        # Set up styles
        header_font = Font(bold=True, size=12)
        total_font = Font(bold=True, size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        current_row = 1
        
        # Table 1: State Quantity Summary
        current_row = self._add_table_1(ws, current_row, header_font, total_font, border)
        current_row += 2  # Add spacing
        
        # Table 2: State Miles Summary
        current_row = self._add_table_2(ws, current_row, header_font, total_font, border)
        current_row += 2  # Add spacing
        
        # Table 3: MPG Calculations by Unit
        current_row = self._add_table_3(ws, current_row, header_font, total_font, border)
        
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
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        # Create Django file
        filename = f"ifta_report_{self.ifta_report.quorter.replace(' ', '_').lower()}.xlsx"
        return ContentFile(excel_buffer.getvalue(), name=filename)
    
    def _add_table_1(self, ws, start_row, header_font, total_font, border):
        """Add Table 1: State Quantity Summary"""
        # Title
        ws.cell(row=start_row, column=1, value="Table 1: Fuel Quantity by State")
        ws.cell(row=start_row, column=1).font = Font(bold=True, size=14)
        start_row += 2
        
        # Headers
        ws.cell(row=start_row, column=1, value="State")
        ws.cell(row=start_row, column=2, value="Quantity")
        
        for col in range(1, 3):
            cell = ws.cell(row=start_row, column=col)
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        start_row += 1
        
        # Data rows
        for state, quantity in sorted(self.fuel_data['state_quantity'].items()):
            ws.cell(row=start_row, column=1, value=state)
            ws.cell(row=start_row, column=2, value=int(quantity))  # Whole numbers only
            
            for col in range(1, 3):
                ws.cell(row=start_row, column=col).border = border
            
            start_row += 1
        
        # Total row
        ws.cell(row=start_row, column=1, value="TOTAL")
        ws.cell(row=start_row, column=2, value=int(self.fuel_data['total_quantity']))
        
        for col in range(1, 3):
            cell = ws.cell(row=start_row, column=col)
            cell.font = total_font
            cell.border = border
            if col == 1:
                cell.alignment = Alignment(horizontal='center')
        
        return start_row + 1
    
    def _add_table_2(self, ws, start_row, header_font, total_font, border):
        """Add Table 2: State Miles Summary"""
        # Title
        ws.cell(row=start_row, column=1, value="Table 2: Miles by State")
        ws.cell(row=start_row, column=1).font = Font(bold=True, size=14)
        start_row += 2
        
        # Headers
        ws.cell(row=start_row, column=1, value="State")
        ws.cell(row=start_row, column=2, value="Miles")
        
        for col in range(1, 3):
            cell = ws.cell(row=start_row, column=col)
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        start_row += 1
        
        # Data rows
        for state, miles in sorted(self.mile_data['state_miles_totals'].items()):
            ws.cell(row=start_row, column=1, value=state)
            ws.cell(row=start_row, column=2, value=int(miles))  # Whole numbers only
            
            for col in range(1, 3):
                ws.cell(row=start_row, column=col).border = border
            
            start_row += 1
        
        # Total row
        ws.cell(row=start_row, column=1, value="TOTAL")
        ws.cell(row=start_row, column=2, value=int(self.mile_data['total_miles']))
        
        for col in range(1, 3):
            cell = ws.cell(row=start_row, column=col)
            cell.font = total_font
            cell.border = border
            if col == 1:
                cell.alignment = Alignment(horizontal='center')
        
        return start_row + 1
    
    def _add_table_3(self, ws, start_row, header_font, total_font, border):
        """Add Table 3: MPG Calculations by Unit"""
        # Title
        ws.cell(row=start_row, column=1, value="Table 3: MPG by Unit")
        ws.cell(row=start_row, column=1).font = Font(bold=True, size=14)
        start_row += 2
        
        # Headers
        ws.cell(row=start_row, column=1, value="Unit")
        ws.cell(row=start_row, column=2, value="MPG")
        
        for col in range(1, 3):
            cell = ws.cell(row=start_row, column=col)
            cell.font = header_font
            cell.border = border
            cell.alignment = Alignment(horizontal='center')
        
        start_row += 1
        
        # Calculate MPG for each unit
        for unit in sorted(self.fuel_data['unique_units']):
            # Get total quantity for this unit
            unit_quantity = self.fuel_data['unit_state_quantity'][
                self.fuel_data['unit_state_quantity']['Unit'] == unit
            ]['Quantity'].sum()
            
            # Get total miles for this unit
            unit_miles = 0
            if unit in self.mile_data['unit_miles_data']:
                unit_miles = sum(self.mile_data['unit_miles_data'][unit].values())
            
            # Calculate MPG (avoid division by zero)
            if unit_miles > 0:
                mpg = int(unit_quantity / unit_miles)  # Whole numbers only
            else:
                mpg = 0
            
            ws.cell(row=start_row, column=1, value=str(unit))
            ws.cell(row=start_row, column=2, value=mpg)
            
            for col in range(1, 3):
                ws.cell(row=start_row, column=col).border = border
            
            start_row += 1
        
        # Overall MPG
        if self.mile_data['total_miles'] > 0:
            overall_mpg = int(self.fuel_data['total_quantity'] / self.mile_data['total_miles'])
        else:
            overall_mpg = 0
        
        ws.cell(row=start_row, column=1, value="OVERALL MPG")
        ws.cell(row=start_row, column=2, value=overall_mpg)
        
        for col in range(1, 3):
            cell = ws.cell(row=start_row, column=col)
            cell.font = total_font
            cell.border = border
            if col == 1:
                cell.alignment = Alignment(horizontal='center')
        
        return start_row + 1


def process_ifta_report(ifta_report_instance):
    """
    Function to process IFTA report files
    Call this after both fuel and mile files are uploaded
    """
    processor = IFTAReportProcessor(ifta_report_instance)
    return processor.process_files()