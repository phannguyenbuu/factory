import pandas as pd
from openpyxl import load_workbook
import string
import django
import os
import sys
import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

# Thiết lập môi trường Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myfactory.settings")
django.setup()

from appfactory.models import DetailItem, DateItem,ShipQtyByContainerRelation, ProductItem, DetailVolumeItem, ProductVolumeItem, DateCanEdit, ShipDetailItem, ShipInfor, ContInfor

_key_code_ = 'MÃ SP'
_valid_letter_length_ = 5
_unvalid_calue_ = ['Unnamed']
_max_columns_ = 100


class ReadExcelCLS():
    def __init__(self, filename, sheet_name, replace_dict = None):
        # self.SELECTED_SHEETS = selected_sheet
        self.file = filename
        self.replace_dict = replace_dict
        self.sheet_name = sheet_name

        self.headRow = 0

    def valid_row(self, line):
        res =  not any(k in line for k in _unvalid_calue_) 
        if not res: return False

        res = res and (not _key_code_ in line) 
        if not res: return False
        
        elements = line.strip().split("|")
        # res = res and (len(elements) >= 1) 
        # if not res: return False

        # res = res and (sum(1 for s in elements if len(s) > _valid_letter_length_) > 2)
        # if not res: return False

        return res

    def colLetter(self, column_index):
        
        column_letter = ""
        while column_index > 0:
            

            column_index, remainder = divmod(column_index - 1, 26)

            if column_letter == '':
                remainder += 1

            column_letter = chr(65 + remainder) + column_letter

            
        if column_letter == '':
            column_letter = 'A'
        if column_letter == '[':
            column_letter = 'AA'
        if column_letter == 'A[':
            column_letter = 'BA'

        return column_letter
    

    def get_column_index(self, column_letter):
        column_index = 0
        for char in column_letter:
            # Tính toán giá trị cho từng ký tự (A = 1, B = 2, ..., Z = 26)
            column_index = column_index * 26 + (ord(char.upper()) - ord('A') + 1)
        return column_index
    
    
    def read_data_by_location(self, column_alphabet, row):
        return self.data[row][column_alphabet]
    
    def setHeader(self, column_alphabet, val):
        self.headers[column_alphabet] = val

    def appendHeaders(self, header_keys, range_column_indexes):
        start_column_index = self.get_column_index(range_column_indexes[0])
        end_column_index = self.get_column_index(range_column_indexes[1])

        # print(header_keys, start_column_index, end_column_index, 7 in range(start_column_index, end_column_index))

        for index, line in enumerate(self.contents):
            ls = line.split('|')
            
            new_line = '|'.join(ls[start_column_index:end_column_index + 1]).upper()

            if all(_s.upper() in new_line for _s in header_keys):
                # print('all', line)
                for n,s in enumerate(ls):
                    if n in range(start_column_index, end_column_index) and any(_s.upper() in s.upper() for _s in header_keys):
                        # print('col', n, self.colLetter(n), s)
                        self.headers[self.colLetter(n)] = s.upper()
                        if index > self.headRow: self.headRow = index
                    
        self.headers = dict(sorted(self.headers.items(), key=lambda item: len(item[0])))
            
    def update_data(self):
        # for index, sheet_name in enumerate(self.visible_sheets):
        # if self.headers:
        res = []

        for index, line in enumerate(self.contents):
            # if self.valid_row(line):
            itm = {}
            for n, s in enumerate(line.strip().split("|")):
                if s and s != '0'  and s != '0.0':
                    itm[self.colLetter(n)] = s
            
            # itm['index'] = index
            itm['sheet'] = self.sheet_name
            itm['file'] = os.path.basename(self.file)
            res += [itm]

        self.data = res
        # else:
        #     print(f'Null headers', self.sheet_name)
    
    def get_item_value_by_col_prefix(self, line_index, keyword):
        for item in self.data:
            if item['index'] == line_index:
                for key, value in self.headers.items():
                    if keyword in value:
                        return item[key] if key in item else None
                    
    def getColumn(self, letter):
        res = []

        for index, item in enumerate(self.data):
            res += [item[letter] if letter in item else None]

        while res and res[-1] is None:
            res.pop()
        
        for i in range(len(res)):
            if res[i] and 'Unnamed:' in res[i]:
                res[i] = None

        return res
    
    def totalHeader(self):
        return self.get_column_index(list(self.headers.items())[-1][0])
            
    # def get_headers_startswith(selft, key):
    #     return [itm for itm in selft.headers.items() if itm[1].startswith(key)]

    def Print(self):
        print(','.join(self.headers.keys()), self.headRow)
        print(','.join(self.headers.values()), self.headRow)

        print('value', self.get_item_value_by_col_prefix(20, "CONT 38"))
        print(self.data[14])

    def read_data(self, header_keys):
        df = pd.read_excel(self.file, sheet_name=self.sheet_name)
        df = df.replace('\n', ' ', regex=True)

        content = df.to_csv(index=False, sep='|', lineterminator='\n')

        if self.replace_dict:
            for key, val in self.replace_dict.items():
                content = content.replace(key, val)
        
        self.contents = content.split('\n')

        
        # print(self.content)

        self.update_data()

        self.headers = {}
        
        for header_key_itm in header_keys:
            self.appendHeaders(header_key_itm['keywords'], header_key_itm['range'])


