
from flask import Blueprint
blueprint = Blueprint("books", __name__)

from datetime import datetime

from flask import render_template, request, url_for, redirect, g, session, flash
from bson.objectid import ObjectId

from src.mongodb_api_1 import *
from src.auth import login_required

@blueprint.route('/new_book', methods=['GET', 'POST'])
@login_required
def new_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        cover_image = request.form.get('cover_image')
        entry_point = request.form.get('entry_point')
        rss = request.form.get('rss')
        section_css_selector = request.form.get('section_css_selector')
        title_css_selector = request.form.get('title_css_selector')
        paragraph_css_selector = request.form.get('paragraph_css_selector')
        next_chapter_css_selector = request.form.get('next_chapter_css_selector')

        insertOne('rr', 'books',
            {
                #added by the system
                'owner' : g.user['userinfo']['name'],
                'last_update' : datetime.now(),
                #collected from form
                'title' : title,
                'author' : author,
                'cover_image' : cover_image,
                'entry_point' : entry_point,
                'rss' : rss,
                'section_css_selector' : section_css_selector,
                'title_css_selector' : title_css_selector,
                'paragraph_css_selector' : paragraph_css_selector,
                'next_chapter_css_selector' : next_chapter_css_selector
            }
        )
        flash('New data instance created successfully!')
        
        #return redirect(url_for('books.edit_book/%s' % id))
 
    data = {
        "title": {'label': "Title", "name": "title", 'text': "" },
        "author": {'label': "author", "name": "author", 'text': "" },
        "cover_image": {'label': "Cover Image URL", "name": "cover_image", 'text': "" },
        "entry_point": {'label': "Starting URL", "name" : "entry_point", 'text': "royalroad.com" },
        "rss": {'label': "RSS URL", 'name': "rss", 'text': "" },
        "section_css_selector": {'label': "Section CSS selector","name": "section_css_selector", 'text': "" },
        "title_css_selector": {'label': "Title CSS selector", 'name': "title_css_selector", 'text': "" },
        "paragraph_css_selector": {'label': "Paragraph CSS selector", "name":"paragraph_css_selector",'text': "" },
        "next_chapter_css_selector": {'label': "Next Chapter Button CSS selector", 'name': "next_chapter_css_selector", 'text': "" }
    }
    kwargs = {
            "TITLE": "New Book",
            "DERCRIPTION": "",
            "SUBMIT": "Submit",
            "DATA": data,
            "ACTION": ""
    }

    return render_template('data_form.html', **kwargs)


