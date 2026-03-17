from flask import Flask, render_template, request
from flask_frozen import Freezer
import os
import re
import yaml
import markdown
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
freezer = Freezer(app)
app.config["TEMPLATES_AUTO_RELOAD"] = True

BLOG_POSTS_DIR = Path(__file__).parent / "blog_posts"

def parse_blog_post(file_path):
    """Parse a markdown file with YAML frontmatter and extract metadata and content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            markdown_content = parts[2].strip()
        else:
            frontmatter = {}
            markdown_content = content
    else:
        frontmatter = {}
        markdown_content = content
    
    title = frontmatter.get('title', file_path.stem)
    date_str = frontmatter.get('date', '')
    tags = frontmatter.get('tags', [])
    
    # Ensure tags is a list
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(',')]
    
    # Parse date
    try:
        post_date = datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        post_date = datetime.now()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['fenced_code', "gfm_admonition"])
    
    return {
        'filename': file_path.name,
        'slug': file_path.stem,
        'title': title,
        'date': post_date,
        'date_str': date_str,
        'tags': tags,
        'content': markdown_content,
        'html_content': html_content
    }

def get_all_blog_posts():
    """Get all blog posts sorted by date (newest first)."""
    if not BLOG_POSTS_DIR.exists():
        return []
    
    posts = []
    for file_path in BLOG_POSTS_DIR.glob("*.md"):
        try:
            post = parse_blog_post(file_path)
            posts.append(post)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
    
    # Sort by date, newest first
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/blog.html", methods=["GET"])
def blog():
    posts = get_all_blog_posts()
    tags_param = request.args.get('tags', '')
    
    # Parse selected tags (comma-separated)
    selected_tags = [tag.strip() for tag in tags_param.split(',') if tag.strip()]
    
    # Filter by tags if provided - post must contain ALL selected tags
    if selected_tags:
        posts = [post for post in posts if all(tag in post['tags'] for tag in selected_tags)]
    
    # Get unique tags for filter UI
    all_tags = set()
    for post in get_all_blog_posts():
        all_tags.update(post['tags'])
    all_tags = sorted(list(all_tags))
    
    return render_template("blog.html", posts=posts, tags=all_tags, selected_tags=selected_tags)

@app.route("/blog/<slug>.html", methods=["GET"])
def blog_post(slug):
    posts = get_all_blog_posts()
    post = next((p for p in posts if p['slug'] == slug), None)
    
    if not post:
        return "Post not found", 404
    
    return render_template("blog_post.html", post=post)

@freezer.register_generator
def blog_post_generator():
    """Generate URLs for all blog posts."""
    for post in get_all_blog_posts():
        yield 'blog_post', {'slug': post['slug']}

if __name__ == "__main__":
    freezer.freeze()
