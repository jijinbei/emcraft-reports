#import "../template/report.typ": report, check

#let video(name, label) = link("https://github.com/jijinbei/emcraft-reports/blob/main/relativistic-bwo/results/" + name + ".mp4", text(fill: rgb("#2b5bc8"))[#label])

#show: report.with(
  lang: "ja",
  title: "相対論的後進波発振器（BWO）の粒子シミュレーション",
  subtitle: "Ku 帯の公表例との照合と、S バンドの設計",
  authors: ("EMCraft contributors",),
  date: "2026",
  abstract: [
    相対論的な電子ビームで GW 級のマイクロ波をつくる後進波発振器（BWO）を、EMCraft の軸対称の粒子シミュレーションで解いた。
    Ku 帯の公表例（Na ら, 2017）は 15.32 GHz の単一モードで再現した（論文 15.575 GHz）。
    寸法の目安だけが公表された S バンドの BWO（Molchanov と Gurnevich, 2024）は、その目安から設計して 3.40 GHz、0.64 GW、効率 17.0% を得た（論文 約 3.6 GHz、約 1 GW、27〜28%）。
  ],
)

= 目的

- EMCraft の粒子シミュレーションが、公表された BWO の振る舞いを再現するかを確かめる（Ku 帯）。
- 設計の目安だけから、S バンドの BWO を EMCraft で設計する。

計算は EMCraft（v0.1.0-15-gaf6863c9、develop）で行い、スクリプトは `scripts/` にある。

= BWO の原理 <sec-principle>

#figure(image("results/principle.svg", width: 100%), caption: [BWO のしくみ。(a) 波打った壁（遅波構造）の中を電子ビームが右へ進み、波のエネルギーは左（陰極側）へ流れる（後進波）。陰極側のカットオフネックで反射して出力へ出る。(b) 波の電界 $E_z$ が電子を減速・加速し、下流では電子が減速の位相に束になって、そのエネルギーを波へ渡す。(c) 下流で強まった波が陰極側へ戻り、入ってきたビームを変調する。この内部のループで、外から帰還をかけなくても発振する。]) <fig-principle>

- 壁を周期的に波打たせると、波は光より遅い成分（空間高調波）をもつ。電子の速さがその位相速度とそろう（同期する）と、電子は同じ位相の電界を受け続ける（@fig-principle (b)）。
- 同期する高調波はエネルギーの流れがビームと逆向き（後進波）なので、増幅とビームの変調が一つのループになる（(c)）。
- 発振する周波数は、分散曲線とビームの速さの直線の交点で決まる（@fig-dispersion）。電流が Johnson の開始条件 $C N = 0.314$ を超えると発振する。
- kA 級のビームは自分の電荷で減速し、交点（周波数）が下がる。電子がエネルギーを渡しすぎると同期から外れ、跳ね返ることもある。これが効率の上限を決める。

= 計算の方法

#figure(image("results/bwo-3d.png", width: 100%), caption: [二つの BWO の 3D の設計（SolidCraft、半分を切り取った図）。灰色が金属の管、橙色が電子ビーム。どちらも軸のまわりの回転体である。]) <fig-3d>

形は SolidCraft で回転体として設計し（`model/`）、EMCraft はその設計を読み込んで解く。
3D のまま解くと、Ku 帯でも格子が約 2700 万点（r–z の約 270 倍）、1 回の計算が 40 時間ほどになり、条件を振って設計することはできない。
管もビームも軸のまわりで同じ形（@fig-3d）なので、場と電子も軸のまわりで変わらないとして、軸を含む半平面（r–z 面）の 2 次元に落として解く。

- 回転体として r–z 面だけを解く（`solve.particles`、`axisymmetric`）。壁は格子の階段で近似し、周波数はやや低く出る。
- ビームは陰極側の端から、決まった電流と電圧で入れる。ガイド磁場は構造の後ろで弱め（`particles.magnetic` の `end`）、ビームを壁に当てる（コレクタ）。
- 出力は、コレクタの先の面を通るポインティング・ベクトルの流れを時間平均して求める（`particles.output`）。効率は出力 ÷ ビームの電力。

= Ku 帯の BWO：公表例との照合 <sec-ku>

Na ら（J. Comput. Phys. 346:295, 2017；arXiv:1701.03784 §5.1）の構造とビームをそのまま組んだ（@fig-ku-section）。
格子は 0.5 mm（軸方向に 4 倍細かく）、100 ns を解く（約 8.5 分）。

#figure(image("results/ku-section.png", width: 100%), caption: [Ku 帯の BWO の断面（r–z 面の半分、灰色が金属、黄色がビーム）。壁の波形 $R = 15 + 2.1 cos(2 pi z\/7.5)$ mm を 14.5 周期。ビームは 550 kV、1.5 kA、5 T。磁場は z = 140 mm で弱まり（赤）、出力はその先（青）で測る。]) <fig-ku-section>

