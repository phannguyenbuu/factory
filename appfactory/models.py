from django.db import models
import json
import datetime
from django.conf import settings
from django.db.models import F

SHEET_TYPE_SP = ['KE HOACH','ĐBN','ĐONGGOI','DBN','DONGGOI']
# default_process_list = [{'color':'#ff0000','label':'PHÔI', 'icon':'p'},
#             {'color':'#8a1fc7','label':'TINH',  'icon':'t'},
#             {'color':'#ff5b6f','label':'NGUOI',  'icon':'i'},
#             {'color':'#038bd5','label': 'HT', 'icon': 'h'},
#             {'color':'#00a846','label': 'LAPRAP', 'icon': 'l'},
#             {'color':'#ee9805','label': 'NHAM', 'icon':'n'},
#             {'color':'#2d6adf','label': 'SON', 'icon': 's'},
#             {'color':'#ffb748','label': 'UV', 'icon': 'u' },
#             {'color':'#555555','label': 'ĐBN','icon': 'd'},
#             {'color':'#555555','label': 'DONGGOI','icon': 'g'}]

default_process_list = ['PHÔI','TINH','NGUOI','HT','LAPRAP','NHAM','SON','UV','ĐBN','DONGGOI']

# def get_date_list(details):
#     # res = []
#     print('ILM', list(details.values('day', 'month')))
#     unique_days_months = (details.values('day', 'month').distinct().order_by('month', 'day'))
        
#     # for item in unique_days_months:
#     #     res += [(f"{item['day']}-{item['month']}")]

#     return [{'label': (f"{item['day']}-{item['month']}")} for item in unique_days_months]

from datetime import datetime, timedelta

class DateItem(models.Model):
    day = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    year = models.IntegerField(default=0)

    process = models.CharField(max_length=50, default='')
    volume = models.FloatField(default=0.0)
    qty = models.IntegerField(default=0)

    content = models.CharField(max_length=255, default='')

    def ToDate(self):
        return datetime(self.year, self.month, self.day, 0, 0, 0)

    def add(self, days):
        date = self.ToDate() + timedelta(days=days)
        return DateItem.objects.create(year = date.year, month = date.month, day = date.day)
        # self.save()

    def subtract(self, days):
        date = self.ToDate() - timedelta(days=days)
        return DateItem.objects.create(year = date.year, month = date.month, day = date.day)
        # self.save()

    def __str__(self):
        return f'{self.day}/{self.month}/{self.year}'


class ProductVolumeItem(models.Model):
    product_volume = models.FloatField(default=0.0)
    all_product_volume = models.FloatField(default=0.0)
    all_product_qty = models.IntegerField(default=0)

    def to_dict(self):
        return {
            "product_volume": self.product_volume,
            "all_product_volume": self.all_product_volume,
            "all_product_qty": self.all_product_qty,
        }

class DetailVolumeItem(models.Model):
    all_this_items_qty_per_product = models.IntegerField(default=0)
    all_this_items_qty = models.IntegerField(default=0)

    this_item_volume = models.FloatField(default=0.0)

    def get_all_this_items_volume_per_product(self):
        return self.qty_per_product * self.volume_per_item
    
zeros = ['','-']
def _vkey(itm, key, f = False):
    s =  itm[key] if key in itm else ('0' if f else None)
    
    if f and (s in zeros): s = '0'
    return float(s) if f else s

