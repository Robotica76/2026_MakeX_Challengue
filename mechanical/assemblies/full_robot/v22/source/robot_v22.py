"""MakeX Challenge 2026 - Storm Breaker v22 (marco ROBOT, mm).

v22 = v21 + MASTIL DE BANDERA desmontable (se instala en el Modification Stage; antes queda SEPARADO del robot).
  * En el robot (permanente, cuenta desde la inspeccion): RECEPTOR impreso sobre el bloque de montaje de la pinza (sube y baja con
    el carro del elevador, 358 mm de carrera) + agujero guia D10 en la tapa superior del mastil del elevador (MAS_tapa, z 609..612).
  * Pieza aparte (Modification Stage, 60 s): MASTIL de tubo de CF 8x6 que entra en el receptor (pasador R) y pasa por la guia, con la
    CABEZA en "C" del dibujo del equipo arriba: el tubo sube, dobla hacia la derecha (+x, hacia afuera) en el brazo superior; un lomo
    interior y un brazo inferior forman la bolsa. El palo de la bandera (<10x10 mm, regla T17) va en la bolsa y una LIGA cruzada entre
    las puntas de los brazos (ranuras) lo aprieta contra el lomo: no se cae con golpes ni tirones.
  * Para colgarla: subir el carro, meter la barra del campo dentro del lazo de la bandera, bajar el carro (el lazo queda en la barra)
    y desplazarse de lado hacia -x (mecanum): el palo sale de la C estirando la liga y la bandera queda colgada sin tocar el robot.
El mastil va en y=-64 (borde delantero del bloque de la pinza) para no pasar por la camara IA que esta sobre la tapa del elevador.
Altura con el mastil: hasta ~1065 mm con el carro arriba (despues del Modification Stage la altura es libre, T01; la huella sigue 500x500).
"""
import cadquery as cq
import robot_v21 as r21
from robot_v21 import box, r19, r20

MX, MY = 181.5, -64.0            # eje del mastil: en el borde delantero del bloque de la pinza (libra la camara IA, y<=-71, por 3 mm)
TUBE_D, TUBE_DI = 8.0, 6.0
SOCK_Z0 = 157.0                  # cara superior del bloque de montaje con el carro abajo (zc = 28)
SOCK_H = 22.0
MAST_TOP = 700.0                 # punta del mastil con el carro abajo (la cabeza queda arriba de la tapa del elevador, z 612)
HEAD_W = 30.0                    # ancho de la cabeza a lo largo de y (eje del palo de la bandera)
POCKET = (5.0, 40.0)             # bolsa: +6 mm de punta = 11 mm del lomo a la liga (palo de 8-10 mm queda apretado) y 40 de alto
ARM_T = 4.0
LIFT0 = r19.elv.CAR_Z_RANGE[0]


def cyl_z(d, z0, z1, x, y):
    return cq.Workplane("XY", origin=(0, 0, z0)).center(x, y).circle(d / 2).extrude(z1 - z0)


def receptor(dz=0.0):
    s = box(MX - 6.5, MX + 6.5, MY - 7.0, MY + 7.0, SOCK_Z0, SOCK_Z0 + SOCK_H)
    s = s.cut(cyl_z(8.3, SOCK_Z0 + 3.0, SOCK_Z0 + SOCK_H + 1, MX, MY))
    s = s.cut(cq.Workplane("YZ", origin=(MX - 8, 0, 0)).center(MY, SOCK_Z0 + 14.0).circle(1.6).extrude(20.0))    # pasador R D3
    return s.translate((0, 0, dz))


def head_profile_xz():
    """Perfil de la cabeza en x-z (forma del dibujo): tubo -> curva -> brazo superior; lomo interior; brazo inferior."""
    zt = MAST_TOP
    zb = zt - POCKET[1] - 2 * ARM_T            # base del brazo inferior
    x_sp0 = MX + 4.0                           # lomo interior (a la derecha del tubo, como en el dibujo)
    x_sp1 = x_sp0 + ARM_T
    x_tip = x_sp1 + POCKET[0] + 6.0            # puntas de los brazos
    top = (cq.Workplane("XZ").moveTo(MX - TUBE_D / 2 - 1.0, zt - 18.0).lineTo(MX - TUBE_D / 2 - 1.0, zt - 4.0)
           .threePointArc((MX + 1.0, zt + 3.0), (MX + 9.0, zt + ARM_T + 0.5)).lineTo(x_tip, zt + ARM_T).lineTo(x_tip, zt)
           .lineTo(x_sp1, zt).lineTo(x_sp1, zt - 2.0).lineTo(MX + TUBE_D / 2 + 1.0, zt - 18.0).close())
    return top, (x_sp0, x_sp1, x_tip, zb, zt)


