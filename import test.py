from inspect import getmembers

libraries=['math','random', 'egsegsegseg']
words={}
for lib in libraries:
    try:
        exec(f'import {lib}\nwords["{lib}"]=[member[0] for member in getmembers({lib})]')
    except ModuleNotFoundError:
        print(f'Can`t find module {lib}')
    except Exception as e:
        raise e
getattr(random,'randint')
compile('exit()','<string>','exec')
print('hi')
compile("random.randint(1,10)",'<string>','exec')
print(random.randint("string_example", 10))