from django import template
import re

register = template.Library()

@register.filter
def mod(value, divisor):
    try:
        return value % divisor
    except (TypeError, ValueError):
        return None

@register.filter
def split(value, delimiter):
    """
    Tách chuỗi dựa trên ký tự delimiter.
    Sử dụng: {{ your_string|split:',' }}
    """
    return value.split(delimiter)

@register.filter(name='replace_bracket')
def replace_bracket(value):
    """Custom filter to replace ']' with an empty string"""
    return value.replace(']', '')

@register.filter
def get_item(dictionary, key):
    """Trả về giá trị trong dictionary theo key."""
    return dictionary.get(key)

@register.filter
def get_item(list, index):
    try:
        return list[index]
    except IndexError:
        return None  # Or return a default value like "Unknown" if you prefer
    

@register.filter
def convert_date_format(input_string):
    # Kiểm tra nếu chuỗi có dấu '-'
    if '-' in input_string:
        # Tách chuỗi theo dấu '-'
        date_parts = input_string.split('-')

        # Kiểm tra nếu chuỗi có đúng 3 phần và là số
        if len(date_parts) == 3 and date_parts[0].isdigit() and date_parts[1].isdigit() and date_parts[2].isdigit():
            year = date_parts[0]  # yyyy
            month = date_parts[1]  # mm
            day = date_parts[2]    # dd

            # Chuyển đổi thành định dạng dd-mm
            formatted_date = f"{day}-{month}"
            return formatted_date  # Trả về kết quả
    return input_string  # Nếu không phải định dạng ngày tháng, trả lại chuỗi gốc

@register.filter
def multiply(value, arg):
    try:
        result = float(value) * float(arg)
        return round(result, 3)  # Làm tròn đến 3 chữ số thập phân
    except (TypeError, ValueError):
        return 0  # Nếu có lỗi, trả về 0
    

@register.filter
def process_icons(process_str, process_dict):
    # Tách chuỗi thành mảng
    processes = process_str.split(",")
    result = []
    

    all_dict_names = [s['label'] for s in process_dict]

    # Đối chiếu với các phần tử trong đối tượng Process
    # for process in processes:
    #     for p in process_dict:
    #         if p['label'] == process.strip():
    #             # Thêm icon với màu sắc
                
    #             result.append(f'<i class="fas fa-{p['icon']}" style="color: {p['color']};"></i>')
    #             break
    #     else:
    #         # Nếu không có icon tương ứng
    #         result.append(process.strip())

    excludes = []
    for process in processes:
        if not (process in all_dict_names):
            excludes += [process]

    if len(excludes) > 0:
        for process in excludes:
            for p in process_dict:
                if p['label'] == process.strip():
                    result.append(f'<i class="fas fa-{p['icon']}" style="color: {p['color']};"></i>')
    else:
        result.append(f'<i class="fas fa-check-circle" style="color: red;"></i>&nbsp;&nbsp;ALL')
    
    return " ".join(result)

@register.filter
def replace(value, args):
    """
    Replace all occurrences of a substring in a string,
    ignoring case.
    Usage: {{ value|replace_ci:"old,new" }}
    """
    if not value or not args:
        return value
    try:
        old, new = args.split(',')
        return re.sub(re.escape(old), new, value, flags=re.IGNORECASE)
    except ValueError:
        return value

@register.filter
def get_item_at_index(value, index):
    """Trả về phần tử tại chỉ mục index trong danh sách"""
    try:
        return value[index]
    except IndexError:
        return None  # Trả về None nếu chỉ mục không hợp lệ