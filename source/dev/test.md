PATH:

+ search
    * general
    * titles
    * creators
    * attachments
    * notes /
    * collections
    * tags /
    * in-collection
    * in-tag
    * new / TODO
    * debug
+ store
    * collection
    * tag
+ export
    * bib
    * citation
    * append /
    * group
+ open
    * item
    * attachment
+ config

TODO: implement smart citation caching:
    
    >Caching

    >For efficient usage of the API, clients should make conditional GET requests whenever possible. If If-Modified-Since-Version: <libraryVersion> is passed with a multi-object read request (e.g., /users/1/items) and data has not changed in the library since the specified version, the API will return 304 Not Modified. If If-Modified-Since-Version: <objectVersion> is passed with a single-object read request (e.g., /users/1/items/ABCD2345), a 304 Not Modified will be returned if the individual object has not changed.

    >While a conditional GET request that returns a 304 should be fast, some clients may wish or need to perform additional caching on their own, using stored data for a period of time before making subsequent conditional requests to the Zotero API. This makes particular sense when the underlying Zotero data is known not to change frequently or when the data will be accessed frequently. For example, a website that displayed a bibliography from a Zotero collection might cache the returned bibliography for an hour, after which time it would make another conditional request to the Zotero API. If the API returned a 304, the website would continue to display the cached bibliography for another hour before retrying. This would prevent the website from making a request to the Zotero API every time a user loaded a page.


Possible Preferences:

+ keep url/doi in citation
+ keep _italics_
+ MMD vs. Pandoc references


+ Authors [number of authors and characters]
    * %a00
+ Authors with initials [number of authors]
    * %A0
+ Authors or Editors [number of authors and characters]
    * %p00
+ Authors or Editors [number of authors]
    * %P0
+ Title [length]
    * %t0
+ Title [number of words]
    * %T0
+ Year [with century]
    * %Y
+ Year [without century]
    * %y
+ Month
    * %m
+ Keywords [number]
    * %k0
+ Arbitrary field [length]
    * %f{}0
+ Arbitrary field words [number]
    * %w{}[ ]0
+ Arbitrary field switch [length]
    * %s{}[][][]0
+ Acronym for arbitrary field
    * %c{}
+ BibTeX type
    * %f{BibTeX Type}
+ Arbitrary document info [length]
    * %i{}0
+ Unique lowercase letters [length]
    * %u0
+ Unique uppercase letters [length]
    * %U0
+ Unique number [length]
    * %n0
+ Escaped digit [0-9]
    * %0
+ Esccaped percent character (also [ or ])
    * %%