def head():
    top, (x_sp0, x_sp1, x_tip, zb, zt) = head_profile_xz()
    y0 = MY - HEAD_W / 2
    h = top.extrude(HEAD_W).translate((0, y0 + HEAD_W, 0))
    spine = box(x_sp0, x_sp1, y0, y0 + HEAD_W, zb, zt)
    bottom = box(x_sp0, x_tip, y0, y0 + HEAD_W, zb, zb + ARM_T)
    sleeve = box(MX - 6.0, x_sp1, y0 + 7.0, y0 + HEAD_W - 7.0, zt - 30.0, zt - 2.0)                                     # manga que abraza el tubo y une el lomo
    h = h.union(spine).union(bottom).union(sleeve)
    h = h.cut(cyl_z(8.2, zt - 31.0, zt - 3.0, MX, MY))                                                                   # alojamiento del tubo
    for zz in (zt + ARM_T / 2, zb + ARM_T / 2):                                                                          # ranuras para la liga
        h = h.cut(box(x_tip - 3.0, x_tip + 1.0, y0 - 1, y0 + HEAD_W + 1, zz - 1.2, zz + 1.2))
    for yy in (y0 + 8.0, y0 + HEAD_W - 8.0):
        h = h.cut(box(x_tip - 3.0, x_tip + 1.0, yy - 3.0, yy + 3.0, zb - 1, zt + ARM_T + 1))
    return h, (x_sp0, x_sp1, x_tip, zb, zt)


def mast_parts(dz=0.0, flag=True):
    out = []
    pin_hole = cq.Workplane("YZ", origin=(MX - 8, 0, 0)).center(MY, SOCK_Z0 + 14.0).circle(1.6).extrude(20.0)
    out.append(("FLAG_mastil_tubo_CF_8x6", cyl_z(TUBE_D, SOCK_Z0 + 3.0, MAST_TOP - 3.0, MX, MY).cut(cyl_z(TUBE_DI, SOCK_Z0, MAST_TOP, MX, MY)).cut(pin_hole), "cf"))
    out.append(("FLAG_pasador_R_D3", cq.Workplane("YZ", origin=(MX - 6.0, 0, 0)).center(MY, SOCK_Z0 + 14.0).circle(1.5).extrude(18.0), "steel"))
    h, (x_sp0, x_sp1, x_tip, zb, zt) = head()
    out.append(("FLAG_cabeza_C_PETG", h, "print"))
    y0 = MY - HEAD_W / 2
    liga = None
    for yy in (y0 + 8.0, y0 + HEAD_W - 8.0):
        l = box(x_tip - 1.0, x_tip + 0.5, yy - 2.5, yy + 2.5, zb, zt + ARM_T)
        liga = l if liga is None else liga.union(l)
    out.append(("FLAG_ligas_x2", liga, "rubber"))
    if flag:                                                                                                              # referencia: bandera (no cuenta en la masa, T02)
        pc = ((x_sp1 + x_tip) / 2 - 0.5, zb + ARM_T + 4.5)                                                       # el palo descansa en el brazo inferior
        pole = cq.Workplane("XZ").center(*pc).rect(8.0, 8.0).extrude(-300.0).translate((0, MY - 150.0, 0))
        cloth = box(pc[0] - 0.5, pc[0] + 0.5, MY - 150.0, MY + 150.0, pc[1] - 404.0, pc[1] - 4.0)
        loop = cq.Workplane("YZ", origin=(pc[0] - 0.75, 0, 0)).center(MY, pc[1]).circle(110.0).circle(108.5).extrude(1.5)
        loop = loop.intersect(box(pc[0] - 2, pc[0] + 2, MY - 120, MY + 120, pc[1] + 4.0, pc[1] + 200))
        out.append(("REF_bandera_palo_8x8_300", pole, "flagpole"))
        out.append(("REF_bandera_tela_400x300", cloth, "flag"))
        out.append(("REF_bandera_lazo", loop, "flag"))
    return [(n, s.translate((0, 0, dz)), c) for n, s, c in out]


COL = {"cf": (0.18, 0.19, 0.21, 1), "print": (0.95, 0.45, 0.10, 1), "steel": (0.7, 0.71, 0.74, 1), "rubber": (0.85, 0.15, 0.15, 1),
       "flagpole": (0.85, 0.2, 0.2, 1), "flag": (0.15, 0.45, 0.85, 0.85)}


def build(mast=False, flag=True, refs=True, screws=True, zc=LIFT0, **kw):
    """mast=False: robot como entra a la cancha (solo el receptor). mast=True: despues del Modification Stage."""
    kw.setdefault("lift", zc - LIFT0)
    asm = r21.build(refs=refs, screws=screws, zc=zc, **kw)
    asm.name = "Robot_StormBreaker_v22" + ("_con_mastil_bandera" if mast else "")
    dz = zc - LIFT0
    for c in asm.children:
        if c.name == "MAS_tapa_y_bandeja_camara_CF3":                                                                    # guia del mastil
            c.obj = (c.obj if hasattr(c.obj, "val") else cq.Workplane().add(c.obj)).cut(cyl_z(10.0, 600.0, 620.0, MX, MY))
    asm.add(receptor(dz), name="FLAG_receptor_mastil_PETG", color=cq.Color(*COL["print"]))
    if mast:
        for n, s, c in mast_parts(dz, flag=flag and refs):
            asm.add(s, name=n, color=cq.Color(*COL[c]))
    return asm


ELEC = r21.ELEC; CABLES = r21.CABLES
elv = r19.elv; ur = r19.ur; ch = r19.ch; TWCOL = r19.TWCOL
