"""Regression coverage for semantic author-affiliation markup."""

from pathlib import Path


def test_latexml_can_associate_each_author_with_the_intended_affiliation():
    manuscript = (Path(__file__).resolve().parents[1] / "main.tex").read_text()
    title_start = manuscript.index(r"\title{")
    semantic_block = manuscript[
        title_start : manuscript.index(r"\makeatletter", title_start)
    ]

    expected = {
        "Junjie Zhou": "Hangzhou Dianzi University",
        "Ergan Shang": "Carnegie Mellon University",
        "Jiayu Wang": "Xi'an Jiaotong University",
        "Pengqian Han": "The University of Auckland",
        "Junkai Wang": "Tsinghua University",
        "Wanghan Xu": "Shanghai Jiao Tong University",
        "Songyuanyi Lu": "The University of Hong Kong",
        "Lin Shi": "Cornell Tech",
    }

    assert semantic_block.count(r"\author{") == 9
    assert r"\author{Koutian Wu\thanks{Earth-Space-AI; Tacite AI." in semantic_block
    for author, affiliation in expected.items():
        assert rf"\author{{{author}\thanks{{{affiliation}}}}}" in semantic_block
