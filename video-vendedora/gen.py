"""Genera escena.svg: 'Así construimos una vendedora con IA en una tarde' (3GO Video), 1080x1920."""
import json, random, sys
sys.path.insert(0, "/root/.claude/skills/synced/58f317dc-92f5-47ed-b7d3-83559a0b31d5_00e12ad1-65ef-4451-a870-4d18a6460c45/video-artesanal/scripts")
from texto import encajar, ancho

W, H = 1080, 1920
B = json.load(open("beats.json"))
BAR = B["bar"]
KICK = B["kick"]
DUR = B["duracion"]
SC = [BAR[0], BAR[2], BAR[4], BAR[6], BAR[8], DUR]  # inicio de cada escena
KRAFT, CARTON, CREMA, TINTA = "#C9A779", "#8C6A43", "#F3EBDD", "#2B2622"
ROJO, AZUL, AMAR, VERDE = "#C8423A", "#3E6FA8", "#F2D16B", "#4E9A5B"
SANS, MONO = "DejaVu Sans", "DejaVu Sans Mono"
rnd = random.Random(6)
out = []


def kicks(t0, t1):
    return [k for k in KICK if t0 <= k < t1]


def aparece(t, salto=28):
    """Animaciones para que un grupo aparezca en t, como colocado a mano."""
    return (f'<set attributeName="opacity" to="1" begin="{t:.3f}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" additive="sum" values="0 {-salto};0 6;0 0" '
            f'dur="0.25s" begin="{t:.3f}s" calcMode="discrete" fill="freeze"/>')


def rebote(ts, amp=14):
    return "".join(f'<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;0 {-amp};0 0" '
                   f'dur="0.25s" begin="{t:.3f}s" calcMode="discrete" fill="remove"/>' for t in ts)


def cinta(x, y, ang, w=110, h=34):
    dientes = "".join(f"L{-w/2 + 2*(i%2)},{-h/2 + i*h/8:.1f} " for i in range(9))
    dientes2 = "".join(f"L{w/2 - 2*(i%2)},{h/2 - i*h/8:.1f} " for i in range(9))
    return (f'<path transform="translate({x},{y}) rotate({ang})" d="M{-w/2},{-h/2} L{w/2},{-h/2} {dientes2} L{-w/2},{h/2} {dientes} Z" '
            f'fill="{CREMA}" fill-opacity="0.65" stroke="#fff" stroke-opacity="0.3"/>')


def caja_texto(id_, x, y, w, h, texto, color, tam=72, fam=SANS, tinta=TINTA, ang=0, pad=40, filtro="recorte", ancla="middle"):
    """Recuadro de papel con texto medido. (x, y) es el centro."""
    lineas, t = encajar(texto, w - 2 * pad, h - 2 * pad, tam=tam, familia=fam)
    al = t * 1.25
    y0 = -(len(lineas) - 1) * al / 2 + t * 0.35
    s = f'<g transform="translate({x},{y}) rotate({ang})"><rect id="{id_}" x="{-w/2}" y="{-h/2}" width="{w}" height="{h}" rx="6" fill="{color}" filter="url(#{filtro})"/>'
    tx = 0 if ancla == "middle" else -w / 2 + pad
    for i, l in enumerate(lineas):
        s += (f'<text data-dentro="{id_}" data-pad="{pad - 8}" x="{tx}" y="{y0 + i*al:.0f}" font-family="{fam}" font-weight="bold" '
              f'font-size="{t}" fill="{tinta}" text-anchor="{ancla}">{l}</text>')
    return s + "</g>"


def arranque(t_fin):
    """La hoja se arranca desde la esquina superior izquierda y desaparece en t_fin."""
    t = t_fin - 0.42
    return (f'<animateTransform attributeName="transform" type="rotate" values="0 0 0;-4 0 0;-11 0 0;-24 0 0;-40 0 0" '
            f'dur="0.42s" begin="{t:.3f}s" calcMode="discrete" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;-20 10;-90 60;-300 220;-700 520" '
            f'dur="0.42s" begin="{t:.3f}s" calcMode="discrete" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t_fin:.3f}s" fill="freeze"/>')


def hoja(color, rayas=False):
    s = f'<rect width="{W}" height="{H}" fill="{color}"/>'
    if rayas:
        s += f'<rect width="{W}" height="{H}" fill="url(#corrugado)"/>'
    return s


