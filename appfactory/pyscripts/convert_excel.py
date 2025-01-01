import pandas as pd
from openpyxl import load_workbook

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

from appfactory.models import DetailItem, ProductItem, DetailVolumeItem, ProductVolumeItem

# SHEET_TYPE_SP = ['HT','ĐBN','ĐONGGOI','DBN','DONGGOI']
SELECTED_SHEETS = ['KE HOACH','PHÔI','PHOI','TINH','NHAM','LAPRAP','NGUOI','SON','UV','ĐBN','DBN','HT','ĐONGGOI','DONGGOI']
REF_KEY = 'ORDER SỐ'

def __process_from_headers(file, sheet, content, headers):
    res = []

    for line in content.split('\n'):
        elements = line.strip().split("|")

        if  (not 'Unnamed' in line) and (not 'MÃ SP' in line) and (len(elements) >= 1) and (sum(1 for item in elements if len(item) > 5) > 2):
            itm = {}

            for index, header in enumerate(headers):
                if header != '' and index < len(elements) :
                    itm[header] = elements[index]
                
            if itm: 
                itm['processing'] = sheet
                itm['file'] = file
                res += [itm]

    return res
   
def __extract_headers_from_content(content):
    for index, line in enumerate(content.split('\n')):
        if 'MÃ SP' in line:
            return [s.upper() for s in line.split('|')]

def generate_details_data(excel_file_path):
    workbook = load_workbook(filename=excel_file_path, read_only=True)
    visible_sheets = [sheet.title for sheet in workbook.worksheets if sheet.title and sheet.title in SELECTED_SHEETS]
    
    print('Workbook:', visible_sheets)

    for index, sheet_name in enumerate(visible_sheets):
        print('Sheet', index,'/',len(visible_sheets),':',sheet_name)

        df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
        df = df.replace('\n', ' ', regex=True)

        content = df.to_csv(index=False, sep='|', lineterminator='\n').replace(' 00:00:00', '')
        _headers = __extract_headers_from_content(content)
        
        if _headers:
            data = __process_from_headers(os.path.basename(excel_file_path),sheet_name, content, _headers)
            print('header', sheet_name, _headers, len(data))

            import_detail_object(data)
            # print('done 2')
        else:
            print(f'Null headers', sheet_name)

    return visible_sheets

def import_detail_object(items):
    default_detail_colume = DetailVolumeItem.objects.create(
                        all_this_items_qty_per_product = 0,
                        all_this_items_qty = 0,
                        this_item_volume = 0,
                    )
    
    default_product_colume = ProductVolumeItem.objects.create(
                        product_volume = 0,
                        all_product_volume = 0,
                        all_product_qty = 0,
                    )
    
    # print('items', len(items))

    for itm in items:
        if itm[REF_KEY]:
            # print('ref', itm)

            val = DetailItem(
                volume = default_detail_colume,
                product_volume = default_product_colume
            )

            val.parse_data(itm, REF_KEY)

def generate_product_fr_details():
    unique_product_codes = DetailItem.objects.values_list('code', flat=True).distinct()
    ProductItem.objects.all().delete()

    for code in unique_product_codes:
        try:
            detail_items = DetailItem.objects.filter(code=code)

            product = ProductItem.objects.create()
            product.details.add(*detail_items)
            # __create_details_for_single_product(product)

            product.save()
        except Exception as e:
            print('Error in', str(e))

import sqlite3

def reset_and_add_details(details):
    # Giả sử 'details' là danh sách các đối tượng DetailItem, bạn sẽ lấy tất cả các 'id' từ các đối tượng này
    detail_ids_to_keep = set(detail.id for detail in details)  # Lấy 'id' từ các đối tượng DetailItem
    
    # Lấy tất cả các đối tượng DetailItem hiện tại trong cơ sở dữ liệu
    current_detail_items = DetailItem.objects.all()

    # Xóa các DetailItem không có trong 'details'
    for item in current_detail_items:
        if item.id not in detail_ids_to_keep:
            item.delete()

    # Thêm lại các DetailItem từ 'details' vào cơ sở dữ liệu
    for detail in details:
        # Nếu DetailItem chưa có trong cơ sở dữ liệu, thêm mới
        if not DetailItem.objects.filter(id=detail.id).exists():
            DetailItem.objects.create(**detail)
    
    print("DetailItems have been reset and added again, while keeping those in 'details'.")

def decrease_dblite(table_key, num_rows):
    products = ProductItem.objects.all()
    
    count = 0
    res = set()

    for product in products:
        details = product.details.all()

        if len(details) > 0:
            res.update(details)
            count += 1

            if count > 10: break

    
    reset_and_add_details(res)
    generate_product_fr_details()
    

    


if __name__ == "__main__":
    decrease_dblite('appfactory_detailitem', 250)
    # generate_product_fr_details()