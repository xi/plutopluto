1.2.0 (2915-12-24)
------------------

-   Fix python3 support
-   Add ``--version`` flag


1.1.0
-----

-   Adapt to changed youtube API.
-   Search for config in more places, e.g. ``~/.plutopluto.cfg``.


1.0.2
-----

Changes
```````

-   The full post title is now included as `title` attribute on the source
    link.
-   On parse error, the server part returns a 500 status instead of an empty
    object.  Also, less parse errors sould occur.

Bugs
````

-   Fix visited link color.
-   Feeds that do not provide timestamps will be shown in the right order.
    This is accomplished by useing current time for each item and subtracting
    n seconds from the nth entry.


1.0.1
-----

Bugs
````

-   Change to python package to fix installation.


1.0.0
-----

JavaScript/python rewrite.


0.0.0
-----

Initial PHP implementation.
