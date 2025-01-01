# views.py
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.shortcuts import render
from appfactory.models import ProductItem, DetailItem, DateItem, sum_qty_to_json, SHEET_TYPE_SP, ShipDetailItem, ShipQtyByContainerRelation, ContInfor
from django.db.models import Q
import json
from datetime import datetime
import os
import shutil
from django.conf import settings
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from appfactory.pyscripts.convert_excel import generate_details_data, generate_product_fr_details

# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from django.db.models.functions import Length
from django.db.models import Sum



def process_files(request):
    if request.method == 'POST' and request.FILES:
        file_paths = []

        # delete_all_contents(settings.MEDIA_ROOT)
        
        # Lưu file lên server
        for file in request.FILES.values():
            fs = FileSystemStorage()
            filename = fs.save(file.name, file)
            file_paths.append(os.path.join(settings.MEDIA_ROOT, filename))
        
        # Gọi hàm xử lý dữ liệu sau khi lưu file
        try:
            start_time = datetime.now()
            DetailItem.objects.all().delete()

            msg = '?'
            # print('Step 1:', file_paths)  # In ra các đường dẫn file đã lưu
            worksheets = []

            for index, file_path in enumerate(file_paths):
                msg += ('&' if index > 0 else '') + f'file_{index}=' + os.path.splitext(os.path.basename(file_path))[0] + ":"
                print('File',index,'/',len(file_paths),':',file_path)
                # Gọi hàm xử lý dữ liệu với đường dẫn đến file
                worksheets = generate_details_data(file_path)
                msg += '_'.join(worksheets)

            generate_product_fr_details()

            end_time = datetime.now()
            print(f"Thời gian thực thi của hàm: {end_time - start_time}")

            msg += f'&detail={DetailItem.objects.all().count()}&product={ProductItem.objects.all().count()}&time={end_time - start_time}'

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

def get_date_list(details):
    # res = []
    unique_days_months = (details.values('day', 'month').distinct().order_by('month', 'day'))
        
    # for item in unique_days_months:
    #     res += [(f"{item['day']}-{item['month']}")]

    return [{'label': (f"{item['day']}-{item['month']}")} for item in unique_days_months]

def total_process_by_date(selected_products, day_str):
    day, month = day_str.split('-')
    day = int(day)
    month = int(month)

    date_items = [date for item in selected_products for date in item.get_date().all()]

    process_list = set()
    for itm in date_items:
        process_list.add(itm.process)

    # print('date_items', len(date_items), len(process_list))
    
    res_qty = {}
    res_vol = {}

    for process in process_list:
        if (not getattr(settings, 'ref_process_value', None)) or (process in settings.ref_process_value):
            filter_date_items = [itm for itm in date_items if itm.day == day and itm.month == month and itm.process == process]
            # print(day,month,len(filter_date_items))
            res_qty[process] = sum(itm.qty for itm in filter_date_items)
            res_vol[process] = sum(itm.volume for itm in filter_date_items)
    
    return res_qty.items(), res_vol.items()

def get_details_date_qty(product_query_set):
    datelist = get_date_list(DateItem.objects.filter(qty__gt=0))

    total_qty = {}
    total_vol = {}

    for itm in datelist:
        day = itm['label']
        ls1, ls2 = total_process_by_date(product_query_set, day)
        
        v = sum_qty_to_json(ls1)

        if v != '':
            total_qty[day] =  v
            total_vol[day] =  sum_qty_to_json(ls2, False)

    return total_qty, total_vol, datelist



def product_list(request):
    # day_value = __get_array_vals(request, 'day')
    process_value = __get_array_vals(request, 'process')
    code_value = __get_array_vals(request, 'code')
    name_value = __get_array_vals(request, 'name')
    po_value = __get_array_vals(request, 'po')

    settings.ref_day_value = __get_array_vals(request, 'day')
    settings.ref_process_value = __get_array_vals(request, 'process')

    print("Code:", code_value,"Name:", name_value,"Day:", settings.ref_day_value,"PO:", po_value,"Process:", settings.ref_process_value)
    
    filtered_queryset = [obj for obj in ProductItem.objects.all() if len(obj.get_code()) > 3 ]

    # Dùng phương thức getter để lọc
    
    if code_value:
        filtered_queryset = [item for item in filtered_queryset if any(code in item.get_code() for code in code_value)]

    if name_value:
        filtered_queryset = [item for item in filtered_queryset if any(name in item.name for name in name_value)]

    if po_value:
        filtered_queryset = [item for item in filtered_queryset if any(po in item.get_po() for po in po_value)]

    if settings.ref_process_value:
        filtered_queryset = [item for item in filtered_queryset if item.is_process(settings.ref_process_value)]

    if settings.ref_day_value:
        filtered_queryset = [item for item in filtered_queryset if item.is_date(settings.ref_day_value)]
    # Tạo 100 màu
    filtered_queryset = sorted(filtered_queryset, key=lambda obj: obj.get_code())
    
    total_qty, total_vol, datelist = get_details_date_qty(filtered_queryset)

    dlist = [{'label':d} for d in settings.ref_day_value] if(settings.ref_day_value and len(settings.ref_day_value) > 0) else datelist

    content = {'products': filtered_queryset[:10],

                'select_lists': {
                    'Process': default_process_list(),
                    'Day': datelist,
                    
                    'PO': build_po_list(),
                    'Code': build_combo_list('get_code'),
                    'Name': build_combo_list('get_name'),
                    
                },

                'FilterDay': dlist,
                'TotalQty': [{'key':key, 'value':total_qty[key]} for key in total_qty],
                'TotalVol': [{'key':key, 'value':total_vol[key]} for key in total_vol],
            }
    
    # print(content['select_lists']['Total'])
    
    # Truyền dữ liệu vào context để sử dụng trong template
    return render(request, 'product_list.html', content)

