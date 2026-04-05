import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "notify_new_posts.py"
SPEC = importlib.util.spec_from_file_location("notify_new_posts", MODULE_PATH)
assert SPEC and SPEC.loader
notify_new_posts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(notify_new_posts)


class NotifyNewPostsTests(unittest.TestCase):
    def write_post(self, root: Path, relative_path: str, front_matter: str) -> Path:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(front_matter, encoding="utf-8")
        return path

    def test_list_candidate_posts_filters_non_publishable_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            published = self.write_post(
                root,
                "content/tech/launch-post.en.md",
                "+++\n"
                "title = 'Launch Post'\n"
                "draft = false\n"
                "+++\n",
            )
            draft = self.write_post(
                root,
                "content/tech/draft-post.en.md",
                "+++\n"
                "title = 'Draft Post'\n"
                "draft = true\n"
                "+++\n",
            )
            self.write_post(
                root,
                "content/search.en.md",
                "---\n"
                "title: search\n"
                "---\n",
            )
            self.write_post(
                root,
                "content/books/_index.en.md",
                "+++\n"
                "title = 'Books'\n"
                "+++\n",
            )

            candidates = notify_new_posts.list_candidate_posts(
                [
                    str(published),
                    str(draft),
                    str(root / "content/search.en.md"),
                    str(root / "content/books/_index.en.md"),
                    str(root / "content/tech/missing.en.md"),
                ]
            )

            self.assertEqual(
                candidates,
                [{"path": str(published), "title": "Launch Post"}],
            )

    def test_parse_feed_links_extracts_title_to_url_map(self) -> None:
        feed_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>Launch Post</title>
      <link>https://example.com/launch-post/</link>
    </item>
    <item>
      <title>Another Post</title>
      <link>https://example.com/another-post/</link>
    </item>
  </channel>
</rss>
"""

        links = notify_new_posts.parse_feed_links(feed_xml)

        self.assertEqual(
            links,
            {
                "Launch Post": "https://example.com/launch-post/",
                "Another Post": "https://example.com/another-post/",
            },
        )


if __name__ == "__main__":
    unittest.main()
