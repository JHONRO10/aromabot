# AromaBot — Base de Datos Supabase

## Concepto simple

Supabase es como una hoja de Excel en la nube que nunca se borra,
que AromaBot puede leer y escribir en milisegundos desde cualquier lugar.

---

## Tabla: aroma_inventario

Guarda el stock de TODOS los productos como pares clave/valor.

| clave | valor | significado |
|---|---|---|
| perfumes_invicto | 50 | 50 unidades de Invicto listas para vender |
| perfumes_leblanc | 50 | 50 unidades de Leblanc |
| perfumes_euphoria | 50 | 50 unidades de Euphoria |
| perfumes_holiday | 50 | 50 unidades de Holiday |
| perfumes_delphy | 50 | 50 unidades de Delphy |
| perfumes_yara_candy | 50 | 50 unidades de Yara Candy |
| perfumes_ultramale | 50 | 50 unidades de Ultramale |
| perfumes_kind_of_party | 50 | 50 unidades de Kind of Party |
| cajas_euphoria | 100 | Cajas para Euphoria y Holiday |
| cajas_passionate | 100 | Cajas para Delphy y Yara Candy |
| cajas_succesfull | 100 | Cajas para Invicto y Leblanc |
| cajas_eternity | 100 | Cajas para Ultramale y Kind of Party |
| stickers_euphoria | 100 | Stickers línea Euphoria |
| stickers_passionate | 100 | Stickers línea Passionate |
| stickers_succesfull | 100 | Stickers línea Succesfull |
| stickers_eternity | 100 | Stickers línea Eternity |
| bolsas | 200 | Bolsas (0.5 por perfume vendido) |
| bonos | 200 | Bonos (0.5 por perfume vendido) |
| tarros_60ml | 100 | Tarros vacíos para fabricar |
| alcohol_ml | 5000 | Alcohol en ml (40ml por perfume fabricado) |

## Tabla: aroma_config

Guarda configuraciones y acumulados del mes.

| clave | valor | significado |
|---|---|---|
| utilidad_mes | 0 | Suma de todas mis ganancias del mes |
| ventas_steven | 0 | Perfumes vendidos por Steven este mes |
| ventas_jairo | 0 | Perfumes vendidos por Jairo este mes |
| ventas_jeferson | 0 | Perfumes vendidos por Jeferson este mes |
| ventas_yo | 0 | Perfumes que vendí yo directamente |

## Tabla: aroma_pedidos

Historial de cada venta registrada.

| columna | tipo | significado |
|---|---|---|
| id | uuid | Identificador único auto-generado |
| distribuidor | text | Nombre del distribuidor |
| productos | jsonb | Qué perfumes y cuántos |
| total_perfumes | int | Total de unidades de esa venta |
| mi_utilidad | float | Cuánto gané yo en esa venta |
| created_at | timestamp | Cuándo se registró |

---

## Reglas de negocio críticas

### Al VENDER descuenta:
- perfume vendido
- caja de su línea
- sticker de su línea
- 0.5 bolsas por perfume
- 0.5 bonos por perfume

### Al FABRICAR descuenta:
- 1 tarro 60ml por perfume
- 40ml de alcohol por perfume

### Al FABRICAR suma:
- El perfume terminado al stock

### Mapa de referencias (perfume → línea de caja/sticker):
| Perfume | Línea |
|---|---|
| euphoria, holiday | euphoria |
| delphy, yara_candy | passionate |
| invicto, leblanc | succesfull |
| ultramale, kind_of_party | eternity |

---

## Cómo resetear el inventario

Si necesitas volver a los valores iniciales, llama este endpoint una vez:
```
GET https://web-production-f4795.up.railway.app/init-inventario
```
**ADVERTENCIA:** Esto sobreescribe el inventario actual. Úsalo solo si hay datos corruptos.
