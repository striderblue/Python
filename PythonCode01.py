import pytz
import datetime
import hashlib
# Online Python - IDE, Editor, Compiler, Interpreter

current_dt = datetime.datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y%m%d%H%M%S')
print(type(current_dt), current_dt)

str_txt = "AC:67:B2:36:4A:34"
print(type(str_txt), str_txt)

concat_txt = f"{current_dt}-{str_txt}"
print(type(concat_txt), concat_txt)

result = hashlib.md5(concat_txt.encode('utf-8'))
print(result.hexdigest())