class VerticalExcelCLS(ReadExcelCLS):
    def generate_vertical_data(self, keywords): #from column contain all keywords
        self.vertical_headers_colIndex = -1

        for n in range(0, 255):
            key = self.colLetter(n)
            col_contents = self.getColumn(key)

            if all(any(s and k.upper() in s.upper() for s in col_contents) for k in keywords):
                self.vertical_headers_colIndex = n
                self.vertical_headers_colLetter = key
                # print('row', n, col_contents)
                self.verticalHeaders = [col_contents[i] for i in range(self.headRow)]
                break
            
        self.verticalData = {}

        if self.vertical_headers_colIndex > -1:
            a = self.vertical_headers_colIndex + 1
            b = 25 * 12

            for row_index in range(self.headRow):
                if self.verticalHeaders[row_index]:
                    key = self.verticalHeaders[row_index]
                    arr = {}
                                        
                    # if not key in self.verticalData: self.verticalData[key] = []
                    for x in range(a, b):
                        letter = self.colLetter(x)

                        if letter in self.data[row_index]:
                            arr[letter] = self.data[row_index][letter]

                    self.verticalData[key] = arr

    def get_row_by_keyIndex(self, key, letter_prefix = None, null_keywords = []):
        res = {}

        # print('VLK', letter_prefix)

        for k, itm in self.verticalData.items():
            if key in k:
                for  __k, __v in itm.items():
                    if (not letter_prefix and __k in string.ascii_uppercase) \
                        or (letter_prefix and (__k.startswith(__ch) for __ch in letter_prefix)):
                        if not any(__s in __v for __s in null_keywords):
                            res[__k] = __v

        return res
    
    def getRow(self, key, exlude_keys = []):
        for k in self.verticalHeaders:
            if k and key in k and not any(__k in k for __k in exlude_keys):
                return self.verticalData[k]

def import_ship_data(clientname, file, headKeys, vertical_po_prefix = None):
    _key_code_ = 'CODE'
    SELECTED_SHEETS = ['TH 2023']
    
    workbook = load_workbook(filename=file, read_only=True)
    
    xls = VerticalExcelCLS(file, 'TH 2023')

    xls.read_data(headKeys)
    xls.generate_vertical_data(['ETD','PO','DESTINATION','THANG SHIP'])

    print(clientname, file, headKeys)
    # print('HEA', xls.verticalHeaders, xls.verticalData,  xls.get_row_by_keyIndex('PO'))

    ls = xls.get_row_by_keyIndex('PO', vertical_po_prefix)
    
    contTypes = {}
    
    for line in xls.data:
        # print(line)
        if sum(('0 HC' in v) or ('0 DC' in v) for k,v in line.items()) > 2:
            contTypes = line
            break
        
    contNames = xls.get_row_by_keyIndex('THÖÙ TÖÏ CONT', vertical_po_prefix)
    

    # print('contTypes', contTypes)

    # print('ls', ls)
    
    for poletter, poname in ls.items():
        cont_type = contTypes[poletter] if poletter in contTypes else None
        cont_name = contNames[poletter] if poletter in contNames else None
        # print('letter', poletter)
        contObj = ContInfor.objects.create(clientname = clientname,
                                            poNumber = poname, 
                                            letter = poletter,
                                            name = cont_name,
                                            contType = cont_type)

        contObj.AddData(xls)
        # contObj.Print()

        

    for index, itm in enumerate(xls.data):
        if index > xls.headRow and 'B' in itm and 'C' in itm and 'E' in itm: 
            ship_detail = ShipDetailItem.objects.create(
                code = itm['B'],
                name = itm['C'],
                color = itm['E'],
            )

            for poletter, poname in ls.items():
                try:
                    contifor = ContInfor.objects.get(clientname = clientname, letter=poletter)

                    if contifor and poletter in itm :
                        # print(poletter, itm)
                        ship_relation = ShipQtyByContainerRelation.objects.create(detail = ship_detail,
                                                    contifor = contifor,
                                                    value = itm[poletter])
                        
                        # ship_relation.Print()
                except ContInfor.DoesNotExist:
                    print(f"No ContInfor found for letter: {poletter}")

