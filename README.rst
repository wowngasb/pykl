PYKL
====

PYKL is the kltool for python, toolset for web, http, cache, dht, xml, json and so on.

Install it typing in your console:

.. code:: bash

    pip install pykl


Usage
-----

You can either do ``pykl --test`` to start a test server for testing
queries or

.. code:: bash

    pykl QUERY_FILE

This command will write in the standard output (or other output if
specified via ``--output``) the resulting JSON.

Your ``QUERY_FILE`` could look similar to this:

.. code::

    {
      page(url:"http://news.ycombinator.com") {
        items: query(selector:"tr.athing") {
          rank: text(selector:"td span.rank")
          title: text(selector:"td.title a")
          sitebit: text(selector:"span.comhead a")
          url: attr(selector:"td.title a", name:"href")
          attrs: next {
             score: text(selector:"span.score")
             user: text(selector:"a:eq(0)")
             comments: text(selector:"a:eq(2)")
          }
        }
      }
    }

Advanced usage
--------------

If you want to generalize your pykl query to any page, just rewrite your
query file adding the ``$page`` var. So should look to something like
this:

.. code::

    query ($page: String) {
      page(url:$page) {
        # ...
      }
    }

And then, query it like:

.. code:: bash

    pykl QUERY_FILE http://news.ycombinator.com
