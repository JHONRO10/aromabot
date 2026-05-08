DISTRIBUIDORES = {
    "steven":   {"nombre": "Steven Rojas",     "tel": "573213143902", "precio": 5750},
    "jairo":    {"nombre": "Jairo Jiménez",    "tel": "573161289921", "precio": 6750},
    "jeferson": {"nombre": "Jeferson Saldaña", "tel": "573044372629", "precio": 7250},
    "yo":       {"nombre": "Yo (Calle)",       "tel": "",             "precio": 25000},
}
# mi_util se calcula dinamicamente: precio - COSTOS["perfume"]
# Steven $500 | Jairo $1.500 | Jeferson $2.000 | Yo $19.750

PERF_REF = {
    "euphoria":      "euphoria",
    "holiday":       "euphoria",
    "delphy":        "passionate",
    "yara_candy":    "passionate",
    "invicto":       "succesfull",
    "leblanc":       "succesfull",
    "ultramale":     "eternity",
    "kind_of_party": "eternity",
}

COSTOS = {
    "perfume":     5250,  # COP por perfume terminado
    "tarros_60ml": 2135,  # COP por tarro 60ml
    "alcohol_ml":  7,     # COP por ml — galon $28.000 / 3785 ml = $7,40 (redondeado)
    "cajas":       530,   # COP por caja
    "stickers":    60,    # COP por sticker
    "bolsas":      50,    # COP por bolsa
    "bonos":       35,    # COP por bono
}

# Costo de reposicion de alcohol: $28.000 por galon (3785 ml)
ALCOHOL_GALON_COP = 28_000
