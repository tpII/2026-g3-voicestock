# Sentido de las transcripciones por dificultad

Revisión cualitativa manual de 10 prompts, 8 configuraciones y 240 transcripciones medidas. No se repitió inferencia.
Las tres repeticiones cuentan como un solo caso por modelo; se revisaron todas las variantes y se adopta la más problemática.

- Coherente: operación final, cantidad y artículo activo reconocibles.
- Ambigua: necesita interpretar nombres o expresiones deformadas.
- Sentido comprometido: pierde/cambia acción, cantidad, corrección o una prohibición explícita.

Números escritos con palabras y unidades equivalentes se aceptan. Errores de nombres cancelados no invalidan una cancelación total clara. Los nombres activos dudosos se califican como ambiguos.
No se escuchó el audio ni se validó un parser. Estos porcentajes son juicios sobre este corpus, no probabilidades de fiabilidad.

## Corpus

- **basico** (2): solo_agregar, solo_restar
- **habitual** (4): restar_ambos, corregir_cantidad, negar_agregacion, negar_restacion
- **exigente** (4): negar_varias_agregaciones, negar_varias_restaciones, negar_agregacion_y_restacion, caso_integral

## Resumen

Cada celda: coherentes / ambiguos / comprometidos (porcentaje coherente).

| Modelo | Básico (2) | Habitual (4) | Exigente (4) |
| --- | --- | --- | --- |
| vosk_full | 1 / 1 / 0 (50%) | 0 / 2 / 2 (0%) | 0 / 2 / 2 (0%) |
| vosk_250ms | 1 / 1 / 0 (50%) | 0 / 2 / 2 (0%) | 0 / 2 / 2 (0%) |
| whisper_tiny | 1 / 0 / 1 (50%) | 2 / 1 / 1 (50%) | 0 / 2 / 2 (0%) |
| whisper_base | 2 / 0 / 0 (100%) | 2 / 1 / 1 (50%) | 0 / 4 / 0 (0%) |
| whisper_small_q5_1 | 2 / 0 / 0 (100%) | 4 / 0 / 0 (100%) | 1 / 0 / 3 (25%) |
| moonshine_tiny_es | 1 / 1 / 0 (50%) | 3 / 0 / 1 (75%) | 0 / 3 / 1 (0%) |
| moonshine_small_es | 1 / 1 / 0 (50%) | 4 / 0 / 0 (100%) | 1 / 1 / 2 (25%) |
| kroko_es | 0 / 2 / 0 (0%) | 2 / 1 / 1 (50%) | 1 / 2 / 1 (25%) |

## Interpretación

Whisper Small Q5 conserva el sentido inequívoco en todos los casos básicos y habituales. Moonshine Small también conserva todos los habituales, pero deforma Sprite en el básico de agregar. Esto matiza la recomendación general anterior: con este criterio explícito, Whisper Small lidera básico/habitual.
En exigente no hay ganador suficiente: Whisper Small y Moonshine Small tienen un caso coherente cada uno, y errores críticos en otros. Kroko conserva mejor la estructura del integral, pero un nombre activo dudoso impide calificarlo como inequívoco. No se descarta Kroko; se distingue preservación de instrucciones de identificación precisa.

## Detalle por prompt

### solo_agregar — basico

**Referencia:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**vosk_full: ambigua** — Sprite deformado; en Kroko además termina en «li». Acción y cantidades conservadas.

> agrega tres coca-cola comunes de dos litros y cuatro spray comunes de uno coma cinco litros

**vosk_250ms: ambigua** — Sprite deformado; en Kroko además termina en «li». Acción y cantidades conservadas.

> agrega tres coca-cola comunes de dos litros y cuatro spray comunes de uno coma cinco litros

**whisper_tiny: coherente** — Acción, cantidades, nombres y unidades reconocibles.

> agrega 3 Coca-Cola comunes de 2 litros y 4 sprite comunes de 1,5 litros

**whisper_base: coherente** — Acción, cantidades, nombres y unidades reconocibles.

> Agrega 3 Coca-Cola comunes de 2 litros y 4 sprite comunes de 1,5 litros.

**whisper_small_q5_1: coherente** — Acción, cantidades, nombres y unidades reconocibles.

> Agrega 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

**moonshine_tiny_es: ambigua** — Sprite deformado; en Kroko además termina en «li». Acción y cantidades conservadas.