class DetailItem(models.Model):
    process = models.CharField(max_length=40, default='', null=True)
    code = models.CharField(max_length=255, default='', null=True)
    po = models.CharField(max_length=255, default='', null=True)
    product_name = models.CharField(max_length=255, default='', null=True)
    name = models.CharField(max_length=255, default='', null=True)

    date = models.ManyToManyField(DateItem)
        
    length = models.FloatField(default=0.0)
    width = models.FloatField(default=0.0)
    depth = models.FloatField(default=0.0)

    volume = models.ForeignKey(DetailVolumeItem, on_delete = models.CASCADE)
    product_volume = models.ForeignKey(ProductVolumeItem, on_delete = models.CASCADE)

    def parse_data(self, itm, order_key):
        self.process = itm['processing']
        
        self.code = _vkey(itm,'MÃ SP').strip()
        # print(self.code)

        self.product_name = _vkey(itm,'TÊN SP')
        self.name = _vkey(itm,'TÊN CTIẾT')
        
        vol_key = 'VOL SP'

        if not itm['processing'] in SHEET_TYPE_SP:
            self.depth = _vkey(itm,'DÀY', True)
            self.width = _vkey(itm,'RỘNG', True)
            self.length = _vkey(itm,'DÀI', True)
            vol_key = 'VOL'

        self.po = _vkey(itm, order_key)
        slg_ct =  _vkey(itm,'SLG CT', True)
        
        this_vol = _vkey(itm,vol_key, True) / (slg_ct if slg_ct != 0 else 1)

        self.volume = DetailVolumeItem.objects.create(
            all_this_items_qty_per_product = slg_ct,
            all_this_items_qty = _vkey(itm,'SLG SP', True),
            this_item_volume = this_vol,
        )

        # print(itm['processing'], 'vol_key', vol_key, '=', self.volume.this_item_volume,)
        
        if self.process == 'KE HOACH':
            self.product_volume = ProductVolumeItem.objects.create(
                product_volume = _vkey(itm,'VOL SP', True),
                all_product_volume = _vkey(itm,'TỔNG VOL SP', True),
                all_product_qty = _vkey(itm,'SLG SP', True),
            )
            
        else:
            ls = []

            for key, value in itm.items():
                if '-' in key and value:
                    ar = key.split('-')

                    if len(ar) > 2:
                        if value in zeros: value = '0'
                        v = float(value)
                        
                        if v != 0:
                            ls += [DateItem(
                                process = self.process,
                                qty = v,
                                volume = this_vol * v,
                                day = int(ar[2]),
                                month = int(ar[1]),
                                year = int(ar[0]),
                            )]

            # print('DATELS', len(ls))
                        
            if len(ls) > 0:
                self.save()

                for date_item in ls:  # date_data là danh sách dữ liệu để tạo DateItem
                    date_item.save()  # Lưu vào database, đảm bảo có id
    
                self.date.add(*ls)

        self.save()

from collections import defaultdict
from django.db.models import Sum

