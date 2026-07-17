#!/usr/bin/env python3
"""Generate a minimal PDF with a greeting message."""

import argparse
import os
import zlib


def pdf(text: str, path: str):
    content = f"BT /F1 48 Tf 50 700 Td ({text}) Tj ET"
    raw = content.encode("latin-1")
    compressed = zlib.compress(raw)

    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
            b"/MediaBox [0 0 612 792] "
            b"/Contents 4 0 R "
            b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\n"
            b"endobj"
        ),
        b"4 0 obj\n<< /Length %d /Filter /FlateDecode >>\nstream\n%s\nendstream\nendobj"
        % (len(compressed), compressed),
    ]

    offsets = []
    lines = [b"%PDF-1.4"]
    for obj in objects:
        offsets.append(sum(len(l) + 1 for l in lines))
        lines.append(obj)

    xref_offset = sum(len(l) + 1 for l in lines)
    xref = b"xref\n0 5\n0000000000 65535 f \n"
    for offset in offsets:
        xref += b"%010d 00000 n \n" % offset

    lines.append(xref)
    lines.append(
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % xref_offset
    )

    with open(path, "wb") as f:
        f.write(b"\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="World")
    parser.add_argument("--greeting", default="Hello")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    out_path = args.out or os.path.join("/tmp", f"{args.name.replace(' ', '_')}.pdf")
    pdf(f"{args.greeting}, {args.name}!", out_path)
    print(out_path)
