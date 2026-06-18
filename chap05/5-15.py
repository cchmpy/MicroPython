import re
s = 'name@email.com'
regex = re.compile('(\w+)@(\w+).(\w+)')
mt = regex.match(s)
for i in range(4):
    print(f'group({i}) =',mt.group(i))
