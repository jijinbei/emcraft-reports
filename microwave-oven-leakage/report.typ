#import "../template/report.typ": report, check

#show: report.with(
  lang: "en",
  title: "Microwave Leakage Through a Microwave Oven's Door",
  subtitle: "Power density 5 cm in front of the door at 2.45 GHz against the 5 mW/cm² limit",
  authors: ("EMCraft contributors",),
  date: "2026",
  abstract: [
    We compute the 2.45 GHz field that leaks through the door gap of a household microwave oven (1000 W into the cavity)
    with a 3D electromagnetic model of the whole oven — control panel, door window, glass turntable and a water load —
    of 2.0 to 2.3 million unknowns, solved with EMCraft v0.1, and compare the power density 5 cm in front of the door with the 5 mW/cm² limit.
    Three doors are compared: a plain 2 mm gap, the textbook quarter-wave ring groove, and the slotted folded choke used in real ovens.
    The plain gap leaks up to 69 mW/cm² and the ring groove 142 mW/cm², both far above the limit; the slotted choke brings it down to 0.008 mW/cm².
    A two-port model of the gap and a transmission-line model show why the groove fails and what the slots do.
    This is a simulation study of a design, not a certification test of a product.
  ],
)

= Problem and limits

A household microwave oven confines the output of its magnetron (about 1000 W at 2.45 GHz, an ISM band)
in a metal box to heat food. The box's only opening is the door: it has a window of perforated metal to see through,
and there is a gap between the door and the body. Both limits are set on the leaking power density 5 cm from the outer surface.

- IEC 60335-2-25 (clause 32): at most 50 W/m² (= 5 mW/cm²) at 5 cm from the outer surface.
- US 21 CFR 1030.10(c)(1): at 5 cm, 1 mW/cm² when shipped and 5 mW/cm² thereafter.

We take 5 mW/cm² as the limit and also show the margin to the 1 mW/cm² shipping limit.

= Closed-form estimates

Before the numerical model, we estimate how each part behaves in closed form; the analysis is checked against these (@sec-verify).

== Cavity resonances

The resonant frequencies of the cavity (a rectangular box of width $a$, height $b$ and depth $d$ with metal walls) are
$ f_(m n p) = c/2 sqrt((m/a)^2 + (n/b)^2 + (p/d)^2) $ <eq-cavity>
(Pozar, _Microwave Engineering_, 4th ed., §6.7).
The cavity is several wavelengths (12.2 cm) across, so many modes lie near 2.45 GHz and
the field inside varies strongly from place to place. This is why a turntable or a stirrer is used to even out the heating.

== Holes in the screen: waveguides below cutoff

A round hole of diameter $D$ in a plate of thickness $t$ is a short circular waveguide.
The cutoff wavelength of its lowest mode, TE#sub[11], is $lambda_c = 1.706 D$ (Pozar §3.4);
for $lambda >> lambda_c$ a wave through the hole is attenuated by
$ A = 8.686 dot (2 pi) / lambda_c sqrt(1 - (lambda_c / lambda)^2) dot t
  approx 32.0 dot t / D quad "dB" $ <eq-cutoff>
