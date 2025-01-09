# views.py
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import render
from appfactory.models import default_process_list, GlobalVars,ProductItem, DetailItem, DateItem, SHEET_TYPE_SP, ShipDetailItem, ShipQtyByContainerRelation, ContInfor
from django.db.models import Q
import json
from datetime import datetime
import os
import shutil
from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from appfactory.pyscripts.convert_excel import generate_details_data, generate_product_fr_details
from appfactory.pyscripts.read_ship_excel import _read_all_ship_excel

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.db.models.functions import Length
from django.db.models import Sum
from datetime import date
from django.db.models import F, OuterRef, Subquery

def process_files(request):
    if request.method == 'POST' and request.FILES:
        file_paths = []

        # delete_all_contents(settings.MEDIA_ROOT)
        file_input_type = 0
        # Lưu file lên server
        for file in request.FILES.values():
            
                
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)

            if filename.startswith('QUANLYSANXUAT'):
                file_input_type = 1

            file_paths.append(os.path.join(settings.MEDIA_ROOT, filename))
        
        # Gọi hàm xử lý dữ liệu sau khi lưu file
        try:
            start_time = datetime.now()
            msg = '?'

            if file_input_type == 1: #PRODUCT LIST
                DetailItem.objects.all().delete()

                worksheets = []

                for index, file_path in enumerate(file_paths):
                    msg += ('&' if index > 0 else '') + f'file_{index}=' + os.path.splitext(os.path.basename(file_path))[0] + ":"
                    print('File',index,'/',len(file_paths),':',file_path)
                    # Gọi hàm xử lý dữ liệu với đường dẫn đến file
                    worksheets = generate_details_data(file_path)
                    msg += '_'.join(worksheets)

                generate_product_fr_details()

                msg += f'&detail={DetailItem.objects.all().count()}&product={ProductItem.objects.all().count()}'
            else:
                _read_all_ship_excel(file_paths)

                msg += f'&product={ContInfor.objects.all().count()}&detail={ShipDetailItem.objects.all().count()}'

            end_time = datetime.now()
            duration = end_time - start_time

            total_seconds = int(duration.total_seconds())

            # Tách phút và giây
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            
            print(f"Thời gian thực thi của hàm: {duration}")

            msg += f'&time={minutes:02}:{seconds:02}'

            return JsonResponse({
                'success': True,
                'message': msg,
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Không có file được gửi'})

def view_upload(request):
    context = {
        'upload_numbers': range (0,9),
        'time_func': 360,
    }
    return render(request, 'upload.html', context)


def __get_array_vals(request, key):
    # parsed_url = urlparse(href)
    # query_params = parse_qs(parsed_url.query)

    v = request.GET.get(key, None)
    # v = query_params.get(key, [None])[0]

    return v.split('|') if v else None

import colorsys

def generate_colors(n):
    """Generate n distinct colors and return them as hex strings."""
    colors = []

    for i in range(n):
        hue = i / n  # Tạo hue cách đều nhau
        lightness = 0.5  # Độ sáng cố định
        saturation = 0.9  # Độ bão hòa cố định
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        rgb = tuple(int(c * 255) for c in rgb)  # Chuyển sang RGB (0-255)

        # Chuyển từ RGB sang hex
        hex_color = '#{:02x}{:02x}{:02x}'.format(*rgb)
        colors.append(hex_color)
    return colors

from datetime import datetime

def product_list(request):
    start_time = datetime.now()

    process_value = __get_array_vals(request, 'process')
    code_value = __get_array_vals(request, 'code')
    name_value = __get_array_vals(request, 'name')
    po_value = __get_array_vals(request, 'po')

    GlobalVars.set_value('FILTER_DAYS', __get_array_vals(request, 'day'))
    GlobalVars.set_value('FILTER_PROCESS', __get_array_vals(request, 'process'))

    _global_days = GlobalVars.get_value('FILTER_DAYS')
    _global_process = GlobalVars.get_value('FILTER_PROCESS')

    print("Code:", code_value,"Name:", name_value,"Day:", _global_days,"PO:", po_value,"Process:", _global_process)
    print ('Time', (datetime.now() - start_time).total_seconds())

    filtered_queryset = ProductItem.objects.all()

    if any(s != None for s in [code_value, name_value, po_value, _global_process, _global_days]):
        if code_value != None:
            filtered_queryset = [item for item in filtered_queryset if any(code in item.code for code in code_value)]

        print ('Time_code', code_value, (datetime.now() - start_time).total_seconds())

        if name_value != None:
            filtered_queryset = [item for item in filtered_queryset if any(name in item.name for name in name_value)]

        print ('Time_name', (datetime.now() - start_time).total_seconds())

        if po_value != None:
            filtered_queryset = [item for item in filtered_queryset if any(po in item.po for po in po_value)]

        print ('Time_po', (datetime.now() - start_time).total_seconds())

        if _global_process != None:
            filtered_queryset = [item for item in filtered_queryset if item.is_process(_global_process)]

        print ('Time_process', (datetime.now() - start_time).total_seconds())

        if _global_days != None:
            filtered_queryset = [item for item in filtered_queryset if item.is_date(_global_days)]
        # Tạo 100 màu
        print ('Time_sort_start', (datetime.now() - start_time).total_seconds())

        filtered_queryset = sorted(filtered_queryset, key=lambda obj: obj.code)

        print ('Time_sort_end', (datetime.now() - start_time).total_seconds())
    
        GlobalVars.setAllTotals(filtered_queryset, False)
    else:
        GlobalVars.set_default()

    print ('Time_end_dlist', (datetime.now() - start_time).total_seconds())

    # for product in filtered_queryset:
    #     print('total_qty', product.summary_qty_by_qty)

    content = {'products': filtered_queryset,

                'select_lists': {
                    'Process': default_process_list,
                    'Day': GlobalVars.get_value('ALL_TOTAL_DATE'),
                    
                    'PO': sorted(build_po_list()),
                    'Code': sorted(build_combo_list('code')),
                    'Name': sorted(build_combo_list('name')),
                },

                'FilterDay': GlobalVars.allValidDays(),
                'TotalQty': GlobalVars.get_value('TOTAL_QTY'),
                'TotalVol': GlobalVars.get_value('TOTAL_VOL'),
            }
    # print('content',content['select_lists'])
    print ('Time_end', (datetime.now() - start_time).total_seconds())
    
    # Truyền dữ liệu vào context để sử dụng trong template
    return render(request, 'product_list.html', content)

def xnt(request):
    sorted_queryset = ContInfor.objects.all()
    # sorted_queryset = ContInfor.objects.filter(etd__year__gte=2024,  # Năm lớn hơn 2024
    #     etd__month__gte=5,   # Tháng lớn hơn hoặc bằng 1
    #     etd__day__gte=1      # Ngày lớn hơn hoặc bằng 1
    # )
    
    content = { 'containers': sorted_queryset.order_by('sort_order'),
               'shipdetails': ShipDetailItem.objects.all(),
               'shiprelations': ShipQtyByContainerRelation.objects.all(),
            }
    
    # print(content['select_lists']['Total'])
    
    # Truyền dữ liệu vào context để sử dụng trong template
    return render(request, 'xnt.html', content)

def success_upload(request):
    # Lấy các tham số từ URL query
    files_data = []

    print(request)

    for key, value in request.GET.items():
        # Kiểm tra xem key có phải là "file" theo định dạng "fileX"
        if key.startswith('file'):
            # index = key[4:]  # Lấy chỉ mục (index) từ key, ví dụ "file1" => index = "1"
            files_data += [value]  # Lưu giá trị vào mảng dữ liệu theo chỉ mục

    detail = request.GET.get('detail', '')
    product = request.GET.get('product', '')
    time = request.GET.get('time', '')

    # Chuyển các tham số file1_data và file2_data thành các hàng dữ liệu
    return render(request, 'upload_success.html', {
        'files_data': files_data,
        'details': detail,
        'product': product,
        'time': time,
    })

def build_po_list(product = True):
    return (sorted(set(DetailItem.objects.values_list('po', flat=True))) if product else sorted(set(DetailItem.objects.values_list(key, flat=True))))
    
def build_combo_list(key):
    # ar = (sorted(set(ProductItem.objects.values_list(key, flat=True))) if product else sorted(set(DetailItem.objects.values_list(key, flat=True))))
    if key == 'code':
        values = [item.code for item in ProductItem.objects.all()]
    else:
        values = [item.name for item in ProductItem.objects.all()]

    for i in range(len(values)):
        if values[i] == '-': values[i] = None

    # Loại bỏ giá trị trống hoặc None, sau đó lấy tập hợp và sắp xếp
    return sorted(set(filter(None, values)))

@csrf_exempt  # Tạm thời bỏ qua kiểm tra CSRF (chỉ cho việc phát triển, không nên dùng trong môi trường sản xuất)
def receive_product_id(request):
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ request body
            data = json.loads(request.body)
            product_id = data.get('productid', None)  # Lấy productid từ dữ liệu gửi đến
            # print('product_id',product_id)
            # print('ref_days', GlobalVars.get_value('REF_DAY')

            if not product_id:
                return JsonResponse({'status': 'error', 'message': 'Product ID not provided'}, status=400)

            # Tìm sản phẩm trong cơ sở dữ liệu
            try:
                product = next(item for item in ProductItem.objects.all() if item.code == product_id)
                # details = product.details.filter(name__isnull=False).order_by('name')

                total_qty, total_vol, total_datelist = ProductItem.get_details_date_qty([product])

                res = []

                for detail in product.details.all():
                    if detail.process in SHEET_TYPE_SP or detail.name:
                        ls = []
                        for dt in detail.date.all():
                            # print(dt.process)
                            if GlobalVars.isValidFilterDay and GlobalVars.isValidFilterProcess:
                                ls += [dt]
                        
                        if len(ls) > 0:
                            
                            res += [{'name':detail.name or '---',
                                    'size':f'{detail.width}{detail.length}{detail.depth}',
                                    'qty':detail.volume.all_this_items_qty,
                                    'vol':detail.volume.this_item_volume,
                                    'date':ls,
                                    # 'volume':[f'{v.day}-{v.month}/{v.process}:{v.volume}' for v in ls]
                                    }]

                # print('res:',len(res),res)

                context = {
                    'id': product_id,
                    'name': product.get_name(),
                    'details': res,
                    'total_qty': list(total_qty.values()), 
                    'total_vol': list(total_vol.values()),  
                    'total_datelist': [itm for itm in total_datelist if itm in total_qty],
                    'selected_dates': GlobalVars.get_value('FILTER_DAYS') or [],
                    'selected_processes': GlobalVars.filterProcess() or [],
                }

                
                rendered_html = render_to_string('product_detail.html', context)

                return JsonResponse({'html': rendered_html})


            except ProductItem.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@csrf_exempt
def add_date(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        date_str = data.get('date', '')
        try:
            # print('ok0',date_str)
            day, month, year = map(int, date_str.split('/'))
            # print('ok0.1')
            new_date = DateItem.objects.create(day=day, month=month, year=year)

            # print('ok1')
            contifor = ContInfor.objects.filter(id=data.get('id')).first()
            # print('ok2')

            if contifor:
                key = data.get('key')
                print('contifor', key, contifor, len(contifor.etd.all()))
                
                if hasattr(contifor, key):  # Kiểm tra nếu contifor có trường này
                    getattr(contifor, key).add(new_date) 
                
                return JsonResponse({'success': True, 'id': new_date.id, 'date': f"{day}/{month}/{year}"})
            else:
                return JsonResponse({'success': False, 'error': 'ContInfor not found'})
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})

@csrf_exempt
def delete_date(request):
    print(request.body)
    if request.method == 'POST':
        data = json.loads(request.body)
        date_id = data.get('id')

        try:
            date_item = DateItem.objects.get(id=date_id)
            date_item.delete()
            return JsonResponse({'success': True})
        except DateItem.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Date not found'})

@csrf_exempt  # Tạm thời bỏ qua kiểm tra CSRF (chỉ cho việc phát triển, không nên dùng trong môi trường sản xuất)
def xnt_receive_product_id(request):
    if request.method == 'POST':
        try:
            
            # Lấy dữ liệu JSON từ request body
            data = json.loads(request.body)
           
            id = data.get('id', None)  # Lấy productid từ dữ liệu gửi đến
            contNumber = data.get('contNumber', None)
            client = data.get('client', None)

            print('product_data', data, id, contNumber, client)
            # print('product_id', product_id)
            # print('ref_days', GlobalVars.get_value('REF_DAY')

            if not id and not contNumber and not client:
                return JsonResponse({'status': 'error', 'message': 'Product ID not provided'}, status=400)

            # Tìm sản phẩm trong cơ sở dữ liệu
            try:
                if contNumber == '--':
                    contObj = ContInfor.objects.filter(clientname=client, poNumber=id).first()
                elif id == '--':
                    contObj = ContInfor.objects.filter(clientname=client, name=contNumber).first()
                else:
                    contObj = ContInfor.objects.filter(clientname=client, poNumber=id, name=contNumber).first()


                details = contObj.details.filter(code__isnull=False).order_by('code')
                res = []

                for itm in details:
                    relate_items = ShipQtyByContainerRelation.objects.filter(detail_id=itm.id,contifor_id=contObj.id)
                    
                    relate_conts_items = ShipQtyByContainerRelation.objects.filter(detail_id=itm.id)
                    
                    relate_conts_items = sorted(
                        relate_conts_items, 
                        key=lambda item: item.contifor.by_sort_date(),  # Sử dụng by_sort_date() làm key
                        reverse=True  # Sắp xếp theo thứ tự giảm dần
                    )

                    __inconts = {}
                    __total = 0
                    for __itm in relate_items: __total += __itm.value

                    __total_in_this = itm.instock
                    __check__total_in_this = True
                    
                    for __itm in relate_conts_items:
                        if not __itm.contifor.is_ship():
                            __name = __itm.contifor.name

                            if __name == None:
                                __name = __itm.contifor.poNumber

                            __date = __itm.contifor.by_sort_date()
                            __name +=  f'({__date.strftime("%d-%m-%y")})'

                            __inconts[__name] = __itm.value

                            if __check__total_in_this: __total_in_this -= __itm.value
                            if __itm.contifor.id == __itm != contObj.id: __check__total_in_this = False

                    if __total_in_this < 0: __total_in_this = 0
                    if __total_in_this > __total: __total_in_this = __total

                    res += [{'code':itm.code, 
                             'name':itm.name,
                             'inconts': __inconts,
                             'qty_require':__total,
                             'qty':__total_in_this,
                             'input':itm.input,
                             'output':itm.output,
                             'note':itm.note,
                             'instock':itm.instock,
                             'instockVolume':itm.instockVolume,
                             'documentDate':itm.documentDate.replace('00:00:00','').strip(),
                            }]

                    
                

                context = {
                    'client': client,
                    'id': id,
                    'contnumber': contNumber,
                    'details': res,
                }

                
                rendered_html = render_to_string('modules/xnt_detail.html', context)

                return JsonResponse({'html': rendered_html})


            except ProductItem.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