> agrega tres coca cola comunes de dos litros y cuatro pryt comunes de uno coma cinco litros

**moonshine_small_es: ambigua** — Sprite deformado; en Kroko además termina en «li». Acción y cantidades conservadas.

> agrega tres coca cola comunes de dos litros y cuatro sprays comunes de uno coma cinco litros

**kroko_es: ambigua** — Sprite deformado; en Kroko además termina en «li». Acción y cantidades conservadas.

> Agregar tres Coca-Cola comunes de dos litros y cuatro sprays comunes de uno coma cinco li

### solo_restar — basico

**Referencia:** Restá dos paquetes de arroz Gallo de 1 kg.

**vosk_full: coherente** — Resta de dos paquetes de arroz Gallo de un kilo reconocible.

> resta dos paquetes de arroz gallo de un kilo

**vosk_250ms: coherente** — Resta de dos paquetes de arroz Gallo de un kilo reconocible.

> resta dos paquetes de arroz gallo de un kilo

**whisper_tiny: sentido_comprometido** — Verbo → Prega y nombre deformado: operación no clara.

> Prega 2 paquetes de arroz gashos de 1 kilo

**whisper_base: coherente** — Resta de dos paquetes de arroz Gallo de un kilo reconocible.

> resta 2 paquetes de arroz gallo de 1 kilo

**whisper_small_q5_1: coherente** — Resta de dos paquetes de arroz Gallo de un kilo reconocible.

> Resta dos paquetes de arroz gallo de un kilo.

**moonshine_tiny_es: coherente** — Resta de dos paquetes de arroz Gallo de un kilo reconocible.

> resta dos paquetes de arroz gallo de un kilo

**moonshine_small_es: coherente** — Resta de dos paquetes de arroz Gallo de un kilo reconocible.

> resta dos paquetes de arroz gallo de un kilo

**kroko_es: ambigua** — Gallo → gaso: marca dudosa.

> Resta dos paquetes de arroz gaso de un kilo

### restar_ambos — habitual

**Referencia:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**vosk_full: sentido_comprometido** — Se pierde la cantidad dos o la acción, según modelo; Vosk tiene variantes medidas sin cantidad y Zero → serio.

> resta dos coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

> resta coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

**vosk_250ms: sentido_comprometido** — Se pierde la cantidad dos o la acción, según modelo; Vosk tiene variantes medidas sin cantidad y Zero → serio.

> resta dos coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

> resta coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

> resta tus coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

**whisper_tiny: coherente** — Ambas restas y cantidades conservadas; cero/0 y unidades en palabras aceptados.

> Restar 2 Coca-Cola a 0 de 2 litros y 4 envases de detergente magistral de 750 ml.

**whisper_base: sentido_comprometido** — Se pierde la cantidad dos o la acción, según modelo; Vosk tiene variantes medidas sin cantidad y Zero → serio.

> Resta, toco cacola a 0 de 2 litros y 4 embases de detergente magistral de 750 ml.

**whisper_small_q5_1: coherente** — Ambas restas y cantidades conservadas; cero/0 y unidades en palabras aceptados.

> Resta 2 Coca-Cola 0 de 2 litros y 4 en bases de detergente magistral de 750 mililitros.

**moonshine_tiny_es: sentido_comprometido** — Se pierde la cantidad dos o la acción, según modelo; Vosk tiene variantes medidas sin cantidad y Zero → serio.

> resta tosco cacola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

**moonshine_small_es: coherente** — Ambas restas y cantidades conservadas; cero/0 y unidades en palabras aceptados.

> resta dos coca cola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

**kroko_es: sentido_comprometido** — Se pierde la cantidad dos o la acción, según modelo; Vosk tiene variantes medidas sin cantidad y Zero → serio.

> Coca-Cola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

### corregir_cantidad — habitual

**Referencia:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**vosk_full: sentido_comprometido** — Verbo inicial irreconocible (a great/Agree) y/o nombre deformado.

> a great tres coca cola comunes de dos litros perdón eran dos

> a great tres cola comunes de dos litros perdón eran dos

**vosk_250ms: sentido_comprometido** — Verbo inicial irreconocible (a great/Agree) y/o nombre deformado.

> a great tres coca cola comunes de dos litros perdón eran dos

**whisper_tiny: sentido_comprometido** — Verbo inicial irreconocible (a great/Agree) y/o nombre deformado.