@blueprint.route('/edit_book/<id>', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    id = ObjectId(id)
    book = findOne('rr', 'books', {'_id': id})
    if book['owner'] != g.user['userinfo']['name']:
        redirect(url_for('books.list_books'))

    if request.method == 'POST':
        # Update the JSON data with the form values

        import json
        with open("data/empty_book_form.json", 'r') as f:
            book_form_template = json.load(f)
        form = request.form
        
        for key in book_form_template.keys():
            book_form_template[key] = form.get(key)
        
        updateOne('rr','books', {'_id': id}, book_form_template)
        flash("data updated!")
        return 'Data updated successfully.'


    # Retrieve the data from MongoDB
    book = findOne('rr', 'books', {'_id': id})

    data = {
        "title": {'label': "Title", "name": "title"},
        "author": {'label': "author", "name": "author"},
        "cover_image": {'label': "Cover Image URL", "name": "cover_image"},
        "entry_point": {'label': "Starting URL", "name" : "entry_point", 'text': "royalroad.com" },
        "rss": {'label': "RSS URL", 'name': "rss", 'text': "" },
        "section_css_selector": {'label': "Section CSS selector","name": "section_css_selector", 'text': "" },
        "title_css_selector": {'label': "Title CSS selector", 'name': "title_css_selector", 'text': "" },
        "paragraph_css_selector": {'label': "Paragraph CSS selector", "name":"paragraph_css_selector",'text': "" },
        "next_chapter_css_selector": {'label': "Next Chapter Button CSS selector", 'name': "next_chapter_css_selector", 'text': "" }
    }
    for key, value in data.items():
        data[key]["text"] = book[key]


    kwargs = {
            "TITLE": "Edit Data",
            "DERCRIPTION": "",
            "SUBMIT": "Save",
            "DATA": data,
            "NO_REDIRECT_ONSUBMIT": True,
            "INCLUDE_IMPORT_EXPORT": True,
            "ACTION": url_for('books.edit_book', id=id),
    }
    return render_template('data_form.html', **kwargs)

@blueprint.route('/download_book/<id>')
def download_book(id):  
    def gen_config(id, data):
        db_api = mongodb_api.from_json("data/mongodb.json")
        data = db_api.findOne({'id': id})['document']

        # FOLDERNAME = hash_url
        config = {}
        config['cache'] = f'cache/{id}'
        config['ignore_cache'] = False # data.get('ignore_cache', True)

        # config['callbacks'] = "books.RR_Template.cbs_base"

        book = { 
            "title"           : data["title"],
            "author"          : data["author"],
            "epub_filename"   : f'out/{id}.epub',
            "cover_image"     : data["cover_image"],
            "css_filename"    : "webbook_dl/kindle.css",
            "entry_point"     : data["entry_point"],
            "chapter"         : data['chapter'],
            "include_images"  : data["include_images"],
        }

        config['book'] = book 
        return config

    from html_to_epub import Config, Book
    config = Config(gen_config(id, request.form))
    config.ignore_last_cache = True

    import os
    os.makedirs(config.cache, exist_ok=True)

    # Still relative
    from books.RR_Template.cbs_base import Callbacks
    book = Book(config, Callbacks(config))

    book.load_html()

    print(config.book.epub_filename)

    from ebooklib import epub
    epub.write_epub(config.book.epub_filename, book.generate_epub(), {})
 

    from RR_cnf_gen import foldername_from_title
    epub_filename = "%s.epub" % foldername_from_title(book.title)

    return redirect(url_for("royalroad_dl.download_book_submit", id=id, epub_filename=epub_filename))


@blueprint.route("/", methods=['GET', 'POST'])
def head():
    kwargs = {
            "TITLE": "RoyalRoad Book Download",
            "DERCRIPTION": "Enter the url to the fiction page of a royalroad book",
            "SUBMIT": "Submit",
            "DATA": {'fiction_page_url': {'label': 'Url', 'type': 'str', 'text': ''}},
            "ACTION": url_for("royalroad_dl.book_config"),
    }
    return render_template('data_form.html', **kwargs)


def royalroad_cofig_from_fiction_page(url, ignoe_cache = False):
    from html_to_epub.util import Network
    from lxml.cssselect import CSSSelector

    from RR_cnf_gen import first_match, foldername_from_title

    base_url = "https://www.royalroad.com"
    cache_dir = "./cache/RR"
    import os
    os.makedirs(cache_dir, exist_ok=True)
    
    cache_filename = Network.cache_filename(cache_dir, url)


    tree = Network.load_and_cache_html(url, cache_filename, ignoe_cache)

    result = {}
    result['TITLE']   = first_match(tree, "div.fic-header h1").text;
    result['AUTHOR']  = first_match(tree, "div.fic-header h4 a").text;
    result['COVER']   = first_match(tree, "div.fic-header img").get('src').split('?')[0];
    result['ENTRY']   = base_url + first_match(tree, "div.portlet table a").get('href').split('?')[0];
    result['OUTFILE'] = foldername_from_title(result['TITLE'])

    print(result)
    return result

@blueprint.route("/configure-book", methods=['GET', 'POST'])
def book_config():
    data = {
        "TITLE"      : {'label': 'Title',          },
        "AUTHOR"     : {'label': 'Author',         },
        "COVER"      : {'label': 'Cover',          },
        "ENTRY"      : {'label': 'First Chapeter', },
        "INCLUDE_IMG"  : {'label': 'Include Images', 'type': 'bool', 'value': False },
        #  "OUTFILE"    : {'label': 'Epub File Name', },
    }

    if request.method == 'POST':
        request_data = request.form

        fiction_page_url = request_data.get("fiction_page_url");
        if not fiction_page_url: 
            return "ERROR: No 'fiction_page_url' was privided. Go to <a href=\"" +  \
                    url_for("royalroad_dl.head") +"\">royalroad-dl</a>"

        from urllib.parse import urlparse
        
        parsed_url = urlparse(fiction_page_url)
        path_parts = parsed_url.path.split("/")
        fiction_id = path_parts[2] if len(path_parts) > 2 else None

        if not fiction_id: 
            return "ERROR: Failed to parse 'fiction_page_url'. Go to <a href=\"" +  \
                    url_for("royalroad_dl.head") +"\">royalroad-dl</a>"

        id = fiction_id;

        if fiction_page_url:
            request_data = royalroad_cofig_from_fiction_page(fiction_page_url)

        for key in data.keys():
            value = request_data.get(key)
            if value: 
                data[key]['text'] = value

    kwargs = {
            "TITLE": "RoyalRoad Book Configuration",
            "DERCRIPTION": "Please check that the following configuration is correct (Note that after clicking, you just have to wait, sorry for the lack of visual indication)",
            "SUBMIT": "Download",
            "DATA": data,
            "NO_REDIRECT_ONSUBMIT": False,
            # "ACTION": url_for("royalroad_dl.book_config"),
            "ACTION": url_for("royalroad_dl.download_book", id=id),
    }
    return render_template('data_form.html', **kwargs)

@blueprint.route('/list_books', methods = ['GET'])
def list_books():
    # Get all available data instances from MongoDB
    # data_instances = db.collection.find()
    books_list = []

    if g.user:
        pprint(g.user)
        books = find('rr', 'books', {'owner': g.user['userinfo']['name']})

        # Prepare the data list to pass to the template
        for book in books:
            print(books)
            books_list.append({
                '_id': book['_id'],
                'title': book['title']
            })
    else:
        flash('Not logged in!')

    return render_template('books.html', data_list=books_list)

@blueprint.route('/delete_book/<id>', methods = ['POST'])
@login_required
def delete_book(id):
    id = ObjectId(id)
    book = findOne('rr', 'books', {'_id': id})
    if book['owner'] != g.user['userinfo']['name']:
        redirect(url_for('books.list_books'))
    deleteOne('rr', 'books', {"_id": id})
    return redirect('../list_books')