DEFS = f"""<defs>
<pattern id="corrugado" width="14" height="14" patternUnits="userSpaceOnUse"><rect width="6" height="14" fill="#000" opacity="0.07"/></pattern>
<filter id="tiembla"><feTurbulence type="turbulence" baseFrequency="0.03" numOctaves="2" seed="1">
<animate attributeName="seed" values="1;2;3" dur="0.25s" calcMode="discrete" repeatCount="indefinite"/></feTurbulence>
<feDisplacementMap in="SourceGraphic" scale="4"/></filter>
<filter id="recorte" x="-10%" y="-10%" width="120%" height="125%"><feMorphology in="SourceAlpha" operator="dilate" radius="4" result="borde"/>
<feFlood flood-color="#FFFFFF"/><feComposite in2="borde" operator="in" result="blanco"/>
<feOffset in="borde" dx="5" dy="7" result="sombra"/><feFlood flood-color="#000" flood-opacity="0.28"/><feComposite in2="sombra" operator="in" result="sombraC"/>
<feMerge><feMergeNode in="sombraC"/><feMergeNode in="blanco"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="sombra" x="-10%" y="-10%" width="125%" height="130%"><feOffset in="SourceAlpha" dx="6" dy="9"/><feGaussianBlur stdDeviation="3"/>
<feComponentTransfer><feFuncA type="linear" slope="0.3"/></feComponentTransfer><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="grano" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="3"/>
<feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="table" tableValues="0 0.10"/></feComponentTransfer></filter>
</defs>"""


# ---------- Escena 1: título ----------
def escena1():
    t0, t1 = SC[0], SC[1]
    s = f'<g id="e1">{hoja(KRAFT, True)}'
    s += caja_texto("marca1", 540, 210, 420, 120, "3GO Video", TINTA, tam=56, tinta=CREMA, ang=-2)
    palabras = [("UNA", AZUL, -4), ("VENDEDORA", ROJO, 3), ("CON IA", VERDE, -2)]
    ks = kicks(t0 + 0.4, t1)
    for i, (p, c, ang) in enumerate(palabras):
        w = ancho(p, 130) + 110
        y = 560 + i * 230
        tt = ks[i] if i < len(ks) else t0 + 0.5 + i * 0.6
        s += f'<g opacity="0" filter="url(#tiembla)">{caja_texto(f"t1_{i}", 540, y, w, 190, p, c, tam=130, tinta=CREMA, ang=ang, pad=50)}{aparece(tt, 40)}</g>'
    # post-it 'en una tarde' + reloj
    tt = ks[3] if len(ks) > 3 else t0 + 2.6
    s += f'<g opacity="0">{caja_texto("postit1", 330, 1330, 470, 300, "en una sola tarde", AMAR, tam=72, ang=-5)}{cinta(330, 1185, -6)}{aparece(tt)}</g>'
    s += f'<g opacity="0">{reloj(790, 1340, "1:00 pm", t0)}{aparece(tt + 0.3)}</g>'
    s += arranque(t1) + "</g>"
    return s


def reloj(cx, cy, etiqueta, t0, r=150):
    s = f'<g transform="translate({cx},{cy})" filter="url(#tiembla)"><circle r="{r}" fill="{CREMA}" stroke="{TINTA}" stroke-width="8" filter="url(#recorte)"/>'
    for i in range(12):
        s += f'<rect x="-4" y="{-r+14}" width="8" height="22" fill="{TINTA}" transform="rotate({i*30})"/>'
    # minutero que avanza a saltos con cada tiempo
    pasos = ";".join(f"{i*30} 0 0" for i in range(9))
    s += (f'<g><rect x="-6" y="{-r+40}" width="12" height="{r-40}" rx="6" fill="{ROJO}"/>'
          f'<animateTransform attributeName="transform" type="rotate" values="{pasos}" dur="4.8s" begin="{t0:.3f}s" calcMode="discrete" fill="freeze"/></g>')
    s += f'<rect x="-6" y="-70" width="12" height="70" rx="6" fill="{TINTA}" transform="rotate(30)"/><circle r="14" fill="{TINTA}"/></g>'
    s += caja_texto(f"hora_{etiqueta.replace(':','').replace(' ','')}", cx, cy + r + 75, 300, 100, etiqueta, TINTA, tam=56, tinta=CREMA, ang=3, pad=24)
    return s