> Agree, 3 cocacó la comune de 2 litros perdón, eran 2.

**whisper_base: coherente** — Acción reconocible y corrección tres → dos conservada.

> Agrega, 3 coca-cola comunes de 2 litros, perdón, eran 2.

**whisper_small_q5_1: coherente** — Acción reconocible y corrección tres → dos conservada.

> Agrega 3 Coca-Cola comunes de 2 litros, perdón eran 2.

**moonshine_tiny_es: coherente** — Acción reconocible y corrección tres → dos conservada.

> agregad tres coca cola comunes de dos litros perdón eran dos

**moonshine_small_es: coherente** — Acción reconocible y corrección tres → dos conservada.

> agrega tres coca cola comunes de dos litros perdón eran dos

**kroko_es: coherente** — Acción reconocible y corrección tres → dos conservada.

> Agregar tres Coca-Cola comunes de dos litros, perdón, eran dos

### negar_agregacion — habitual

**Referencia:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**vosk_full: ambigua** — Razón de cancelación presente, pero instrucción final deformada, truncada o sin su no.

> agrega cinco botellas de agua villavicencio de uno coma cinco litros perdón esas no llegar a no las carnes

**vosk_250ms: ambigua** — Razón de cancelación presente, pero instrucción final deformada, truncada o sin su no.

> agrega cinco botellas de agua villavicencio de uno coma cinco litros perdón esas no llegar a no las carnes

**whisper_tiny: ambigua** — Razón de cancelación presente, pero instrucción final deformada, truncada o sin su no.

> Abrega 5 de agua visualicencia de 1,5 litros. Perdón, esas no llegaron a las carres.

**whisper_base: ambigua** — Razón de cancelación presente, pero instrucción final deformada, truncada o sin su no.

> Abrega 5 tallas de agua vizadiscencio de 1,5 litros. Perdón, esas no llegaron las cargues.

**whisper_small_q5_1: coherente** — Cancelación completa explícita; marca deformada no impide cancelar todas las operaciones de este caso.

> Agrega 5 botellas de agua billa de licencia de 1,5 litros. Perdón, esas no llegaron, no las cargues.

**moonshine_tiny_es: coherente** — Cancelación completa explícita; marca deformada no impide cancelar todas las operaciones de este caso.

> agrega cinco botellas de agua visualicencia de uno coma cinco litros perdón esas no llegaron no las cargues

**moonshine_small_es: coherente** — Cancelación completa explícita; marca deformada no impide cancelar todas las operaciones de este caso.

> agrega cinco botellas de agua a visodicencio de uno coma cinco litros perdón esas no llegaron no las cargues

**kroko_es: ambigua** — Razón de cancelación presente, pero instrucción final deformada, truncada o sin su no.

> Agrega cinco botellas de agua visuavicencio de uno coma cinco litros. Perdón, esas no llegaron, no las car

### negar_restacion — habitual

**Referencia:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**vosk_full: ambigua** — Cancelación final deformada (no lo agrestes); requiere interpretación.

> resta cuatro envases detergentes magistral de setecientos cincuenta mililitros perdón no se vendieron no lo agrestes

**vosk_250ms: ambigua** — Cancelación final deformada (no lo agrestes); requiere interpretación.

> resta cuatro envases detergentes magistral de setecientos cincuenta mililitros perdón no se vendieron no lo agrestes

**whisper_tiny: coherente** — No se vendieron / no los restes conserva inequívocamente la cancelación total, aunque haya errores en el nombre o verbo inicial.

> Resta 4 en bases de 300 magistrales de 750 mililitros, pero no se vendieron, no los restes.

**whisper_base: coherente** — No se vendieron / no los restes conserva inequívocamente la cancelación total, aunque haya errores en el nombre o verbo inicial.

> Restá 4 envases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

**whisper_small_q5_1: coherente** — No se vendieron / no los restes conserva inequívocamente la cancelación total, aunque haya errores en el nombre o verbo inicial.

> Resta 4 en bases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

**moonshine_tiny_es: coherente** — No se vendieron / no los restes conserva inequívocamente la cancelación total, aunque haya errores en el nombre o verbo inicial.

> restá cuatro envases de detergente magistral de setecientos cincuenta mililitros perdón no se vendieron no los restes

**moonshine_small_es: coherente** — No se vendieron / no los restes conserva inequívocamente la cancelación total, aunque haya errores en el nombre o verbo inicial.

