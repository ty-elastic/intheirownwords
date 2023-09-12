def strip_field_arrays(fields):
    out = {}
    for key in fields:
        if len(fields[key]) == 1:
            out[key] = fields[key][0]
        else:
            out[key] = fields[key]
    return out
