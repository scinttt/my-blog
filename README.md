# Renren Zhang's Blog

Personal tech blog built with Hugo + PaperMod theme, deployed on Vercel.

🔗 **Live Site**: creaturelove.com


## Local Development

### First Time Setup
```bash
git clone https://github.com/scinttt/my-blog.git
cd my-blog
git submodule update --init --recursive  # Important: Pull theme files
```

### Local Preview
```bash
hugo server -D  # Include drafts
hugo server     # Published posts only
```

## Creating New Posts
```bash
# Create new post
hugo new posts/my-post.md

# Edit post
code content/posts/my-post.md

# Publish (remove draft = true or set to false)
git add .
git commit -m "Add new post"
git push
```

## Adding Images

### Method 1: Static Directory
```bash
# Put image in static/images/
cp photo.jpg static/images/

# Reference in Markdown
![description](/images/photo.jpg)
```

### Method 2: Post Directory
```bash
# Create post folder
hugo new posts/my-post/index.md

# Put image inside
cp photo.jpg content/posts/my-post/

# Reference in Markdown
![description](photo.jpg)
```

## Notes

- Remove `draft = true` or set to `draft = false` before publishing
- Vercel automatically builds and deploys after pushing to GitHub
- Remember to run `git submodule update --init --recursive` when cloning on a new machine

## License

Content licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