> resta cuatro envases de detergentes magistral de setecientos cincuenta mililitros perdón no se vendieron no los restes

**kroko_es: coherente** — No se vendieron / no los restes conserva inequívocamente la cancelación total, aunque haya errores en el nombre o verbo inicial.

> Pero está cuatro envases de detergentes magistral de setecientos cincuenta mililitros. Perdón, no se vendieron, no los restes

### negar_varias_agregaciones — exigente

**Referencia:** Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

**vosk_full: ambigua** — Artículo pendiente arroz Gallo deformado; no se puede garantizar identidad.

> agrega tres coca cola comunes de dos litros cuatro spray comunes de uno coma cinco litros y cinco paquete de ahorro gallo de un kilo medio que las coca colas comunes de dos litros y las esprit comunes de uno coma cinco no las cargues

**vosk_250ms: ambigua** — Artículo pendiente arroz Gallo deformado; no se puede garantizar identidad.

> agrega tres cola comunes de dos litros cuatro spray comunes de uno coma cinco litros y cinco paquete de ahorro gallo de un kilo medio que las coca colas comunes de dos litros y las esprit comunes de uno coma cinco no las cargues

**whisper_tiny: ambigua** — Artículo pendiente arroz Gallo deformado; no se puede garantizar identidad.

> Abrega 3 Coca-Cola comunes de 2 litros, 4 sprite comunes de 1,5 litros y 5 pague de arrogayo de un kilo. Me guivo que las Coca-Cola comunes de 2 litros y las sprite comunes de 1,5 no las carres.

**whisper_base: ambigua** — Artículo pendiente arroz Gallo deformado; no se puede garantizar identidad.

> A agregar 3 cocacolas comunes de 2 litros, 4 sprites comunes de 1,5 litros y 5 paquetes de rogallos de 1 kilo. Me equivoque las cocacolas comunes de 2 litros y las sprites comunes de 1,5 no las cargas.

**whisper_small_q5_1: sentido_comprometido** — Falta verbo inicial de agregar: operación pendiente sobre arroz implícita.

> 3 Coca-Cola comunes de 2 litros 4 Sprite comunes de 1,5 litros y 5 paquetes de arroz gallo de 1 kilo. Me equivoque, las Coca-Cola comunes de 2 litros y Sprite comunes de 1,5 no las cargués.

**moonshine_tiny_es: ambigua** — Artículo pendiente arroz Gallo deformado; no se puede garantizar identidad.

> agregad tres coca cola comunes de dos litros cuatro sprite comunes de uno coma cinco litros y cinco paquetes de arroga sho de un kilo me equivoqué las coca colas comunes de dos litros y las sprite comunes de uno coma cinco no las cargues

**moonshine_small_es: coherente** — Verbo de agregar, arroz Gallo pendiente y cancelaciones conservados; Sprite deformado queda cancelado de manera consistente.

> agrega tres coca cola comunes de dos litros cuatro spray comunes de 1,5 litros y cinco paquetes de arroz gallo de un kilo me equivoqué las coca colas comunes de dos litros y las spray comunes de uno coma cinco no las cargues

**kroko_es: coherente** — Verbo de agregar, arroz Gallo pendiente y cancelaciones conservados; Sprite deformado queda cancelado de manera consistente.

> Agrega tres Coca-Cola común es de dos litros, cuatro sprays comunes de uno comas cinco litros y cinco paquetes de arroz gallo de un kilo. Me equivoqué, las Coca-Colas comunes de dos litros y las spray comunes, de uno coma cinco, no las cargues

### negar_varias_restaciones — exigente

**Referencia:** Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

**vosk_full: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> presta dos coca-cola cero de dos litros tres paquetes arroyo de un kilo y cuatro en de detergente magistral de setecientos cincuenta mililitros las coca cero y el arroz no se vendieron no los prestes

**vosk_250ms: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> presta dos coca-cola cero de dos litros tres paquetes arroyo de un kilo y cuatro en de detergente magistral de setecientos cincuenta mililitros las coca cero y el arroz no se vendieron no los prestes

**whisper_tiny: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> presta 2 cocacola 0 de 2 litros, 3 paquetes de arroz vayo de un kilo y 4 en bases de de tergen de magistral de 75 mililitros. Las cocaceros y el arroz no se vendieron, no los restes.

