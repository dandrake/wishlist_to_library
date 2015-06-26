""".

Generate an RSS feed of books available at your local library from a
wishlist on LibraryThing.

https://github.com/dandrake/wishlist_to_library
"""

import string
import time
import json
import sys
import urllib.request
from bs4 import BeautifulSoup

def amazon_to_isbns(fn):
    """Given a filename containing JSON data from an Amazon wishlist (see
    https://github.com/doitlikejustin/amazon-wish-lister), this returns
    a list of ISBNs.

    This isn't used in this script; it's for your convenience so you can
    use it if you are converting from an Amazon wishlist to a
    LibraryThing one.

    Here we assume the JSON decodes as a list of dictionaries, each with
    a `link` attribute that starts with
    "`http://www.amazon.com/dp/0316212377/...`" where the bit following
    the "dp" is an ISBN/ASIN.
    """
    with open(fn) as f:
        wishlist = json.load(f)
        ret = []
        for item in wishlist:
            isbn = item['link'].split('/')[4]
            # is it really an isbn?
            if (all(c in string.digits for c in isbn) and
                isbn[-1] in string.digits + 'X'):
                ret.append(isbn)
    return ret
    # or if you just want to copy and paste the ISBNs:
    # for isbn in ret:
    #     print(isbn)

def isbn_to_soup(isbn):
    """When you search, it will take you straight to the book's page if
    there's only one result, or it will give you a page of search
    results. This function's purpose is to just return a tuple: a URL to
    the book page, and the BeautifulSoup-ified version of the book page

    If the ISBN goes directly to a book page, it's easy. Otherwise, we
    look through all the links in the search results and simply take the
    first one that points to a book page.

    returns ('', None) if it can't find the book.
    """
    mpl_lookup_url = 'https://www.linkcat.info/cgi-bin/koha/opac-search.pl?idx=isbn&q={0}'
    result = urllib.request.urlopen(mpl_lookup_url.format(isbn))
    soup = BeautifulSoup(result.read())
    if 'opac-detail' in result.geturl():
        # sweet, we got a book page
        return (result.geturl(), soup)
    else:
        # find first book page link, follow that, return it, hope for the best
        try:
            url = ('https://www.linkcat.info' + 
                   [link for link in
                    [a.get('href') for a in soup.find_all('a')] 
                    if 'opac-detail' in link][0])
        except IndexError:
            # no links with opac-detail? Looks like the book isn't in MPL.
            return ('', None)
        return (url, BeautifulSoup(urllib.request.urlopen(url).read()))

def soup_to_libs(soup):
    """My library system lists what branches have a book in an HTML table;
    this just looks for table rows and returns the name of the branch
    and the status (Available, Checked out, etc) as tuples in a list.
    """
    rows = soup.table.tbody.find_all('tr')
    texts = [[td.text.strip() for td in tds] 
             for tds in [row.find_all('td') for row in rows]]
    return [(t[0], t[5]) for t in texts]

def filter_and_sort_libs(libs):
    """take the output from `soup_to_libs()` and return a list of library
    branches at which the item is available. You can also use this to
    sort the list so that the closest library is first, etc.
    """
    return [x[0] for x in libs if 'Available' in x[1]]

def book_to_feed_item(book):
    """return a dictionary with keys title, description, id, link, content
    -- or an empty dictionary if the book isn't available.
    """
    ret = dict()
    url, soup = isbn_to_soup(book['ISBN'])
    if url == '' and soup is None:
        return ret
    libs = filter_and_sort_libs(soup_to_libs(soup))
    if len(libs) == 0:
        return ret
    else:
        #print('Adding {0} to feed...'.format(book['title']))
        bullet = '<li>{0}</li>'
        rows = '\n'.join([bullet.format(lib) for lib in libs])
        ret['content'] = r'''<p><i>{0}</i> by {1} is available from:</p>
        <ul>{3}</ul>

        <a href="{2}">MPL link</a> and
        <a href="http://www.librarything.com/isbn/{4}">LibraryThing link</a>
        '''.format(book['title'], book['author_fl'], url, rows, book['ISBN'])

        ret['title'] = book['title'] + ' by ' + book['author_fl']
        ret['description'] = book['title'] + ' by ' + book['author_fl']
        ret['link'] = {'href': url, 'rel': 'alternate'}
        # add in the time so that every time the script runs, the feed
        # reader thinks it's a new unread item
        ret['id'] = url + '?' + str(time.time())
        return ret
        
def generate_feed(books):
    """given a list of books (dictionaries of the kind `get_wishlist()`
    produces) return a feed as a FeedGenerator object.
    """
    from feedgen.feed import FeedGenerator
    fg = FeedGenerator()
    fg.id('something that can act as an ID, I guess')
    fg.title('Wishlist books available from my public library')
    fg.author({'name': "wishlist_to_library.py", 'uri': 'https://github.com/dandrake/wishlist_to_library'})
    fg.link(href='http://foo.com', rel='self')
    fg.description('My wishlist items (from LibraryThing) currently available from my public library system')
    for book in books:
        item = book_to_feed_item(book)
        if len(item) > 0:
            fe = fg.add_entry()
            fe.content(item['content'])
            fe.title(item['title'])
            fe.description(item['description'])
            fe.link(item['link'])
            fe.id(item['id'])
    return fg

def get_wishlist():
    """See https://www.librarything.com/wiki/index.php/LibraryThing_JSON_Books_API for API documentation.

    Returns my LibraryThing books that are in my wishlist. Each is a
    dictionary; the relevant keys are: ISBN, author_fl (or author_lf if
    you want "Family Name, Given Name"), and title.
    """
    url = 'https://www.librarything.com/api_getdata.php?userid=birfoomp&key=1970264230&showCollections=1&responseType=json&max=250'
    return [b for b in 
            json.loads(urllib.request.urlopen(url).read().decode('utf-8'))['books'].values()
            if '4' in b['collections'].keys()]

if __name__ == '__main__':
    feed = generate_feed(get_wishlist()).rss_str(pretty=True)
    try:
        with open(sys.argv[1], 'w') as outf:
            outf.write(feed)
    except IndexError:
        print(feed)