# ---------- Escena 2: el código ----------
def escena2():
    t0, t1 = SC[1], SC[2]
    s = f'<g id="e2">{hoja(CARTON, True)}'
    s += f'<g>{caja_texto("et2", 540, 250, 560, 150, "1. El código", AMAR, tam=80, ang=-3)}{cinta(540, 175, 4)}{rebote(kicks(t0, t1)[::2])}</g>'
    lineas = [("def escucha():", "voz → texto", AZUL), ("def piensa():", "Claude decide", ROJO), ("def responde():", "texto → voz", VERDE)]
    ks = kicks(t0 + 0.3, t1 - 0.5)
    for i, (cod, nota, c) in enumerate(lineas):
        y = 600 + i * 380
        w = ancho(cod, 66, MONO) + 100
        ang = rnd.uniform(-2.5, 2.5)
        tt = ks[i * 2] if i * 2 < len(ks) else t0 + 0.4 + i
        s += f'<g opacity="0">{caja_texto(f"cod{i}", 540, y, max(w, 760), 180, cod, CREMA, tam=66, fam=MONO, ang=ang, ancla="start", pad=40)}'
        s += f'{cinta(540 - max(w,760)/2 + 30, y - 62, -20, 90, 30)}{aparece(tt)}</g>'
        s += f'<g opacity="0">{caja_texto(f"nota{i}", 640, y + 135, 440, 96, nota, c, tam=48, tinta=CREMA, ang=-ang*1.5, pad=22)}{aparece(tt + 0.3, 16)}</g>'
    s += arranque(t1) + "</g>"
    return s


# ---------- Escena 3: la hoja de Google ----------
def escena3():
    t0, t1 = SC[2], SC[3]
    s = f'<g id="e3">{hoja(KRAFT, True)}'
    s += f'<g>{caja_texto("et3", 540, 250, 560, 150, "2. La hoja", AMAR, tam=80, ang=2)}{cinta(540, 175, -5)}{rebote(kicks(t0, t1)[::2])}</g>'
    x0, y0, cw, rh = 120, 450, [330, 300, 210], 170
    tw = sum(cw)
    s += f'<g filter="url(#tiembla)"><rect id="tabla" x="{x0}" y="{y0}" width="{tw}" height="{rh*5}" fill="{CREMA}" filter="url(#recorte)" transform="rotate(-1.5 540 900)"/>'
    s += f'<rect x="{x0}" y="{y0}" width="{tw}" height="{rh}" fill="{VERDE}" transform="rotate(-1.5 540 900)"/>'
    s += "".join(f'<line x1="{x0}" y1="{y0+rh*i}" x2="{x0+tw}" y2="{y0+rh*i}" stroke="{TINTA}" stroke-width="4" transform="rotate(-1.5 540 900)"/>' for i in range(1, 5))
    xs = [x0, x0 + cw[0], x0 + cw[0] + cw[1], x0 + tw]
    s += "".join(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0+rh*5}" stroke="{TINTA}" stroke-width="4" transform="rotate(-1.5 540 900)"/>' for x in xs[1:3])
    s += "</g>"
    cab = ["Nombre", "Teléfono", "Estado"]
    filas = [("Ana", "300 •••"), ("Luis", "310 •••"), ("Marta", "315 •••"), ("Pedro", "320 •••")]
    s += f'<g transform="rotate(-1.5 540 900)">'
    for j, c in enumerate(cab):
        _, t = encajar(c, cw[j] - 40, rh - 40, tam=50)
        s += f'<rect id="cab{j}" x="{xs[j]}" y="{y0}" width="{cw[j]}" height="{rh}" fill="none"/>'
        s += f'<text data-dentro="cab{j}" data-pad="10" x="{xs[j]+cw[j]/2}" y="{y0+rh/2+t*0.35}" font-family="{SANS}" font-weight="bold" font-size="{t}" fill="{CREMA}" text-anchor="middle">{c}</text>'
    ks = kicks(t0 + 0.2, t1 - 0.4)
    for i, (n, tel) in enumerate(filas):
        yy = y0 + rh * (i + 1)
        for j, v in enumerate((n, tel)):
            _, t = encajar(v, cw[j] - 40, rh - 40, tam=54)
            s += f'<rect id="c{i}{j}" x="{xs[j]}" y="{yy}" width="{cw[j]}" height="{rh}" fill="none"/>'
            s += f'<text data-dentro="c{i}{j}" data-pad="10" x="{xs[j]+cw[j]/2}" y="{yy+rh/2+t*0.35}" font-family="{SANS}" font-weight="bold" font-size="{t}" fill="{TINTA}" text-anchor="middle">{v}</text>'
        cx, cy = xs[2] + cw[2] / 2, yy + rh / 2
        # marca roja 'pendiente' que se vuelve chulo verde
        tt = ks[i + 2] if i + 2 < len(ks) else t0 + 1.5 + i * 0.6
        s += f'<g><circle cx="{cx}" cy="{cy}" r="42" fill="none" stroke="{ROJO}" stroke-width="10"/><set attributeName="opacity" to="0" begin="{tt:.3f}s" fill="freeze"/></g>'
        s += (f'<g opacity="0"><path d="M{cx-40},{cy} L{cx-10},{cy+32} L{cx+44},{cy-36}" fill="none" stroke="{VERDE}" stroke-width="18" '
              f'stroke-linecap="round" stroke-linejoin="round"/>{aparece(tt, 20)}</g>')
    s += "</g>"
    s += f'<g opacity="0">{caja_texto("postit3", 540, 1560, 640, 200, "clientes por llamar", AMAR, tam=66, ang=-3)}{aparece(t0 + 0.9)}</g>'
    s += arranque(t1) + "</g>"
    return s


