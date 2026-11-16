// The reports' common look: A4, a title block, numbered sections and equations, and a
// verification box for each check against a closed form or a published result.

#let report(title: "", subtitle: "", authors: (), date: none, abstract: [], lang: "ja", body) = {
  set document(title: title, author: authors)
  set page(paper: "a4", margin: (x: 2.2cm, y: 2.4cm), numbering: "1 / 1")
  set text(font: if lang == "ja" { ("Noto Sans CJK JP", "DejaVu Sans") } else { ("Noto Sans", "DejaVu Sans") }, size: 10.5pt, lang: lang)
  set par(justify: true, leading: 0.7em)
  set heading(numbering: "1.1")
  set math.equation(numbering: "(1)")
  show heading.where(level: 1): it => block(above: 1.6em, below: 0.9em, text(size: 14pt, weight: "bold", it))
  align(center)[
    #set par(justify: false)
    #text(size: 20pt, weight: "bold", title) \
    #v(0.3em)
    #text(size: 12pt, fill: luma(80), subtitle) \
    #v(0.6em)
    #authors.join(", ") #if date != none [ · #date]
  ]
  v(1em)
  block(fill: luma(245), inset: 12pt, radius: 4pt, width: 100%)[*#if lang == "ja" [要旨] else [Abstract]* \ #abstract]
  v(1em)
  body
}

// A check of a computed number against a reference: what, ours, the reference, the tolerance.
#let check(what, ours, reference, tolerance, source) = block(
  stroke: (left: 3pt + rgb("#2b83f1")), inset: (left: 10pt, y: 6pt), width: 100%,
)[
  #context if text.lang == "ja" [
    *検証：#what* \
    計算 #ours ／ 基準 #reference（許容 #tolerance） \
    #text(size: 9pt, fill: luma(90))[出典：#source]
  ] else [
    *Check: #what* \
    Computed #ours / reference #reference (tolerance #tolerance) \
    #text(size: 9pt, fill: luma(90))[Source: #source]
  ]
]
