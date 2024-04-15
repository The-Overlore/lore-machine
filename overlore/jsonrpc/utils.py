def snake_to_camel(in_str: str) -> str:
    temp = in_str.split("_")
    res = temp[0] + "".join(ele.title() for ele in temp[1:])

    return res