# ---------- Escena 4: la primera llamada ----------
def escena4():
    t0, t1 = SC[3], SC[4]
    s = f'<g id="e4">{hoja(CARTON, True)}'
    s += f'<g>{caja_texto("et4", 540, 250, 760, 150, "3. Primera llamada", AMAR, tam=80, ang=-2)}{cinta(540, 175, 6)}</g>'
    s += reloj(820, 560, "5:00 pm", t0, r=120)
    # teléfono de cartón que vibra con cada bombo
    ks = kicks(t0, t0 + 2.4)
    vib = "".join(f'<animateTransform attributeName="transform" type="rotate" additive="sum" values="-6 0 0;6 0 0;-4 0 0;0 0 0" dur="0.25s" begin="{k:.3f}s" calcMode="discrete" fill="remove"/>' for k in ks)
    s += (f'<g transform="translate(330,830)"><g filter="url(#tiembla)">'
          f'<rect x="-150" y="-260" width="300" height="520" rx="40" fill="{AZUL}" filter="url(#recorte)"/>'
          f'<rect x="-115" y="-205" width="230" height="350" rx="12" fill="{CREMA}"/>'
          f'<circle cx="0" cy="205" r="26" fill="{CREMA}"/>'
          + "".join(f'<path d="M{150+i*34},{-90-i*24} q{30+i*10},{90+i*24} 0,{180+i*48}" fill="none" stroke="{AMAR}" stroke-width="12" stroke-linecap="round"/>' for i in range(3))
          + f'</g>{vib}</g>')
    # burbujas de diálogo
    s += f'<g opacity="0">{caja_texto("bur1", 690, 1080, 520, 150, "¿Aló?", CREMA, tam=78, ang=3)}{aparece(t0 + 1.4)}</g>'
    s += f'<g opacity="0">{caja_texto("bur2", 500, 1400, 820, 270, "Hola, soy Sofía, de 3GO Video", VERDE, tam=70, tinta=CREMA, ang=-2)}{aparece(t0 + 2.6)}</g>'
    s += arranque(t1) + "</g>"
    return s


# ---------- Escena 5: cierre ----------
def escena5():
    t0 = SC[4]
    s = f'<g id="e5">{hoja(KRAFT, True)}'
    ks = kicks(t0, DUR)
    letras = list("3GO")
    for i, l in enumerate(letras):
        c = [ROJO, AZUL, VERDE][i]
        tt = ks[i] if i < len(ks) else t0 + 0.3 * i
        s += f'<g opacity="0" filter="url(#tiembla)">{caja_texto(f"le{i}", 300 + i*240, 520, 220, 260, l, c, tam=190, tinta=CREMA, ang=[-6, 4, -3][i], pad=20)}{aparece(tt, 50)}</g>'
    tt = ks[3] if len(ks) > 3 else t0 + 1.2
    s += f'<g opacity="0">{caja_texto("vision", 540, 820, 640, 170, "VISION", TINTA, tam=120, tinta=CREMA, ang=2)}{aparece(tt, 30)}</g>'
    tt = ks[5] if len(ks) > 5 else t0 + 2.0
    s += (f'<g opacity="0">{caja_texto("cta", 540, 1210, 860, 330, "¿La quieres en tu empresa?", AMAR, tam=86, ang=-3)}'
          f'{cinta(160, 1060, -25)}{cinta(920, 1060, 22)}{aparece(tt)}{rebote(ks[7::2], 10)}</g>')
    s += f'<g opacity="0">{caja_texto("web", 540, 1560, 560, 110, "3govideo.com", CREMA, tam=60, ang=1, pad=26)}{aparece(tt + 0.8, 16)}</g>'
    s += "</g>"
    return s


svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{DEFS}'
       + escena5() + escena4() + escena3() + escena2() + escena1()
       + f'<rect width="{W}" height="{H}" filter="url(#grano)" style="mix-blend-mode:multiply" pointer-events="none"/></svg>')
open("escena.svg", "w", encoding="utf-8").write(svg)
print("escena.svg", len(svg) // 1024, "KB; escenas en", SC)