class ProductItem(models.Model):
    detail_count = models.IntegerField(default=0)
    code = models.CharField(max_length=255, default='', null=True)
    name = models.CharField(max_length=255, default='', null=True)
    po = models.CharField(max_length=255, default='', null=True)
    qty = models.IntegerField(default=0)
    volume =  models.JSONField(default=dict)  # Lưu trữ JSON

    date = models.ManyToManyField(DateItem)

    summary_qty_by_qty = models.JSONField(default=dict)  # Lưu trữ JSON
    summary_qty_by_vol = models.JSONField(default=dict)  # Lưu trữ JSON

    process = models.CharField(max_length=50, default='')
    details = models.ManyToManyField(DetailItem)

    def updateQtyByDate(self):
        self.summary_qty_by_qty = self.get_summary_qty_by_(True)
        self.summary_qty_by_vol = self.get_summary_qty_by_(False)
        self.save()

    def updateData(self):
        self.code = self.get_code()
        self.po = self.get_po()
        self.name = self.get_name()

        self.date.clear()

        for itm in self.details.all():
            # print(len(itm.date.all()))
            self.date.add(*itm.date.all())

        self.save()

        # print('date',len(self.date.all()))

        self.volume = self.get_volume()
        self.process = ','.join([itm.process for itm in self.date.all()])
        
        self.updateQtyByDate()
        
    def get_code(self):
        itm = self.details.first()
        return itm.code if itm else None
    
    def get_po(self):
        itm = self.details.first()
        return itm.po if itm else None
    
    def get_name(self):
        itm = self.details.first()
        return itm.product_name if itm else None
    
    def get_volume(self):
        return self.details.filter(product_volume__isnull=False).first().product_volume.to_dict()
    
    def sum_qty_by_dd_mm_process(self, day, month, is_qty = True):
        # Lọc DateItem theo ngày và tháng
        # all_dates = self.date
        date_items = [d for d in self.date.all() if d.day == day and d.month == month]
        
        # Tạo dictionary để lưu trữ kết quả
        process_summary = defaultdict(float)
        
        filter_process = GlobalVars.filterProcess()
        # print(filter_process)
        
        for itm in date_items:
            if not filter_process or (itm.process in filter_process):
                process_summary[itm.process] += float(itm.qty if is_qty else itm.volume)  # Hoặc thay `qty` bằng trường cần tính tổng
        
        return process_summary
        
    def is_date(self, day_value):
        if (not day_value) or len(day_value) == 0:
            return True
        
        for day_str in day_value:
            day, month = day_str.split('-')
            day = int(day)
            month = int(month)
            # print(product.sum_qty_by_dd_mm_process(day, month))
            
            if len([itm for itm in self.sum_qty_by_dd_mm_process(day, month) if len(itm) != 0]) > 0:
                return True
            
        return False
    

    def is_process(self, process_value):
        return any(date.process in process_value for date in self.date.distinct())

    def get_unique_days_and_months(self):
        return { (date.day, date.month) for date in self.date.all() }
    
    def get_summary_qty_by_(self, is_qty):
        res = {}
        # print('unique', self.get_unique_days_and_months())
        for itm in self.get_unique_days_and_months():
            day, month = itm
            res[f'{day}-{month}'] = ProductItem.sum_qty_to_json(self.sum_qty_by_dd_mm_process(day, month, is_qty), is_qty)
        return res



    @classmethod    
    def total_process_by_date(cls, selected_products, day_str):
        day, month = day_str.split('-')
        day = int(day)
        month = int(month)

        date_items = [date for item in selected_products for date in item.date.all()]

        process_list = set()
        for itm in date_items:
            process_list.add(itm.process)

        # print('date_items', len(date_items), len(process_list))
        
        res_qty = {}
        res_vol = {}

        filter_process = GlobalVars.filterProcess()
        # print('filter_process', filter_process)

        for process in process_list:
            if not filter_process or (itm.process in filter_process):
                filter_date_items = [itm for itm in date_items if itm.day == day and itm.month == month and itm.process == process]
                # print(day,month,len(filter_date_items))
                res_qty[process] = sum(itm.qty for itm in filter_date_items)
                res_vol[process] = sum(itm.volume for itm in filter_date_items)
        
        return res_qty, res_vol
    
    @classmethod
    def sum_qty_to_json(cls, ls, is_qty = True):
        res = []
        # print(ls)
        filter_process = GlobalVars.filterProcess()

        for process, total in ls.items():
            if not filter_process or ((process in filter_process) and total != 0):
                s = f'{int(total):,}' if is_qty else str(round(total,6))
                if s != '0':
                    res += [f"{process}:{s}"]

        return "<br>".join(res)

    @classmethod  
    def get_details_date_qty(cls, queryset):
        datelist = set()
        
        for product in queryset:
            # print('DL', product.details.filter(date__qty__gt=0))
            for detail in product.details.all():
                for _date in detail.date.all():
                    if _date.qty != 0:
                        datelist.add(f"{_date.day}-{_date.month}")

        datelist = sorted(datelist, key=lambda x: datetime.strptime(f"{x}-2024", "%d-%m-%Y"), reverse=True)
        
        total_qty = {}
        total_vol = {}

        for day in datelist:
            a, b = cls.total_process_by_date(queryset, day)
            # print('a-b',a,b)
            v = cls.sum_qty_to_json(a)

            if v != '':
                total_qty[day] =  v
                total_vol[day] =  cls.sum_qty_to_json(b, False)

        return total_qty, total_vol, list(datelist)


column_key_checks = ['BOOKING CUTOFF', 'BOOKING ETD', 'THANG SHIP','LOAD CONT TT','ETD IN VIETNAM','PO MIX','DESTINATION']
column_key_in_models = ['bookingCutoff','bookingEtd','monthShip','loadContTT','etdVietNam']
    