**whisper_base: ambigua** — Acción y cantidades reconocibles, pero detergente Magistral deformado; identidad incierta.

> Reesta 2 cocacolla 0 de 2 litros, 3 paquetes de arroz gallo de un kilo y 4 envases de terjén de magistral de 750 ml. Las coca 0 y el arroz no se vendieron, no los restes.

**whisper_small_q5_1: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> Prestar 2 Coca-Cola 0 de 2 litros, 3 paquetes de arroz gallo de 1 kilo y 4 en base de detergente magistral de 750 mililitros. Las Coca-0 y el arroz no se vendieron, no los restes.

**moonshine_tiny_es: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> presta dos coca colas cero de dos litros tres paquetes de arroja sho de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros las cocas hero y el arroz no se vendieron no los restes

**moonshine_small_es: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> presta dos coca cola cero de dos litros tres paquetes de arroz gallo de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros las cocas cero y el arroz no se vendieron no los restes

**kroko_es: sentido_comprometido** — Restá → presta/Prestar: resta pendiente de detergente queda expresada como otra acción; Tiny además cambia 750 → 75 ml.

> Presta dos Coca-Cola cero de dos litros, tres paquetes de rosgallo de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros. Las cocas cero y el arroz no se vendieron, no los restes.

### negar_agregacion_y_restacion — exigente

**Referencia:** Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

**vosk_full: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> agrega cuatro spray comunes de dos litros y resta dos paquetes de arroz gallo de un kilo perdón la césped no llegaron y el arroz no se vendió nuevas ninguna de esas dos operaciones

**vosk_250ms: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> agrega cuatro spray comunes de dos litros y resta dos paquetes de arroz gallo de un kilo perdón la césped no llegaron y el arroz no se vendió nuevas ninguna de esas dos operaciones

**whisper_tiny: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> Agrega, cuatro sprite comunes de dos litros y restados paquetes de arroz gallos de un kilo. Perdón, las especies no llegaron y el arroz no se vendió. No has ninguna de esas dos operaciones.

**whisper_base: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> Agrega, cuatro sprites comunes de dos litros y resta dos paquetes de arroz gallos de un kilo. Perdón, las sprites no llegaron y el arroz no se vendió, no das ninguna de esas dos operaciones.

**whisper_small_q5_1: coherente** — Cancelación total explícita no hagas ninguna; nombres deformados no alteran el resultado de cancelar ambas.

> Agrega 4 spray comunes de 2 litros y resta 2 paquetes de arroz gallo de 1 kilo. Perdón, las spray no llegaron y el arroz no se vendió, no hagas ninguna de esas 2 operaciones.

**moonshine_tiny_es: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> agrega cuatro spray comunes de dos litros y restad dos paquetes de arrojacho de un kilo perdón las spain no llegaron y el arroz no se vendió no das ninguna de esas dos operaciones

**moonshine_small_es: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> agrega cuatro sprays comunes de dos litros y restad dos paquetes de arroz gallo de un kilo perdón las espéim no llegaron y el arroz no se vendió no das ninguna de esas dos operaciones

**kroko_es: ambigua** — Instrucción final no das/Novas/nuevas/no has y/o referencias de Sprite deformadas: requiere interpretación.

> Agrega cuatro spys comunes de dos litros y resta dos paquetes de arroz gallo de un kilo. Perdón, las spike no llegaron y el arroz no se vendió. Novas ninguna de esas dos operaciones

### caso_integral — exigente

**Referencia:** Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

**vosk_full: sentido_comprometido** — Restá dos Sprite → resta doce; nombres y negaciones deformados.

> agrega tres cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

> agrega tres coca cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

**vosk_250ms: sentido_comprometido** — Restá dos Sprite → resta doce y omite cantidad tres de fideos.

> agrega tres coca comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

> agrega tres cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos así que no los cargues resta dos paquetes de arroz gallo de un kilo y paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no reste es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

> agrega tres coca cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

**whisper_tiny: sentido_comprometido** — Cambia 2 litros → 1/2 y 750 → 75 ml; deforma corrección y cancelaciones.

