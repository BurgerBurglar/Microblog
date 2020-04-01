import os
import json
from flask import request, url_for, current_app


def get_sample_data(dtype):
    file_dir = os.path.dirname(__file__)
    db_file = os.path.join(file_dir, "data.json")
    with open(db_file) as f:
        data = json.load(f)[dtype]
    return data


def paginate_posts(query, redirect_to, perpage=None, **kw):
    page = request.args.get("page", 1, type=int)
    per_page = perpage or current_app.config["POSTS_PER_PAGE"] or 20
    pagination = query.paginate(page, per_page, error_out=False)
    return {
        "next_url": url_for(redirect_to, page=pagination.next_num, **kw) if pagination.has_next else None,
        "prev_url": url_for(redirect_to, page=pagination.prev_num, **kw) if pagination.has_prev else None,
        "posts": pagination.items
    }
