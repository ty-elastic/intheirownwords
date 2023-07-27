def strip_field_arrays(fields):
    out = {}
    for key in fields:
        out[key] = fields[key][0]
    return out
