#import "../template/report.typ": report, check

#let video(name, label) = link("https://github.com/jijinbei/emcraft-reports/blob/main/relativistic-bwo/results/" + name + ".mp4", text(fill: rgb("#2b5bc8"))[#label])

#show: report.with(
  lang: "en",
  title: "Particle Simulation of Relativistic Backward-Wave Oscillators",
  subtitle: "A published Ku-band tube reproduced, and an S-band tube designed from rules of thumb",
  authors: ("EMCraft contributors",),
  date: "2026",
  abstract: [
    A backward-wave oscillator (BWO) turns a relativistic electron beam into gigawatt microwaves.
    We solve two of them with EMCraft's axisymmetric particle-in-cell simulation.
    A published Ku-band BWO (Na et al., 2017) oscillates in a single mode at 15.32 GHz (15.575 GHz published).
    An S-band BWO whose authors gave only rules of thumb for its dimensions (Molchanov and Gurnevich, 2024) is designed from those rules:
    3.40 GHz, 0.64 GW and 17.0 % efficiency (about 3.6 GHz, 1 GW and 27–28 % published).
  ],
)

= Aims

- Check that EMCraft's particle simulation reproduces a published BWO (Ku band).
- Design an S-band BWO with EMCraft from rules of thumb alone.

The runs used EMCraft's develop branch (the final runs d8e4fa3c on the CPU, the dimension scans e72b4edd on a GPU, CUDA in double precision); the scripts are in `scripts/`.

= How a BWO works <sec-principle>

#figure(image("results/principle.svg", width: 100%), caption: [How a BWO works. (a) The electron beam runs right through a rippled wall (the slow-wave structure) while the wave's energy flows left, towards the cathode (a backward wave); the cut-off neck at the cathode end reflects it to the output. (b) The wave's $E_z$ slows and speeds the electrons; downstream they bunch in the slowing phase and give their energy to the wave. (c) The wave, grown downstream, returns to the cathode end and modulates the incoming beam: a loop inside the tube, so it oscillates with no external feedback.]) <fig-principle>

- A periodic ripple gives the wave components slower than light (space harmonics). An electron moving at such a component's phase velocity (in synchronism) keeps meeting the same phase of the field (@fig-principle (b)).
- The synchronous harmonic carries its energy against the beam (a backward wave), so amplification and the beam's modulation close one loop ((c)).
- The frequency is where the dispersion curve meets the beam's speed line (@fig-dispersion). The tube oscillates once the current passes Johnson's start condition $C N = 0.314$.
- A kiloampere beam slows under its own charge and lowers the crossing (the frequency). Electrons that give up too much energy fall out of synchronism and may turn back; this sets the efficiency's limit.

= Method

#figure(image("results/bwo-3d.png", width: 100%), caption: [The two BWOs in 3D (SolidCraft designs, cut in half): grey the metal tube, orange the electron beam. Both are bodies of revolution about their axis.]) <fig-3d>

Each tube is designed in SolidCraft as a body of revolution (`model/`), and EMCraft imports the design.
Solved in 3D, even the Ku-band tube takes some 27 million cells (270 times the r–z grid) and about 40 hours a run: too slow to design with.
The tube and the beam are the same all round the axis (@fig-3d), so the fields and the electrons are taken to be too, and the problem is solved on the half plane through the axis (the r–z plane).

- Only the r–z plane is solved, as a body of revolution (`solve.particles`, `axisymmetric`). The wall is a staircase of cells, which puts the frequency slightly low.
- The beam enters at the cathode end with a given current and voltage. The guiding field falls away past the structure (`particles.magnetic`, `end`), so the beam lands on the wall (a collector).
- The output power is the Poynting flux through a plane past the collector, averaged in time (`particles.output`); the efficiency is that power over the beam's.

= The Ku-band BWO: a published tube reproduced <sec-ku>

The structure and the beam of Na et al. (J. Comput. Phys. 346:295, 2017; arXiv:1701.03784 §5.1) are built as published (@fig-ku-section).
Cells of 0.5 mm (four times finer along the axis), 100 ns solved (about 8.5 minutes).

#figure(image("results/ku-section.png", width: 100%), caption: [The Ku-band BWO's section (half the r–z plane; grey metal, yellow the beam). The wall's ripple $R = 15 + 2.1 cos(2 pi z\/7.5)$ mm over 14.5 periods. The beam 550 kV, 1.5 kA, 5 T. The field weakens at z = 140 mm (red); the output is measured beyond (blue).]) <fig-ku-section>