class DateCanEdit(models.Model):
    psi = models.ManyToManyField(DateItem, related_name='psi_shipcaneditinfor')
    cyCut = models.ManyToManyField(DateItem, related_name='cycut_shipcaneditinfor')
    siCut = models.ManyToManyField(DateItem, related_name='sicut_shipcaneditinfor')
    shipRun = models.ManyToManyField(DateItem, related_name='shiprun_shipcaneditinfor')
    bookingCutoff = models.ManyToManyField(DateItem, related_name='bookingCutoff_shipcaneditinfor')
    bookingEtd = models.ManyToManyField(DateItem, related_name='bookingEtd_shipcaneditinfor')
    monthShip = models.ManyToManyField(DateItem, related_name='monthShip_shipcaneditinfor')
    loadContTT = models.ManyToManyField(DateItem, related_name='loadContTT_shipcaneditinfor')
    etd = models.ManyToManyField(DateItem, related_name='etdVietNam_shipcaneditinfor')
    
class QtyProcess(models.Model):
    DBN = models.IntegerField(default=0)
    DONG_GOI = models.IntegerField(default=0)
    TON_KHO = models.IntegerField(default=0)


def pday(s):
        return int(s) if s.strip().isdigit() else 0
    
def contains_no_alphabet(s):
    for char in s:
        if char.isalpha():
            return False
    return True


def validDate(val):
        d = 0
        m = 0
        y = 2024

        val = val.replace('-','/').replace('THANG','').replace('00:00:00','').strip()

        if contains_no_alphabet(val):
            arr = val.split('/')
            
            for i in range(len(arr), 3):
                arr += ['0']

            d = pday(arr[0])
            m = pday(arr[1])
            y = pday(arr[2])

            if d > 2000:
                tmp = d
                d = y
                y = tmp

            if y == 0: y = 2025

        # print('date', val, d,m,y)
    
        return DateItem.objects.create(day = d, month = m, year = y)


class ShipDetailItem(models.Model):
    code = models.CharField(max_length=50, default='', null=True) # TÊN CONT
    name = models.CharField(max_length=255, default='', null=True) # TÊN CONT
    color = models.CharField(max_length=50, default='', null=True) # TÊN CONT
    qty = models.CharField(max_length=50, default='', null=True) # TÊN CONT
    client = models.CharField(max_length=50, default='', null=True) # TÊN CONT
    qtyByProcess = models.OneToOneField(QtyProcess, on_delete=models.CASCADE, null=True, blank=True)
    # contifor = models.ForeignKey(ContInfor, on_delete=models.CASCADE, null=True)
    # isInput = models.BooleanField(default=True)
    input = models.IntegerField(default=0)
    output = models.IntegerField(default=0)
    note = models.CharField(max_length=255, default='', null=True)

    instock = models.IntegerField(default=0)
    instockVolume = models.FloatField(default=0.0)

    documentDate = models.CharField(max_length=20, default='', null=True)
    

    def Print(self):
        print('ShipDetailItem', self.note, self.input, self.output, self.instock, self.instockVolume)


