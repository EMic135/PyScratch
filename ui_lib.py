def all_children(wid, finList=None, indent=0):
    finList = finList or []
    children = wid.winfo_children()
    for item in children:
        finList.append(item)
        all_children(item, finList, indent + 1)
    return finList