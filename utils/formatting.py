def get_string_array(array,precision=2):
    return " ".join(f"{x:.{precision}f}" for x in array) + " "

def get_string_dict(dictionary,key_order,name,precision=2):
    array = []
    for key in key_order:
        try:
            tmp = dictionary[key]
        except:
            # print(f"No {name} set for {key}, default to zero")
            tmp = 0
        array.append(tmp)
    return get_string_array(array, precision=precision)

def write_line(f, data, comment="", width=70, end="\n"):
    """
    Write a left-alignd data string with aligned comments,

    Parameters
    ----------
    f : file object
    data : str
        Data portion of the line
    comment : str
        Comment
    width : Column where comment starts
    """
    f.write(f"{data:<{width}}{comment}{end}")
    return None