class ContInfor(models.Model):
    clientname = models.CharField(max_length=50, default='', null=True) # TÊN SP
    name = models.CharField(max_length=50, default='', null=True) # TÊN SP
    contIndex = models.CharField(max_length=10, default='', null=True) # TÊN SP
    letter = models.CharField(max_length=5, default='', null=True) # TÊN SP
    dest = models.CharField(max_length=50, default='', null=True) # TÊN SP
    # date = models.OneToOneField(DateCanEdit, on_delete=models.CASCADE, null=True, blank=True)
    contType = models.CharField(max_length=10, default='', null=True) # TÊN SP
    poNumber = models.CharField(max_length=20, default='', null=True) # TÊN SP
    
    etd = models.ManyToManyField(DateItem, related_name='etd_contifor')



    psi = models.ManyToManyField(DateItem, related_name='psi_contifor')
    cyCut = models.ManyToManyField(DateItem, related_name='cycut_contifor')
    siCut = models.ManyToManyField(DateItem, related_name='sicut_contifor')
    shipRun = models.ManyToManyField(DateItem, related_name='shiprun_contifor')


    details = models.ManyToManyField(ShipDetailItem, related_name='details_ContInfor')
    instock = models.IntegerField(default=0)
    instockVolume = models.FloatField(default=0.0)
    qty = models.IntegerField(default=0)

    sort_order = models.IntegerField(default=0)

    def is_ship(self):
        return any([itm.note != '' for itm in self.details.all()])

    def by_sort_date(self): # Lấy giá trị ngày so sánh theo thứ tự psi -> cycut -> etd
         # Lấy ngày cuối cùng từ psi, cyCut và etd
        last_psi = self.psi.last()  # Lấy ngày cuối cùng từ psi
        last_cycut = self.cyCut.last()  # Lấy ngày cuối cùng từ cyCut
        last_etd = self.etd.last()  # Lấy ngày cuối cùng từ etd

        # Tạo danh sách các ngày và sắp xếp theo thứ tự ưu tiên: psi -> cyCut -> etd
        dates = []

        # Thêm ngày từ psi, nếu có
        if last_psi:
            return datetime(last_psi.year, last_psi.month, last_psi.day)

        # Thêm ngày từ cyCut, nếu có
        if last_cycut:
            return datetime(last_cycut.year, last_cycut.month, last_cycut.day)

        # Thêm ngày từ etd, nếu có
        if last_etd:
            return datetime(last_etd.year, last_etd.month, last_etd.day)

        return datetime(1900, 1, 1)

    @classmethod
    def sortData(cls):
        sorted_queryset = ContInfor.objects.annotate(last_etd=F('etd__last')).order_by('clientname','-last_etd__year', '-last_etd__month', '-last_etd__day')
        for index, item in enumerate(sorted_queryset):
            item.sort_order = index + 1  # Gán giá trị sắp xếp
            item.save()  # Lưu thay đổi vào cơ sở dữ liệu

    def updateData(self):
        items = ShipQtyByContainerRelation.objects.filter(contifor_id=self.id)
        
        ls = []
        qty = 0
        instock = 0
        instockVolume = 0

        for itm in items:
            ls += [itm.detail]
            qty += itm.value
            instock += itm.detail.instock
            instockVolume += itm.detail.instockVolume

        self.details.add(*ls)
        self.qty = qty
        self.instock = instock
        self.instockVolume = instockVolume

        self.save()

    def create_10_sample_can_edited_date(self):
        return [DateItem.objects.create() for i in range(10)]
    
    
    

    def AddData(self, xls):
        v = xls.getRow('DESTINATION')
        # print('dest',self.letter,v)
        if v and self.letter in v:
            self.dest = v[self.letter]

        # column_key_checks = ['BOOKING CUTOFF', 'BOOKING ETD', 'THANG SHIP','LOAD CONT TT','ETD IN VIETNAM','PO MIX','DESTINATION']

        # if 'BOOKING CUTOFF' in xls.verticalData:
        #     self.date.bookingCutoff=(self.create_can_edited_date(xls.verticalData['BOOKING CUTOFF'])[self.letter])

        

        v = xls.getRow('PO')
        # print('po',self.letter, v)
        if v and self.letter in v:
            self.poNumber = v[self.letter]

        # if 'LOAD CONT TT' in xls.verticalData:
        #     self.contType = xls.verticalData['LOAD CONT TT']

        # if 'BOOKING ETD' in xls.verticalData:
        #     self.date.bookingEtd = xls.verticalData['BOOKING ETD']

        # if 'THANG SHIP' in xls.verticalData:
        #     self.date.monthShip = xls.verticalData['THANG SHIP']
            
        # self.save()

        v = xls.getRow('ETD', ['BOOKING'])

        # print('vt', v)
        
        if v and self.letter in v:
            # print('etd',self.letter, v[self.letter], self.create_can_edited_date(v[self.letter]))
            self.etd.add(validDate(v[self.letter]))

        # print("ETD items after add:", self.etd.all())

        self.save()

    def Print(self):
        print('container', self.clientname, self.poNumber,  self.name, self.dest, self.contType, self.letter, 
              f':{self.etd.all()[0].day}-{self.etd.all()[0].month}')


class ShipQtyByContainerRelation(models.Model):
    detail = models.ForeignKey(ShipDetailItem, on_delete=models.CASCADE)
    contifor = models.ForeignKey(ContInfor, on_delete=models.CASCADE)
    value = models.IntegerField(default=0)

    def Print(self):
        print(f'{self.detail.code} - {self.detail.name} - {self.contifor.name} - {self.value}')