def xnt(request):
    
    content = { 'containers': ContInfor.objects.all().order_by('clientname', 'name'),
               'shipdetails': ShipDetailItem.objects.all(),
               'shiprelations': ShipQtyByContainerRelation.objects.all(),

            }
    
    # print(content['select_lists']['Total'])
    
    # Truyền dữ liệu vào context để sử dụng trong template
    return render(request, 'xnt.html', content)


def default_process_list():
    return [{'color':'#ff0000','label':'PHÔI', 'icon':'p'},
            {'color':'#8a1fc7','label':'TINH',  'icon':'t'},
            {'color':'#ff5b6f','label':'NGUOI',  'icon':'i'},
            {'color':'#038bd5','label': 'HT', 'icon': 'h'},
            {'color':'#00a846','label': 'LAPRAP', 'icon': 'l'},
            {'color':'#ee9805','label': 'NHAM', 'icon':'n'},
            {'color':'#2d6adf','label': 'SON', 'icon': 's'},
            {'color':'#ffb748','label': 'UV', 'icon': 'u' },
            {'color':'#555555','label': 'ĐBN','icon': 'd'},
            {'color':'#3cb8ff','label': 'DONGGOI','icon': 'g'}]

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
    ar = (sorted(set(DetailItem.objects.values_list('po', flat=True))) if product else sorted(set(DetailItem.objects.values_list(key, flat=True))))
    res = [{'label': s} for s in ar]

    distinct_colors = generate_colors(len(res))

    for index, itm in enumerate(res):
        itm['color'] = distinct_colors[index]

    return res

def build_combo_list(key, product = True):
    # ar = (sorted(set(ProductItem.objects.values_list(key, flat=True))) if product else sorted(set(DetailItem.objects.values_list(key, flat=True))))
    if product:
        values = [item.get_code() for item in ProductItem.objects.all()]
    else:
        values = [item.get_code() for item in DetailItem.objects.all()]

    # Loại bỏ giá trị trống hoặc None, sau đó lấy tập hợp và sắp xếp
    ar = sorted(set(filter(None, values)))

    res = [{'label': s} for s in ar]

    distinct_colors = generate_colors(len(res))

    for index, itm in enumerate(res):
        itm['color'] = distinct_colors[index]

    return res

@csrf_exempt  # Tạm thời bỏ qua kiểm tra CSRF (chỉ cho việc phát triển, không nên dùng trong môi trường sản xuất)
def receive_product_id(request):
    if request.method == 'POST':
        try:
            # Lấy dữ liệu JSON từ request body
            data = json.loads(request.body)
            product_id = data.get('productid', None)  # Lấy productid từ dữ liệu gửi đến
            print('product_id',product_id)
            # print('ref_days', settings.ref_day_value)

            if not product_id:
                return JsonResponse({'status': 'error', 'message': 'Product ID not provided'}, status=400)

            # Tìm sản phẩm trong cơ sở dữ liệu
            try:
                product = next(item for item in ProductItem.objects.all() if item.get_code() == product_id)
                # details = product.details.filter(name__isnull=False).order_by('name')

                total_qty, total_vol, total_datelist = get_details_date_qty([product])

                res = []

                for detail in product.details.all():
                    if detail.process in SHEET_TYPE_SP or detail.name:
                        ls = []
                        for dt in detail.date.all():
                            # print(dt.process)
                            if ((not settings.ref_day_value) or (f'{dt.day}-{dt.month}' in settings.ref_day_value)) and ((not settings.ref_process_value) or (dt.process in settings.ref_process_value)):
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
                    'total_datelist': [itm['label'] for itm in total_datelist if itm['label'] in total_qty],
                    'selected_dates': settings.ref_day_value or [],
                    'selected_processes': settings.ref_process_value or [],
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
            # print('ref_days', settings.ref_day_value)

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

                    __total = 0

                    for __itm in relate_items: __total += __itm.value

                    res += [{'code':itm.code, 
                             'name':itm.name,
                             'qty':__total,
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
