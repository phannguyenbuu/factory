import pandas as pd
from openpyxl import load_workbook
from django.db.models import Sum

import django
import os
import sys
import json
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

import json

# Thiết lập môi trường Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myfactory.settings")
django.setup()

from appfactory.models import DateItem, DetailItem, ProductItem

def test_data():
    # code = 'T929'
    # selected_sheets = ['HT','SON','ĐONGGOI','DONGGOI', 'PHÔI','TINH','NHAM','LAPRAP','NGUOI','UV','ĐBN']

    # for sheet in selected_sheets:
    #     filter_objs = DetailItem.objects.filter(process__icontains=sheet)

    #     print(sheet, len(filter_objs))

    #     if sheet == 'DONGGOI':
    #         for prd in filter_objs:
    #             if prd.code == 'JAC-WAR2DSK-06':
    #                 print(prd.code, prd.product_count, prd.comment, prd.date)

    
    # for itm in DetailItem.objects.all():
    #     if itm.name == '':
    #          print(itm.code)

    # items = DetailItem.objects.filter(name__isnull=True)
    # print(len(items), len(ProductItem.objects.all()))
    # In ra code của các item này
    # for itm in items:
    #     print(itm.date)

    # for prd in ProductItem.objects.all():
    #     if 'SP08' in prd.code:
    #         print(prd.code,prd.date)
            # for itm in prd.details.all():
                # print(itm.code,'{',itm.name,'}', itm.process, itm.product_count, itm.date, 'ĐBN' in itm.date)
    

    for product in ProductItem.objects.all():
        if product.get_code() == '1019131-668-V-003':
            print('product', product.get_name(), product.get_summary_qty_by_process())
            print('product', product.get_name(), product.get_summary_volume_by_process())
                # product.get_volume().all_product_volume, product.get_volume().product_volume)
            for detail in product.details.all():
                print('detail',detail.volume.this_item_volume, detail.volume.this_item_volume)
                # for dt in detail.date.all():
                #     # if dt.day == 2 and dt.month == 12:
                #     print(dt.day == 2, dt.month, dt.qty,dt.volume)
            # for itm in product.get_summary_qty_by_process():
            #     print(itm['key'],'******',itm['value'])
            # print(len(product.get_summary_volume_by_process()))
            
test_data()