> Agrega, 3 cucacola con 1/2 litros, prón, el andos, agrega 4 prítcomunes de 1,5 litros y 5 tillas de agua visavicencia de 1,5 litros. Prón, no yo hago ni 1 de esos 2 productos, así lleno los carres, resta 2 paquetes de arroz gallo de 1 kilo y 3 paquetes de fíjidos matarasos y 500 gramos. Resta 4 cococola 0 de 2 litros y 5 en bases de de 3 gente magistral de 75 ml. Perdón, ni las cocacelen y los detergentes se vendieron, no resten 1 de esos 2 productos. Agrega 6 en bases de leche y la serenísima, de 1 litro y resta 2 spray comune de 2 litros. Perdón, la leche no llegó y esa se spray no se vendieron, no carrega la leche ni resta y se ases prítos.

**whisper_base: ambigua** — Conserva corrección, cantidades y cancelaciones recuperables; arroz/fideos y marcas deformados.

> Agrega, tres cocacola comunes de dos litros, perdón, eran dos. Agrega, cuatro spray comunes de uno coma cinco litros y cinco dotellas de agua vizabicensio de uno coma cinco litros. Perdón, no llegó ni uno de esos dos productos, así que no en los carreras. Resta a dos paquetes de arroz gayo de un kilo y tres paquetes de fíjidos matarazo de 500 gramos. Resta a cuatro cocacola cero de dos litros y cinco envases de detergente magistral de 750 mililitros. Perdón, ni las cocaceron y los detergentes se vendieron, no restes ninguno de esos dos productos. Agrega, seis envases de leche y la serenísima, de un litro y restas dos spray comunes de dos litros. Perdón, la leche no llegó y esas spray no se vendieron, no carges la leche ni restes esas spray.

**whisper_small_q5_1: sentido_comprometido** — Omite Agregá y perdón eran dos: queda tres en lugar de dos en la operación inicial.

> 3 Coca-Cola comunes de 2 litros, 4 Sprite comunes de 1,5 litros y 5 botellas de agua viva visencio de 1,5 litros. No llegó ninguno de esos 2 productos, así que no los cargués. Resta 2 paquetes de arroz gallo de 1 kilo y 3 paquetes de fideos matarazos de 500 gramos. Resta 4 Coca-Cola 0 de 2 litros y 5 en bases de detergente magistral de 750 ml. Perdón, ni las Coca-cero ni los detergentes se vendieron, no restes ninguno de esos 2 productos. Agrega 6 en bases de leche lazerenísima de 1 litro y resta 2 Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron. No cargués la leche ni restes esa Sprite.

**moonshine_tiny_es: ambigua** — Conserva corrección y prohibiciones finales; razón no se vendieron pierde no y arroz Gallo queda deformado.

> agrega tres coca cola comunes de dos litros perdón eran dos agrega cuatro spray comunes de uno coma cinco litros y cinco botellas de agua bishavicencia de uno coma cinco litros perdón no llego a ninguno de esos dos productos así que no los cargues resta a dos paquetes de arroga sho de un kilo y tres paquetes de fideos matarazos de quinientos gramos resta cuatro coca cola cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros perdón ni las cocaseron ni los detergentes se vendieron no restes ninguno de esos dos productos agrega seis envases de leche la cerenísima un litro y restar dos spray comunes de dos litros perdón la leche nos llevó y esas espeñas se vendieron no cargues la leche ni restes esas sprite

**moonshine_small_es: sentido_comprometido** — Conserva corrección pero así que no los cargues → así lleno los cargues: pierde prohibición explícita.

> agrega tres coca cola comunes de dos litros perdón eran dos agrega cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llevo ninguno de esos dos productos así lleno los cargues restar dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarazos de 500 gramos resta cuatro coca cola cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros perdón ni las coca cero ni los detergentes se vendieron no restes ninguno de esos dos productos agrega a seis envases de leche la serenísima en un litro y restar dos spray comunes de dos litros perdón la leche no llegó y esas espéi no se vendieron no cargues la leche ni restes esas spray

**kroko_es: ambigua** — Conserva corrección, cantidades y todas las cancelaciones explícitas; nombre activo Matarazzo → matarazos queda dudoso.

> Agrega tres Coca-Cola comunes de dos litros, perdón, eran dos. Agrega cuatro sprays comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno comas cinco litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargués. Resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarazos de quinientos gramos. Resta cuatro Coca-Cola, cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros. Perdón, ni las coca ceros ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agrega seis envases de leche la serenísima, de un litro y resta dos spray comunes de dos litros. Perdón, la leche no llegó y esas sprays no se vendieron. No cargues la leche ni restes esas sprays.