def _read_all_ship_excel():
    ShipDetailItem.objects.all().delete()
    ContInfor.objects.all().delete()
    ShipQtyByContainerRelation.objects.all().delete()

    import_ship_data('UMBRA', 'media/TH XUAT UMBRA 2023.xlsx',
                     [{'keywords':['CODE', 'ITEM', 'COLOR'],'range':['A','Z']},], 'B')
    
    import_ship_data('MFC', 'media/TH XUAT MFC 2023.xlsx',
                     [{'keywords':['CODE', 'ITEM', 'COLOR'],'range':['A','Z']},],)
    
    import_ship_data('ASL', 'media/TH XUAT ASHLEY 2023.xlsx', 
                     [{'keywords':['CODE', 'ITEM', 'COLOR'],'range':['A','Z']},],'JK')
    
    import_ship_data('FWG', 'media/TH XUAT FWG 2023.xlsx', 
                     [{'keywords':['CODE', 'ITEM', 'COLOR'],'range':['A','Z']},],'A')
    
    import_ship_data('AXC', 'media/TH XUAT AXCESS  2023- NEW 01-03-2023.xlsx', 
                     [{'keywords':['CODE', 'ITEM', 'COLOR'],'range':['A','Z']},],'A')
    
    for itm in ContInfor.objects.all():
        if itm.name and not itm.name.startswith('CONT'): 
            itm.name = None
            itm.save()
            print(f"Set none for code: {itm.poNumber}")

        if itm.poNumber and itm.poNumber.startswith('CONT'):
            itm.name = itm.poNumber
            itm.poNumber = None
            itm.save()
            print(f"Set none for cont: {itm.poNumber}")
    
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def _read_XNT_excel():
    xls = VerticalExcelCLS('media/TP ( N-X-T ) THANG  12-2024.xls', 'NHAP LIEU')
    xls.read_data([{'keywords':['MÃ TP', 'TÊN SẢN PHẨM'],'range':['A','Z']},])
    print(len(ShipDetailItem.objects.all()))

    for line in xls.data:
        if 'L' in line:
            code = line['L'].upper()
            if code:
                obj, created = ShipDetailItem.objects.get_or_create(code=code)
                
                # obj.isInput = 'NHẬP' in line['I'].upper()
                obj.name = line['M'].upper()
                obj.input = int(line['P']) if 'P' in line and (line['P'].isdigit()) else 0
                obj.output = int(line['R']) if 'R' in line and (line['R'].isdigit()) else 0

                obj.note = line['T'].upper() if 'T' in line else None
                obj.documentDate = line['F'].upper() if 'F' in line else None
                obj.save()
                
                if created:
                    print(f"Not found for code: {code}")

    xls = VerticalExcelCLS('media/TP ( N-X-T ) THANG  12-2024.xls', 'BAO CAO X-N-T')
    xls.read_data([{'keywords':['MÃ TP', 'TÊN SẢN PHẨM'],'range':['A','Z']},])

    for line in xls.data:
        if 'B' in line:
            code = line['B'].upper()

            in_stock =  int(line['Q']) if 'Q' in line and (line['Q'].isdigit()) else 0
            in_stock_vol = line['R'] if 'R' in line and is_float(line['R']) else 0

            if code and in_stock != 0:
                obj, created = ShipDetailItem.objects.get_or_create(code=code)
                
                # obj.isInput = 'NHẬP' in line['I'].upper()
                # obj.name = line['M'].upper()
                obj.instock = in_stock
                obj.instockVolume = in_stock_vol

                obj.save()
                
                if created:
                    print(f"Stock-Not found for code: {code}")

if __name__ == "__main__":
    _read_all_ship_excel()
    _read_XNT_excel()

    for itm in ContInfor.objects.all():
        itm.updateData()

    # for itm in ShipDetailItem.objects.all():
    #     itm.Print()
