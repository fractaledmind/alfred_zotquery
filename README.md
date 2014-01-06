ZotQuery

Search your Zotero data from the comfort of your keyboard. 

ZotQuery is an Alfred workflow that grants the user access to the data stored in their Zotero application. The Python scripts in this repo form all of the necessary components for this workflow. 

There are 2 main functions:

1. Search
2. Cache

Under `Search` there are 5 options:

1. General search
2. Title-specific search
3. Author-specific search
4. Tag-specific search
5. Collection-specific search

Note that all searches coerce both the query and the data into lowercase, so you can search using lowercase queries and still get matches. 

The `General` search is launched by the keyword `zot`. This will search your entire Zotero database for any use of the query provided. The search script is "loose," that is, it searches for matches of the query "in" the data not matches that "equal" the data. This means you can search half words, etc. 

The `Author` search is launched by `zot:a`. This search only queries the last names of the authors of your Zotero data. For example: `zot:a thomas` will return all the items that have an author (or editor, translator, etc.) with the last name "Thomas". 

The `Title` search is launched by `zot:t`. This search only queries the title fields of your Zotero data. For example: `zot:t examle` will return all of the items whose title contains the word "example". 

The final two searches (Tag and Collection) are two-step searches. In step-one, you search for a particular Tag or Collection; in step-two you search within that particular Tag or Collection for your query. 

The `Tag` search is launched by `z:tag`. This allows you to search through all of your Zotero tags. Once you select a tag, Alfred will automatically initiate the `zot:tag` search, which will search within that tag for your query. The `zot:tag` query functions just like the general `zot` query, except that it is limited to those items with the previously chosen tag. 

The `Collection` search is similar. It is launched by `z:col`, which begins a search for all of your Zotero collections. Once you choose a particular collection, Alfred will initiate the `zot:c` search, which will search within that particular collection. As above, the `zot:c` search functions just like the simple `zot` search. 

Finally, there is also the Caching function. All of the query scripts are querying a JSON cache of your Zotero database. This file is created and then updated with the keyword `z:cache`. This function will find your Zotero sqlite database, read its contents, and create a JSON cache of the pertinent information. Since it is directly reading your Zotero database, the Zotero app **must** be closed when you run this function. Otherwise, the database will be locked and unreadable. This provides the reason for separating the caching and the querying functions: if every query read the sqlite database, you could only use the Alfred workflow when the Zotero app was closed. Since the queries read the JSON cache instead, you can run the workflow in any environment. You must still, however, update the cache with the Zotero app closed. 