#figure(grid(columns: 3, gutter: 6pt,
  image("results/final-ku-power.png"), image("results/final-ku-spectrum.png"), image("results/final-ku-phase.png")),
  caption: [Ku 帯の結果。左：出力（約 50 ns で定常）。中：スペクトル（15.32 GHz の単一の山）。右：電子の z と運動エネルギー（束になる様子、@fig-principle (b)）。]) <fig-ku-results>

#figure(image("results/ku-evolution.png", width: 100%), caption: [Ku 帯の時間発展。$E_z$（青が負、赤が正、全時刻で同じ色の目盛り）に電子（黒い点）を重ねた。遅波構造に立つ波が育ち、ビームが束になって進み、コレクタで壁へ曲がる。動画：#video("ku-growth", [成長 0〜100 ns]) ・ #video("ku-rf", [定常の RF 約 9 周期])。]) <fig-ku-evolution>

#table(columns: 3, align: (left, right, right),
  [*量*], [*EMCraft（0.5 mm）*], [*Na ら*],
  [発振周波数], [15.32 GHz], [15.575 GHz],
  [定常になるまで], [約 50 ns], [約 35 ns],
  [出力・効率], [70 MW・8.5%], [記載なし],
)

周波数が 1.6% 低いのは、壁の階段近似による。EMCraft の以前の検証で、格子を細かくして外挿すると 15.46〜15.66 GHz となり、論文を挟んだ。

= S バンドの BWO：設計

== 目安から寸法へ

Molchanov と Gurnevich（Nonlinear Phenomena in Complex Systems 27(2):123, 2024）は、550 keV、80 Ω（約 6.9 kA）、1.3 T 以上で約 1 GW、効率 27〜28% を示したが、
寸法は目安（周期 $approx 0.37 lambda_g$、平均半径 $approx 0.29 lambda_g$、深さ $approx lambda_g \/ 12$）だけである。
3.6 GHz で三つが矛盾しない $lambda_g = 127$ mm から、周期 47 mm、平均半径 36.9 mm、深さ 10.6 mm とした（波形は正弦波）。

#figure(image("results/sband-dispersion.png", width: 70%), caption: [S バンドの遅波構造（最終案の周期 44 mm）の分散（青、EMCraft）と、ビームの速さの直線。交点が発振の目安：550 keV では 3.78 GHz、0.8c に減速したビームでは 3.67 GHz。]) <fig-dispersion>

== 設計の要点

目安の寸法のままでは、ビームが空間電荷で減速して効率は 2% だった。効いたのは次の三つである（1 回 5〜8 分の計算で変数を振った）。
- ビームを壁に近づける（半径 25 → 29.5 mm）：減速が減り、結合が強まる。周期を 44 mm に詰めて、効率 19%。
- コレクタを置いて出力を測り直す：ビームの束が出力面を横切る分が除かれ、同じ構造で 15%。
- 出力側の 2 周期を浅くする：深さは周期の中央から中央へなだらかに変える。減速した電子の跳ね返りが減り（0.41 kA）、17.0%。

#figure(image("results/sband-section.png", width: 100%), caption: [S バンドの最終案。カットオフネック、挿入部 30 mm、周期 44 mm の波形 5 周期（後半 2 周期をなだらかに浅く）、出力ホーン。ビームは 550 kV、6.9 kA、半径 28.5〜30.5 mm、2.5 T。]) <fig-sband-section>

== 結果

#figure(grid(columns: 3, gutter: 6pt,
  image("results/final-sband-power.png"), image("results/final-sband-spectrum.png"), image("results/final-sband-phase.png")),
  caption: [S バンドの最終案の結果。左：出力（約 35 ns で定常、約 0.65 GW）。中：スペクトル（3.40 GHz）。右：電子の z と運動エネルギー。]) <fig-sband-results>

#figure(image("results/sband-evolution.png", width: 100%), caption: [S バンドの時間発展（@fig-ku-evolution と同じ描き方）。動画：#video("sband-growth", [成長 0〜60 ns]) ・ #video("sband-rf", [定常の RF])。]) <fig-sband-evolution>

#table(columns: 3, align: (left, right, right),
  [*量*], [*EMCraft の最終案*], [*Molchanov と Gurnevich*],
  [発振周波数], [3.40 GHz], [約 3.6 GHz],
  [出力], [0.64 GW], [約 1 GW],
  [効率], [17.0%], [27〜28%],
)

周波数が低いのは、ビームが空間電荷と相互作用で約 0.7c まで減速し、交点が下がったためである（@fig-dispersion）。
効率が届かないのは、論文が最適化した両端の波形（反射の強さ）と挿入部の寸法が公表されておらず、本書では再現していないためと考える。

= まとめ

- Ku 帯の公表例を、EMCraft の軸対称の粒子シミュレーションは 15.32 GHz の単一モードで再現した（−1.6% は壁の階段近似）。
- S バンドは目安の寸法から設計し、3.40 GHz、0.64 GW、効率 17.0% を得た。ビームを壁に近づけることが最も効いた。
- 出力は、ビームを出力面の手前で止めて（コレクタ）測る必要がある。止めないと効率が数ポイント多く出る。

本書はシミュレーションによる検討で、実際の装置の測定ではない。
