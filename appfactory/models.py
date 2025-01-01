from django.db import models
import json
import datetime
from django.conf import settings

SHEET_TYPE_SP = ['KE HOACH','ĐBN','ĐONGGOI','DBN','DONGGOI']


def sum_qty_to_json(ls, is_qty = True):
    res = []

    for process, total in ls:
        if total != 0:
            s = f'{int(total):,}' if is_qty else str(round(total,6))
            res += [f"{process}:{s}"]

    return "<br>".join(res)

class DateItem(models.Model):  
    day = models.IntegerField(default=0)
    month = models.IntegerField(default=0)
    year = models.IntegerField(default=0)

    process = models.CharField(max_length=50, default='')
    volume = models.DecimalField(max_digits=20, decimal_places=6, default=0.0)
    qty = models.IntegerField(default=0)

    content = models.CharField(max_length=255, default='')

class ProductVolumeItem(models.Model):
    product_volume = models.DecimalField(max_digits=20, decimal_places=6, default=0.0)
    all_product_volume = models.DecimalField(max_digits=20, decimal_places=6, default=0.0)
    all_product_qty = models.IntegerField(default=0)

class DetailVolumeItem(models.Model):
    all_this_items_qty_per_product = models.IntegerField(default=0)
    all_this_items_qty = models.IntegerField(default=0)

    this_item_volume = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)

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
            self.save()
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
                        
            if len(ls) > 0:
                self.save()

                for date_item in ls:  # date_data là danh sách dữ liệu để tạo DateItem
                    date_item.save()  # Lưu vào database, đảm bảo có id
    
                self.date.add(*ls)

from collections import defaultdict
from django.db.models import Sum

class ProductItem(models.Model):
    detail_count = models.IntegerField(default=0)
    code = models.CharField(max_length=255, default='', null=True)
    # name = models.CharField(max_length=255, default='', null=True)
    # po = models.CharField(max_length=255, default='', null=True)
    # qty = models.IntegerField(default=0)

    details = models.ManyToManyField(DetailItem)
    
    def get_code(self):
        itm = self.details.first()
        return itm.code if itm else None
    
    def get_po(self):
        itm = self.details.first()
        return itm.po if itm else None
    
    def get_name(self):
        itm = self.details.first()
        return itm.product_name if itm else None
    
    def get_date(self):
        return DateItem.objects.filter(detailitem__in=self.details.all()).distinct()

    def get_volume(self):
        return self.details.filter(product_volume__isnull=False).first().product_volume

    def get_process(self):
        all_dates = self.get_date()
        return [itm.process for itm in all_dates].distinct()
    
    def sum_qty_by_dd_mm_process(self, day, month, is_qty = True):
        # Lọc DateItem theo ngày và tháng
        date_items = self.get_date().filter(day=day, month=month)
        
        # Tạo dictionary để lưu trữ kết quả
        process_summary = defaultdict(float)
        
        
        for itm in date_items:
            if (not getattr(settings, 'ref_process_value', None)) or (itm.process in settings.ref_process_value):
                process_summary[itm.process] += float(itm.qty if is_qty else itm.volume)  # Hoặc thay `qty` bằng trường cần tính tổng
        
        return process_summary.items()
        # res = [{process: int(total) if is_qty else total} for process, total in process_summary.items()]

        # print("<br>".join([f"{process}: {total}" for process, total in process_summary.items()]))
        # Chuyển kết quả thành dictionary thông thường (nếu cần)

    

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
        return any(date.process in process_value for date in self.get_date().distinct())

    def get_unique_days_and_months(self):
        # Lấy danh sách ngày/tháng từ get_date()
        all_dates = self.get_date()
        
        # Lấy các cặp day-month duy nhất
        unique_dates = all_dates.values('day', 'month').distinct()

        # for item in unique_dates:
        #     print('day', item['day'], 'month', item['month'])
        # Trả về danh sách các cặp dưới dạng tuple
        return unique_dates
    
    def get_summary_qty_by_(self, is_qty):
        res = {}
        # print(self.get_unique_days_and_months())
        for itm in self.get_unique_days_and_months():
            day = itm['day']
            month = itm['month']
            
            res[f'{day}-{month}'] = sum_qty_to_json(self.sum_qty_by_dd_mm_process(day, month, is_qty), is_qty)
            # print(day,month,self.sum_qty_by_dd_mm_process(day, month, is_qty), res[f'{day}-{month}'])
        # print('res',res)
        # print([{'key':key, 'value':res[key]} for key in res])
        return [{'key':key, 'value':res[key]} for key in res]
    
    def get_summary_qty_by_process(self):
        return self.get_summary_qty_by_(True)
    
    def get_summary_volume_by_process(self):
        return self.get_summary_qty_by_(False)
    

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

class ShipInfor(models.Model):  
    containerName = models.CharField(max_length=50, default='', null=True) # TÊN CONT
    code = models.CharField(max_length=50, default='', null=True) # MÃ SP
    name = models.CharField(max_length=50, default='', null=True) # TÊN SP
    sheetname = models.CharField(max_length=50, default='', null=True) # TÊN CỘT

    poEtd = models.ManyToManyField(DateItem, related_name='poetd_shipcaneditinfor')

    

    poContent = models.CharField(max_length=50, default='', null=True)
    poName = models.CharField(max_length=50, default='', null=True)

    clientName = models.CharField(max_length=50, default='', null=True) # TÊN KHÁCH HÀNG
    status = models.CharField(max_length=50, default='', null=True) # TRẠNG THÁI SHIP

    qty = models.IntegerField(default=0)
    qtyProcess = models.OneToOneField(QtyProcess, on_delete=models.CASCADE, null=True, blank=True)


    











# scp -r myfactory.zip root@145.223.23.137:factory/myfactory.zip
# scp -r appfactory/templates/product_list.html root@145.223.23.137:factory/appfactory/templates/product_list.html
# rm -r appfactory
# mkdir /factory/appfactory
# scp -r db.sqlite3 root@145.223.23.137:factory
# scp -r appfactory root@145.223.23.137:factory/appfactory/
# scp -r ./appfactory/templates/ root@145.223.23.137:factory/appfactory/templates/
# scp -r ./appfactory root@145.223.23.137:factory/appfactory/
# scp -r ./requirements.txt root@145.223.23.137:/factory/
# scp -r ./newrequire.txt root@145.223.23.137:/factory/
# scp -r ./appfactory/views.py root@145.223.23.137:factory/appfactory/views.py
# ssh root@145.223.23.137
# scp -r ./ root@145.223.23.137:factory
# scp -r ./appfactory root@145.223.23.137:factory/
# scp -r ./db.sqlite3 root@145.223.23.137:factory/db.sqlite3
# python manage.py runserver 0.0.0.0:8000
# scp -r root@145.223.23.137:factory/media ./media
# scp -r db.sqlite3 root@145.223.23.137:factory
# rsync -av --delete ./appfactory root@145.223.23.137:factory/appfactory
# tmux attach -t factory