class GlobalVars(models.Model):
    params = models.JSONField(default=dict)

    @classmethod
    def setAllTotals(cls, queryset, is_default):
        if is_default:
            GlobalVars.set_value('FILTER_DAYS', None)
            GlobalVars.set_value('FILTER_PROCESS', None)

        for itm in queryset:
            itm.updateQtyByDate()

        total_qty, total_vol, datelist = ProductItem.get_details_date_qty(queryset)
        # print('GlobalVars', total_qty, total_vol, datelist)

        if is_default:
            GlobalVars.set_value('ALL_TOTAL_QTY', total_qty)
            GlobalVars.set_value('ALL_TOTAL_VOL', total_vol)
            GlobalVars.set_value('ALL_TOTAL_DATE', datelist)
        
        GlobalVars.set_value('TOTAL_QTY', total_qty)
        GlobalVars.set_value('TOTAL_VOL', total_vol)
        GlobalVars.set_value('TOTAL_DATE', datelist)

        # print('Total', GlobalVars.get_value('ALL_TOTAL_QTY'),
        #     GlobalVars.get_value('ALL_TOTAL_VOL'),
        #     GlobalVars.get_value('ALL_TOTAL_DATE'))
            

    @classmethod
    def isValidFilterDay(cls, day, month):
        vals = cls.get_value('FILTER_DAYS')
        return (not vals) or (f'{day}-{month}' in vals)

    @classmethod
    def isValidFilterProcess(cls, process):
        vals = cls.get_value('FILTER_PROCESS')
        return (not vals) or (process in vals)

    @classmethod
    def get_global_vars(cls):
        obj, created = cls.objects.get_or_create(id=1)  # Đảm bảo chỉ có 1 bản ghi
        return obj

    @classmethod
    def get_value(cls, key, default=None):
        obj = cls.get_global_vars()
        return obj.params.get(key, default)

    @classmethod
    def set_value(cls, key, value):
        obj = cls.get_global_vars()
        obj.params[key] = value
        obj.save()

    @classmethod
    def delete_value(cls, key):
        obj = cls.get_global_vars()
        if key in obj.params:
            del obj.params[key]
            obj.save()

    @classmethod
    def set_default(cls):
        obj = cls.get_global_vars()
        for key,value in obj.params.items():
            if 'ALL_' + key in obj.params:
                obj.params[key] = obj.params['ALL_' + key] 

        obj.save()

        return obj
    
    @classmethod
    def allValidDays(cls):
        date_list =  [d for d in GlobalVars.get_value('FILTER_DAYS')] \
            if(GlobalVars.get_value('FILTER_DAYS') and len(GlobalVars.get_value('FILTER_DAYS')) > 0) else cls.get_value('TOTAL_DATE', default='')
        return sorted(date_list, key=lambda x: datetime.strptime(x, "%d-%m"), reverse=True)

    @classmethod
    def Print(cls):
        obj = cls.get_global_vars()
        print(obj.params)
        
    @classmethod
    def filterDays(cls):
        return GlobalVars.get_value('FILTER_DAYS')
    
    @classmethod
    def filterProcess(cls):
        return GlobalVars.get_value('FILTER_PROCESS')

# scp -r myfactory.zip root@145.223.23.137:factory/myfactory.zip
# scp -r appfactory/templates/product_list.html root@145.223.23.137:factory/appfactory/templates/product_list.html
# rm -r media
# mkdir /factory/appfactory
# scp -r db.sqlite3 root@145.223.23.137:factory
# scp -r appfactory root@145.223.23.137:factory/appfactory/
# scp -r ./appfactory/templates/ root@145.223.23.137:factory/appfactory/


    
# scp -r ./requirements.txt root@145.223.23.137:/factory/
# scp -r ./newrequire.txt root@145.223.23.137:/factory/
# scp -r ./appfactory/views.py root@145.223.23.137:factory/appfactory/views.py
# ssh root@145.223.23.137
# scp -r ./ root@145.223.23.137:factory

# scp -r ./appfactory root@145.223.23.137:factory/

# scp -r ./db.sqlite3 root@145.223.23.137:factory/
# python manage.py runserver 0.0.0.0:8000
# scp -r root@145.223.23.137:factory/media ./media
# scp -r db.sqlite3 root@145.223.23.137:factory
# rsync -av --delete ./appfactory root@145.223.23.137:factory/appfactory
# tmux attach -t factory
    
# scp -r root@145.223.23.137:factory/db.sqlite3 ./