For a square hole of side $w$ (TE#sub[10], $lambda_c = 2 w$), $A approx 27.3 dot t / w$ dB.
For $D = 2$ mm and $t = 0.6$ mm, $A approx 9.6$ dB. This is the attenuation inside the hole only; the coupling into and out of
the hole (Bethe's small-hole theory, Bethe 1944) adds to it.

== Door gap and choke

The gap between the door and the body is a parallel-plate line. A groove (a choke) a quarter wavelength deep
(about 30 mm at 2.45 GHz) placed in the gap turns the short at its bottom into an open at its mouth, putting a high impedance in series
along the gap. The current along the gap is suppressed, and so is the leak. The effect depends on frequency and weakens as the depth departs from $lambda\/4$.

= Model

== The whole oven

The oven is built as a real countertop oven (SolidCraft scripts: `model/make.py` writes `oven-gap`, `oven-choke` and `oven-slotted`).
The cavity is on the left and the control compartment on the right; the magnetron's power reaches the cavity's right wall through a waveguide inside the control compartment.
All dimensions are design parameters, listed below.

#table(columns: 3, align: (left, right, left),
  [*Symbol*], [*Value*], [*Meaning*],
  [$a times d times h$], [330 × 330 × 210 mm], [cavity (width, depth, height); the door at $y = 0$],
  [$w$], [45 mm], [wall thickness, also the width of the flange the door rests on],
  [$g$], [2 mm], [gap between door and flange; the same between the door's right edge and the control panel],
  [$t$], [40 mm], [door thickness],
  [$c_w$], [130 mm], [width of the control compartment (right of the cavity)],
  [$g_b times g_n$], [86 × 43 mm], [waveguide cross-section (TE#sub[10] cutoff 1.74 GHz), shorted at its bottom, opening into the cavity's right wall through an 86 × 60 mm aperture at its top],
  [$t_r$, $t_t$], [140 mm, 6 mm], [radius and thickness of the glass turntable (12 mm above the floor)],
  [$b_r$, $l_h$], [42.5 mm, 48.5 mm], [radius and depth of the water load (275 ml)],
  [$w_w times w_h$], [220 × 150 mm], [door window (a 12 mm deep recess whose bottom is the perforated screen)],
  [$c_s times c_d$, $c_l$], [6 × 30 mm, 30 mm], [ring groove's width and depth, and its distance from the cavity's edge (`oven-choke`)],
  [$f_s$, $f_l$], [8.5 mm, 36 mm], [start and end of the slotted choke's lip (`oven-slotted`)],
)

- The body (`shell`) and the door (`door`) are perfect conductors. The window's perforated screen is a metal plate without holes (leakage through the holes is not covered in this version; @eq-cutoff).
- The magnetron's antenna is a lumped port (`feed`) reaching 18 mm into the guide from its outer broad wall, a quarter of a guide wavelength (174 mm) from the shorted end.
- The load is the 275 ml of water of the IEC 60335-2-25 leakage test, in a beaker 85 mm across at the middle of the turntable.
  The water follows a Debye model at 25 °C ($epsilon_s = 78.36$, $epsilon_oo = 5.2$, $tau = 8.27$ ps; Kaatze 1989): $epsilon_r = 77.2 - j 9.2$ at 2.45 GHz.
  The turntable is borosilicate glass ($epsilon_r = 4.6$, $tan delta = 0.005$; von Hippel 1954).
  The beaker's thin glass (2 mm) is left out and the water sits that much above the plate (EMCraft cannot yet mesh a dielectric inside, or touching, another dielectric).
- An air box surrounds the oven and a 31 mm thick PML ($lambda\/4$ at 2.45 GHz) absorbs at its outside. It reaches 120 mm in front of the door, where the leak is measured, and 45–60 mm elsewhere (the cabinet is metal, so the leak can only come from round the door).
- The feed on the right and the control compartment on one side leave the oven without a symmetry plane: the whole oven is solved.

#figure(image("results/model.png", width: 100%), caption: [The 3D model of the oven solved (slotted choke, drawn by SolidCraft). (a) Outside: the door (with its window) on the left, the control panel on the right. (b) Inside, the body and the door see-through: the slots round the door's rim, the turntable (light blue) and the water (blue), the waveguide running up the control compartment. (c) A horizontal section at the feed's height, seen from above: the waveguide opens into the cavity's right wall.]) <fig-model>

== The chokes

The gap between the door and the body runs from the cavity's edge across the 45 mm flange to the outside. The three doors differ only in the door's inner face, the side facing this gap.
@fig-doors-cad shows where each choke is in the CAD models and @fig-choke draws their cross-sections.

- *No choke* (`oven-gap`): the door's inner face is flat; the 2 mm gap runs straight to the outside.
- *Ring groove* (`oven-choke`): a groove 6 mm wide and 30 mm ($lambda\/4$) deep runs all round the door's inner face, 30 mm from the cavity's edge: the textbook choke.
- *Slotted choke* (`oven-slotted`): a folded choke (Osepchuk et al., US 3,767,884). The door's rim facing the gap is a 1 mm plate (the lip) with a 4 mm deep channel behind it.
  The channel opens into the gap at its outer end (its mouth) and is closed at the cavity end. 58 slots 2.5 mm wide, every 18 mm, cut the lip into teeth.

#figure(image("results/doors-cad.png", width: 100%), caption: [The three doors in the CAD models (SolidCraft). Top: the door seen from the cavity (the body cut away just behind it; the hatched block on the left is the control panel's cut). The ring groove runs all round the rim; the slots line the rim. Bottom: the door's lower rim cut at the middle ($x = a\/2$), the outside on the left, the cavity on the right; brown hatching is the door's cut, blue the body's.]) <fig-doors-cad>

#figure(image("results/choke.svg", width: 100%), caption: [The gap round the three doors, cut across the lower rim (where: the red line in @fig-lip (b)); the outside on the left, the cavity on the right. Grey is metal, light blue air, the red dashes the leak's path (cavity → 2 mm gap → outside). The groove (b) is 6 mm wide and 30 mm ($lambda\/4$) deep, open to the gap. The lip (c) is 1 mm thick; the channel behind it, 4 mm deep, opens into the gap at its lower end.]) <fig-choke>

#figure(image("results/lip.svg", width: 90%), caption: [(a) The slotted choke's lip seen from the cavity. The dark parts open into the channel behind; the slots are 2.5 mm wide, every 18 mm, cutting the lip into teeth. (b) The oven from the front; the red line is where @fig-choke cuts.]) <fig-lip>

== Solving

The models are solved with EMCraft v0.1. Second-order Nédélec elements on a mesh of 4 elements per wavelength give 1.99 million unknowns without a choke,
2.04 million with the ring groove and 2.31 million with the slotted choke.
They are solved with EMCraft's direct solver (multifrontal LDL#super[T]). The largest fronts are never formed whole: they are assembled and factored panel by panel,
and the factor's large blocks are kept as low-rank tiles to a tolerance of $10^(-8)$ (block low-rank approximation; Amestoy et al., SIAM J. Sci. Comput. 37(3), 2015).
Iterative refinement recovers the accuracy given up, to a backward error of $10^(-16)$ or less. Each model fits a 30 GB machine (peak 20–26 GB) and takes about 25 minutes.

= Analysis

== The gap as a two-port

A piece of the door's rim is cut out and solved as a two-port through the 2 mm gap, from the cavity side (port 1) to the outside (port 2) (`scripts/cell.py`).
Conducting walls close it on both sides across a width $b$ along the rim, so the wave in the gap varies along the rim as $sin(pi y\/b)$.
$b = 300$ mm is a nearly uniform field, $b = 80$ mm one that varies strongly along the rim.
In the real oven the field inside rises and falls many times along the rim (@fig-plane-A, @fig-plane-B inside the cavity).

Seen as a shorted stub in series with the gap's line, the plain groove gives
$ S_21 = (2 Z_0) / (2 Z_0 + j Z_g tan beta d), quad beta^2 = k^2 - (pi\/b)^2 $ <eq-stub>
($Z_g\/Z_0$ is the ratio of the groove's width to the gap, 3; $d$ is the groove's depth; Pozar §2.3, §4.3).
A field that varies along the rim makes $beta$ smaller, and the frequency at which the groove acts as $lambda\/4$ rises.

#table(columns: 4, align: (left, right, right, right),
  [*Structure*], [*$b$*], [*$|S_21|$ at 2.45 GHz*], [*Dip*],
  [plain groove], [300 mm], [−22.5 dB (formula −27.6 dB)], [2.65 GHz],
  [plain groove], [80 mm], [−7.7 dB (formula −8.0 dB)], [3.20 GHz],
  [folded, no slots], [80 mm], [−5.2 dB], [3.20 GHz],
  [slotted ($f_s = 10$ mm)], [300 / 80 mm], [−22.5 / −24.3 dB], [2.55 / 2.55 GHz],
  [slotted ($f_s = 8.5$ mm)], [300 / 80 mm], [−73.2 / −40.1 dB], [2.45 / 2.45 GHz],
)

The plain groove hardly works at 2.45 GHz on a wave that varies strongly along the rim ($b = 80$ mm): its dip moves to 3.2 GHz.
The slots cut the lip into teeth, which stop the current along the rim, and give both waves a dip at the same frequency.
This agrees with the patent's explanation (the slots stop the modes that travel along the rim).

= Results

The power density $1\/2 "Re"(E times H^*)$ 5 cm in front of the door (50 mm from its outer face, on 17 × 15 points every 30 mm × 20 mm covering the door and the control panel)
is scaled to 1000 W accepted by the oven (the feed's incident power less the reflected).

#table(columns: 4, align: (left, right, right, right),
  [*Door*], [*Maximum (mW/cm²)*], [*Mean (mW/cm²)*], [*Against 5 mW/cm²*],
  [no choke (`oven-gap`)], [69.1], [13.7], [14 ×],
  [ring groove (`oven-choke`)], [141.5], [23.6], [28 ×],
  [slotted choke (`oven-slotted`)], [0.0079], [0.0011], [1/630],
)

The fields are shown on the four planes of @fig-planes. The colour is $|E|$ for 1000 W on a log scale; "limit" on the colour bar is
the $|E|$ of a plane wave of 5 mW/cm² (194 V/m). Near the door the field is not a plane wave, so the mark is a guide; the verdict is the power density in the table above.

#figure(image("results/planes.svg", width: 100%), caption: [Where the field pictures' planes lie. A: a vertical section through the middle of the cavity ($x = a\/2$); B: a horizontal section at the feed's height; C: 2 mm in front of the door's outer face; D: 5 cm in front of it (the limit's plane).]) <fig-planes>

#figure(image("results/plane-B.png", width: 100%), caption: [$|E|$ on plane B (horizontal, at the feed, seen from above; the door at the bottom, metal grey). Without a choke and with the ring groove the field is strong all along the front of the door, strongest in front of the seam between the door and the control panel ($x approx 480$ mm). With the slotted choke the outside is at a few V/m.]) <fig-plane-B>

#figure(image("results/plane-D.png", width: 100%), caption: [$|E|$ on plane D (5 cm in front of the door, seen from the front). The black frames are the door, its window and the control panel.]) <fig-plane-D>

#figure(image("results/plane-C.png", width: 100%), caption: [$|E|$ on plane C (2 mm in front of the door's outer face).]) <fig-plane-C>

#figure(image("results/plane-A.png", width: 100%), caption: [$|E|$ on plane A (the vertical section through the middle of the cavity, seen from the side; the door on the left). The field leaves through the gap between the door and the body at the door's upper and lower edges. With the ring groove it is strong inside the groove too.]) <fig-plane-A>

The leak comes not through the door's face (the window) but through the gap round its edges. Without a choke it is strongest in front of the seam between the door and the control panel (@fig-plane-B, @fig-plane-D).
The ring groove doubles the leak: it resonates along the rim and strengthens the field in the gap instead (inside the groove in @fig-plane-A).
The slotted choke lowers the maximum to about 1/8800 of the plain gap's (−39 dB): about 600 times below the 5 mW/cm² limit and more than 100 times below the 1 mW/cm² shipping limit.

The previous version's half model, without a control panel, gave a maximum of 1.8 mW/cm² without a choke.
The whole oven adds the leak through the seam beside the panel and is close to 40 times higher.

= Verification <sec-verify>

#check([plain groove's $|S_21|$ (2.45 GHz, $b = 80$ mm)], [−7.7 dB], [−8.0 dB (@eq-stub)], [1 dB], [the series-stub transmission-line model. Pozar, _Microwave Engineering_, §2.3, §4.3])

#check([plain groove's $|S_21|$ (2.45 GHz, $b = 300$ mm)], [−22.5 dB], [−27.6 dB (@eq-stub)], [near the dip, shifted by the junction's parasitic reactance], [as above; the dips are at 2.65 GHz and 2.55 GHz])

#check([compressed factor], [S-parameters solved with the factor compressed to $10^(-6)$ (coarser than this report's $10^(-8)$) and iterative refinement (the high-pass filter sample)], [the same with the factor uncompressed], [$10^(-9)$], [EMCraft's test `a_compressed_factor_gives_the_exact_ones_s_parameters`])

#check([the whole oven's solutions], [backward errors $3.9 times 10^(-18)$, $3.8 times 10^(-16)$, $1.8 times 10^(-17)$], [0 (the exact solution)], [$10^(-12)$], [EMCraft's solve report (`backward_error`)])

The mesh was checked on the previous version's half model by solving it with 4 and 5 elements per wavelength (second order, `results/half-model/`).
The means agree within 10 % for every door; the maxima, single points, move by up to 30 %. The whole oven here is solved with 4 elements per wavelength.
The differences between the three doors (a factor of 2 to four orders of magnitude) are larger than this spread.

#table(columns: 5, align: (left, right, right, right, right),
  [*Door (half model)*], [*Max, 4 per λ*], [*Max, 5 per λ*], [*Mean, 4 per λ*], [*Mean, 5 per λ*],
  [no choke], [1.51], [1.77], [0.386], [0.386],
  [ring groove], [34.2], [33.9], [4.76], [4.69],
  [slotted choke], [0.0027], [0.0021], [0.00042], [0.00038],
)

= Conclusions

- A door over a plain 2 mm gap leaks up to 69 mW/cm² at 5 cm, 14 times the 5 mW/cm² limit. The leak comes from the door's edges, above all the seam beside the control panel.
- A textbook $lambda\/4$ groove round the door makes the leak worse (up to 142 mW/cm²): the field in the gap varies along the rim, so the groove does not act as $lambda\/4$, and the groove resonates along the rim.
- Folding the groove and slotting its lip (the structure of real ovens) brings the leak down to 0.008 mW/cm², about 600 times below the limit.
- Leakage through the door's perforated screen is not covered: this version treats the window as a metal plate.

This is a simulation study of a design, not a certification test of a product.
