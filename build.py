#!/usr/bin/env python3
"""Build a dictd database from the Century Dictionary (1889) markdown extraction.

Source: https://github.com/hupong/century-dictionary -- 187,438 headwords, A-Z,
extracted from the archive.org scans in 2017.  The Century Dictionary is public
domain (1889-1891, William Dwight Whitney ed.).

Writes century.dict.dz + century.index in dictd's native format, so dictfmt is
not required.  The index is three tab-separated fields per line -- headword,
offset, length -- with the offsets in dictd's own base64 variant, and sorted by
dictd's comparison (case folded, non-alphanumerics ignored) or binary search in
the server will miss entries.

    ./build.py ~/path/to/century.md
"""
import os, re, subprocess, sys

B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

def b64(n):
    """dictd's base64: big-endian, minimal digits, no padding."""
    if n == 0:
        return B64[0]
    out = ""
    while n:
        out = B64[n & 63] + out
        n >>= 6
    return out

def sort_key(w):
    """dictd's index collation, determined experimentally.

    The server binary-searches the index, so it must be sorted exactly as dictd
    compares: fold ASCII case, drop ASCII punctuation, keep spaces, and keep
    non-ASCII bytes untouched, comparing bytes in the C locale.

    `LC_ALL=C sort -df` is close but wrong: -d drops accented letters, so
    "Vígfússon" sorts before "Vigil" while dictd -- which keeps the UTF-8 bytes,
    and 0xC3 > 'i' -- puts it after.  One mis-sorted neighbour makes the binary
    search miss, and a naive key (fold case, strip everything non-alphanumeric)
    failed 35 of 150 EB1911 lookups.
    """
    out = []
    for b in w.encode("utf8"):
        if b > 127:
            out.append(b)
        else:
            c = chr(b)
            if c.isalnum() or c == " ":
                out.append(ord(c.lower()))
    return bytes(out)

def clean(s):
    s = s.replace("****", " ").replace("**", "")
    s = s.replace("‘", "'").replace("’", "'")
    return re.sub(r"[ \t]+", " ", s).strip()

def entries(path):
    head, body = None, []
    for line in open(path, encoding="utf8", errors="ignore"):
        m = re.match(r"^####\s*(.+?)\s*$", line)
        if m:
            if head:
                yield head, body
            head, body = m.group(1), []
        elif head is not None:
            t = clean(line)
            # the first sense usually repeats the headword in bold; drop it
            if t and not body and t.lower().startswith(head.lower()):
                t = t[len(head):].lstrip(" .,")
            if t:
                body.append(t)
    if head:
        yield head, body

def main(src):
    out = os.path.dirname(os.path.abspath(__file__))
    dict_path = os.path.join(out, "century.dict")
    idx_path = os.path.join(out, "century.index")
    index = []
    with open(dict_path, "w", encoding="utf8") as f:
        def put(word, text):
            off = f.tell()
            f.write(text)
            index.append((word, off, f.tell() - off))
        # dictd serves these as metadata
        put("00-database-short", "     Century Dictionary (1889)\n")
        put("00-database-url", "     https://github.com/hupong/century-dictionary\n")
        put("00-database-info",
            "     The Century Dictionary and Cyclopedia (1889-1891),\n"
            "     William Dwight Whitney, ed.  Public domain.\n"
            "     Text from the 2017 markdown extraction of the archive.org\n"
            "     scans; OCR errors from the original pass remain.\n")
        n = 0
        for head, body in entries(src):
            if not body:
                continue
            text = head + "\n" + "".join("  " + b + "\n" for b in body)
            put(head, text)
            n += 1
    index.sort(key=lambda r: sort_key(r[0]))
    with open(idx_path, "w", encoding="utf8") as f:
        for word, off, ln in index:
            f.write(f"{word}\t{b64(off)}\t{b64(ln)}\n")
    subprocess.run(["dictzip", "-f", dict_path], check=True)
    print(f"  {n} entries")
    for p in (dict_path + ".dz", idx_path):
        print(f"  {os.path.basename(p):<22} {os.path.getsize(p)/1048576:.1f} MB")

if __name__ == "__main__":
    main(os.path.expanduser(sys.argv[1]))
