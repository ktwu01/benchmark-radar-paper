"""Check author identity and affiliation links in converted title output."""

import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

import pytest

EXPECTED_AUTHORS = {
    "Koutian Wu": ["Earth-Space-AI", "Tacite AI"],
    "Junjie Zhou": ["Hangzhou Dianzi University"],
    "Ergan Shang": ["Carnegie Mellon University"],
    "Jiayu Wang": ["Xi'an Jiaotong University"],
    "Pengqian Han": ["The University of Auckland"],
    "Junkai Wang": ["Tsinghua University"],
    "Wanghan Xu": ["Shanghai Jiao Tong University"],
    "Songyuanyi Lu": ["The University of Hong Kong"],
    "Lin Shi": ["Cornell Tech"],
}
LATEXML_NS = {"ltx": "http://dlmf.nist.gov/LaTeXML"}
CORRESPONDING_EMAIL = "mailto:k@tacite.ai"


class HTMLTree(HTMLParser):
    """Parse the emitted HTML5 without requiring a browser or HTML dependency."""

    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = ET.Element("html-document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        element = ET.SubElement(self.stack[-1], tag, dict(attrs))
        if tag not in self.VOID_TAGS:
            self.stack.append(element)

    def handle_startendtag(self, tag, attrs):
        ET.SubElement(self.stack[-1], tag, dict(attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        element = self.stack[-1]
        if len(element):
            element[-1].tail = (element[-1].tail or "") + data
        else:
            element.text = (element.text or "") + data


def has_classes(element, *classes):
    return set(classes).issubset(element.get("class", "").split())


def text_without_markers(element):
    """Ignore rendered affiliation/footnote markers, retaining all prose."""
    if (
        element.tag.rsplit("}", 1)[-1] in {"tags", "tag"}
        or has_classes(element, "ltx_tag")
        or has_classes(element, "ltx_note_mark")
    ):
        return ""
    text = element.text or ""
    for child in element:
        text += text_without_markers(child) + (child.tail or "")
    return text


def normalized_text(element):
    return " ".join(text_without_markers(element).replace("\u2019", "'").split())


def assert_author_mapping(authors, name_nodes, affiliation_nodes):
    names = []
    for author in authors:
        name = name_nodes(author)
        assert len(name) == 1, "Each author needs exactly one rendered name"
        names.append(normalized_text(name[0]))
    assert names == list(EXPECTED_AUTHORS), "Missing, duplicate, or reordered authors"

    for name, author in zip(names, authors, strict=True):
        affiliations = [normalized_text(node) for node in affiliation_nodes(author)]
        assert sorted(affiliations) == sorted(EXPECTED_AUTHORS[name]), name
        mail_links = [
            node.get("href") for node in author.iter() if node.get("href", "").startswith("mailto:")
        ]
        expected_mail = [CORRESPONDING_EMAIL] if name == "Koutian Wu" else []
        assert mail_links == expected_mail, f"Correspondence attached to {name}"
        if expected_mail:
            assert "Corresponding author:" in normalized_text(author)


def test_converted_title_preserves_all_authors_and_their_affiliations(tmp_path):
    tools = {name: shutil.which(name) for name in ("latexml", "latexmlpost")}
    missing = [name for name, executable in tools.items() if executable is None]
    if missing:
        message = "Author HTML verification requires " + ", ".join(missing)
        if os.environ.get("REQUIRE_LATEXML") == "1":
            pytest.fail(message)
        pytest.skip(message)

    repository = Path(__file__).resolve().parents[1]
    manuscript = (repository / "main.tex").read_text(encoding="utf-8")
    title_end = re.search(r"(?m)^\\maketitle\b", manuscript)
    assert title_end is not None, "Cannot locate the manuscript's title rendering"
    source = tmp_path / "author-title.tex"
    source.write_text(manuscript[: title_end.end()] + "\n\\end{document}\n", encoding="utf-8")
    xml_path = tmp_path / "author-title.xml"
    html_path = tmp_path / "author-title.html"
    commands = [
        [
            tools["latexml"],
            f"--path={repository}",
            f"--destination={xml_path}",
            f"--log={tmp_path / 'latexml.log'}",
            str(source),
        ],
        [
            tools["latexmlpost"],
            "--format=html5",
            f"--destination={html_path}",
            str(xml_path),
        ],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=120)
        log = tmp_path / (Path(command[0]).name + "-command.log")
        log.write_text(result.stdout + result.stderr, encoding="utf-8")
        assert result.returncode == 0, f"Conversion failed; see {log}\n{result.stderr}"

    document = ET.parse(xml_path).getroot()
    assert not document.findall(".//ltx:ERROR", LATEXML_NS)
    assert_author_mapping(
        document.findall(".//ltx:creator[@role='author']", LATEXML_NS),
        lambda author: author.findall("ltx:personname", LATEXML_NS),
        lambda author: author.findall("ltx:contact[@role='affiliation']", LATEXML_NS),
    )

    html = HTMLTree()
    html.feed(html_path.read_text(encoding="utf-8"))
    html.close()
    assert_author_mapping(
        [node for node in html.root.iter() if has_classes(node, "ltx_creator", "ltx_role_author")],
        lambda author: [node for node in author.iter() if has_classes(node, "ltx_personname")],
        lambda author: [
            node
            for node in author.iter()
            if has_classes(node, "ltx_contact", "ltx_role_affiliation")
        ],
    )
