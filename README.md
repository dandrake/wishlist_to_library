# wishlist-to-library

Slurp in your to-read book wishlist, look up the availability at your
local library, and generate an RSS feed with the available books.

This is inspired by
[Jon Udell's LibraryLookup](http://jonudell.net/LibraryLookup.html) but
that is mostly bitrotted. Here I have an updated version that you can
adapt for your own use.

## your wishlist

First, put all the books you want to read into a
[LibraryThing](https://librarything.com) collection; I'm using
LibraryThing because it has a
[very nice API](https://www.librarything.com/wiki/index.php/LibraryThing_JSON_Books_API)
that allows you to easily grab a list of your books in JSON format.

If you have books in an Amazon wishlist, you can manually extract the
ISBNs using
[this Amazon wishlist-to-JSON converter](https://github.com/doitlikejustin/amazon-wish-lister);
that will give you, in JSON format, a list of dictionaries, each
representing something in your wishlist. Each dictionary item has a
`link` key, and the ISBN can be extracted from that. See the function
`amazon_to_isbns()` in the Python file. You can paste a big list of
ISBNs into LibraryThing and it will import them all.

You can use some other wishlist service; the function `get_wishlist()`
can be adapted to work with anything so long as each book is represented
by a dictionary with keys `ISBN`, `title`, and `author_fl` (for "author
first last": William Shakespeare instead of Shakespeare, William).

## your library

Next you need a way to query your local library. The included code has
the Madison, Wisconsin public library hard-coded. (I live there.) The
`isbn_to_soup()` function takes an ISBN, looks up the book at the
library using a
[link like this one](https://www.linkcat.info/cgi-bin/koha/opac-search.pl?idx=isbn&q=9780062059888),
and returns the resulting book page, parsed with
[Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/). Then
`soup_to_libs()` parses that page to get a list of the branches with the
book and the status at each of them. Finally, `filter_and_sort_libs()`
filters out the branches where the book isn't available. You can use
that to sort the branches so that the closest one to you is listed
first, or whatever.

You'll need to figure out how to query your own library; Jon Udell's
[bookmarklet generator](http://jonudell.net/LibraryLookupGenerator.html)
has some links to common library software systems.

## the RSS feed

Finally, I use [feedgen](https://github.com/lkiesow/python-feedgen) to
make an RSS feed out of the data. You can publish it and view it in an
RSS reader.

## TODO

* LibraryThing has a
[ThingISBN](http://blog.librarything.com/thingology/2008/01/while-you-were-sleeping-thingisbn-got-better/)
service that returns a list of related ISBNs, which could be used to
make querying your local library more robust; however, I think my
library does that on their end already.

* output in Markdown format (which could be piped through
  [pandoc](http://pandoc.org/) to create HTML).