#figure(grid(columns: 3, gutter: 6pt,
  image("results/final-ku-power.png"), image("results/final-ku-spectrum.png"), image("results/final-ku-phase.png")),
  caption: [The Ku band. Left: the output power (steady from about 50 ns). Middle: the spectrum (one peak, 15.32 GHz). Right: the electrons' z and kinetic energy (bunching, @fig-principle (b)).]) <fig-ku-results>

#figure(image("results/ku-evolution.png", width: 100%), caption: [The Ku band as it grows: $E_z$ (blue negative, red positive, one colour scale for all moments) with the electrons over it (black dots). The wave standing on the structure grows, the beam bunches as it goes, and the collector turns it to the wall. Videos: #video("ku-growth", [growth, 0–100 ns]) · #video("ku-rf", [steady RF, about 9 periods]).]) <fig-ku-evolution>

#table(columns: 3, align: (left, right, right),
  [*Quantity*], [*EMCraft (0.5 mm)*], [*Na et al.*],
  [Frequency], [15.32 GHz], [15.575 GHz],
  [Time to steady state], [about 50 ns], [about 35 ns],
  [Output, efficiency], [70 MW, 8.5 %], [not given],
)

The frequency is 1.6 % low because of the wall's staircase. In EMCraft's earlier verification, finer cells extrapolated to 15.46–15.66 GHz, which brackets the paper's.

= The S-band BWO: a design

== From rules of thumb to dimensions

Molchanov and Gurnevich (Nonlinear Phenomena in Complex Systems 27(2):123, 2024) report about 1 GW at 27–28 % from 550 keV, 80 Ω (about 6.9 kA) and 1.3 T or more,
but give the dimensions only as rules: a period $approx 0.37 lambda_g$, a mean radius $approx 0.29 lambda_g$ and a depth $approx lambda_g \/ 12$.
With $lambda_g = 127$ mm, where the three agree at 3.6 GHz, the start is a 47 mm period, a 36.9 mm mean radius and a 10.6 mm depth (a sinusoidal ripple).

#figure(image("results/sband-dispersion.png", width: 70%), caption: [The S-band slow-wave structure's dispersion (the final 44 mm period; blue, EMCraft) and the beam's speed lines. Their crossings estimate the frequency: 3.78 GHz at 550 keV, 3.67 GHz for a beam slowed to 0.8c.]) <fig-dispersion>

== What mattered

With the rules' dimensions the beam slows under its space charge and the efficiency is 2 %. Three things mattered:
- Bring the beam close to the wall (radius 25 → 29.5 mm): it slows less and couples more strongly. With the period shortened to 44 mm, 19 %.
- Measure the output past a collector: the beam's bunches no longer cross the output plane, and the same structure gives 15 %.
- Make the last two periods shallower, the depth changing smoothly from the middle of one period to the next: fewer slowed electrons turn back (0.41 kA), 17.0 %.

Around the final design the dimensions were scanned finely on a GPU (each point one 60 ns run, about a minute; @fig-maps).
- The tube oscillates only in a narrow window of periods, 43–45 mm; at 42 mm and below it falls out of synchronism and nearly stops.
- The closer the beam to the wall the better: each millimetre further in from 30.5 mm roughly halves the efficiency.
- The output end's depth matters little: ±1 mm keeps 16–18 %.

#figure(image("results/sband-maps.png", width: 100%), caption: [The efficiency (%) around the final design. (a) The period against the beam's outer radius (2 mm thick). (b) The inner radii of the last two periods. The red frame is the final design.]) <fig-maps>

#figure(image("results/sband-section.png", width: 100%), caption: [The final S-band design: a cut-off neck, a 30 mm insert, five ripple periods of 44 mm (the last two made shallower smoothly) and an output horn. The beam 550 kV, 6.9 kA, radius 28.5–30.5 mm, 2.5 T.]) <fig-sband-section>

== Results

#figure(grid(columns: 3, gutter: 6pt,
  image("results/final-sband-power.png"), image("results/final-sband-spectrum.png"), image("results/final-sband-phase.png")),
  caption: [The final S-band design. Left: the output power (steady from about 35 ns, about 0.65 GW). Middle: the spectrum (3.40 GHz). Right: the electrons' z and kinetic energy.]) <fig-sband-results>

#figure(image("results/sband-evolution.png", width: 100%), caption: [The S band as it grows (drawn as @fig-ku-evolution). Videos: #video("sband-growth", [growth, 0–60 ns]) · #video("sband-rf", [steady RF]).]) <fig-sband-evolution>

#table(columns: 3, align: (left, right, right),
  [*Quantity*], [*EMCraft's design*], [*Molchanov and Gurnevich*],
  [Frequency], [3.40 GHz], [about 3.6 GHz],
  [Output], [0.64 GW], [about 1 GW],
  [Efficiency], [17.0 %], [27–28 %],
)

The frequency is lower because the beam slows to about 0.7c under its space charge and the interaction, which lowers the crossing (@fig-dispersion).
The efficiency falls short, we think, because the paper's optimized end corrugations (their reflections) and its insert are not published and are not reproduced here.

= Summary

- EMCraft's axisymmetric particle simulation reproduces the published Ku-band BWO in a single mode at 15.32 GHz (−1.6 %, the wall's staircase).
- The S-band BWO, designed from rules of thumb, gives 3.40 GHz, 0.64 GW and 17.0 % efficiency. Bringing the beam close to the wall mattered most.
- The output must be measured with the beam stopped before the output plane (a collector); without one the efficiency reads a few points high.

This is a simulation study, not a measurement of a real device.
