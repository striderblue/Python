import re

txt = "ntsandbox/core/energy/7C:DF:A1:F4:D7:A0/solar01"
pattern = r"ntsandbox/core/([^/]+)/([^/]+)/([^/]+)"

x = re.match(pattern, txt)

if x:
    print(x)
    print(x.groups())
    print(x.group(1))
