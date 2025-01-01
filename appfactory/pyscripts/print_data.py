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

from appfactory.models import POrderItem,DateItem, DetailItem, ContainerItem, ProductItem, POrderItem

itm = DetailItem.objects.all()[0]

# print(itm.name,itm.qty)