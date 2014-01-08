# ZotQuery

### Search your Zotero data from the comfort of your keyboard. 

**ZotQuery** is an Alfred workflow that grants the user access to the data stored in their Zotero application. The Python scripts in this repo form all of the necessary components for this workflow. 

### REQUIREMENTS ###

This workflow utilizes the Zotero API to export citations of chosen items. In order for the user to utilize these functions, they must have and set up a Zotero private key. To do so, the user must sign into their Zotero account at [zotero.org](www.zotero.org) and go to the "Feeds/API" tab. Here they will find something like so:

![The API tab](/screenshots/Zotero___Settings___Feeds_API.png)

This shows a user who has two API keys set up, one for personal use and one for the iOS app [PaperShip](http://www.papershipapp.com/ "PaperShip - Manage, Annotate, and Share your Papers On The Go ..."). If you do not have a Personal API key, you can easily set one up by clicking the "Create new private key" link. 

Once you have set up a personal api key, you will need this key and the userID (Library ID) to set-up the ZotQuery workflow. The necessary steps are as follows:

1. Open the workflow folder by going into the Alfred preferences, selecting any of the script in the ZotQuery workflow and pressing this button:

![Open workflow folder](/screenshots/Alfred_Preferences-5.png)

2. Find the `setting.json` file:

![Find settings](/screenshots/find-settings.png)

3. Open that file and replace the "user_id" and "api_key" values with the appropriate data:

![Modify settings](/screenshots/settings_json.png)

The workflow reads this `settings.json` file whenever it attempts to connect to the Zotero API, so if you don't alter it properly, the Export Citation and Export Reference functions will not work.


### FUNCTIONS

There are 3 main functions:

1. Search
2. Export
3. Cache

Under `Search` there are 5 options:

1. General search
2. Title-specific search
3. Author-specific search
4. Tag-specific search
5. Collection-specific search

Note that all searches coerce both the query and the data into lowercase, so you can search using lowercase queries and still get matches. 

The `General` search is launched by the keyword `zot`. 

![A general search](/screenshots/zotquery_init.png)

This will search your entire Zotero database for any use of the query provided. The search script is "loose," that is, it searches for matches of the query "in" the data not matches that "equal" the data. This means you can search half words, etc. 

![Searching...](/screenshots/zotquery_searching.png)

Once you complete your query, and the script catches up with you, you will see a list of all of your Zotero items that match the query. For ease of use, the workflow also provides unique icons for the various item types:

* article 
![article](/icons/n_article.png)
* book 
![book](/icons/n_book.png)
* chapter 
![chapter](/icons/n_chapter.png)
* conference paper
![conference](/icons/n_conference.png)
* etc. 
![others](/icons/n_written.png)

![A list of items](/screenshots/zotquery_zot.png)

When you select an item, Zotero will open to that item.

The `Author` search is launched by `zot:a`. This search only queries the last names of the authors of your Zotero data. For example: `zot:a thomas` will return all the items that have an author (or editor, translator, etc.) with the last name "Thomas". 

![An author-specific search](/screenshots/zotquery_author_search.png)

The `Title` search is launched by `zot:t`. 

![A title-specific search](/screenshots/zotquery_title_init.png)

This search only queries the title fields of your Zotero data. For example: `zot:t examle` will return all of the items whose title contains the word "example". 

![Results of a title-specific search](/screenshots/zotquery_title_search.png)


The final two searches (Tag and Collection) are two-step searches. In step-one, you search for a particular Tag or Collection; in step-two you search within that particular Tag or Collection for your query. 

The `Tag` search is launched by `z:tag`. 

![A tag-specific search](/screenshots/zotquery_tag_init.png)

This allows you to search through all of your Zotero tags. 

![A tag-specific search](/screenshots/zotquery_tag_search.png)

Once you select a tag, Alfred will automatically initiate the `zot:tag` search, which will search within that tag for your query. The `zot:tag` query functions just like the general `zot` query, except that it is limited to those items with the previously chosen tag. 

![Searching within a tag](/screenshots/zotquery_in-tag_search.png)

The `Collection` search is similar. It is launched by `z:col`, which begins a search for all of your Zotero collections. 

![A collection-specific search](/screenshots/zotquery_collection_search.png)

Once you choose a particular collection, Alfred will initiate the `zot:c` search, which will search within that particular collection. 

![Searching within a tag](/screenshots/zotquery_in-collection_search.png)

As above, the `zot:c` search functions just like the simple `zot` search. 

- - - 
Once you select an item, there are 3 options:

1. Open Zotero to that item.

2. Export an author-date reference to that item.

3. Export a Markdown citation of that item.


If you merely hit `return` on your chosen item, option 1 will occur and Zotero will open to that item. If you hit `option+return` when you choose your item, you will export an author-date reference. If you hit `control+return`, you will export a full citation of the item in Markdown format. 

The workflow defaults to Chicago (author-date) style. If you wish to use another of Zotero's CSL styles, you need merely change `style` key for the zot.item call in the action_export-md-format.py and the action_export-ref.py scripts. Here's what the code will look like and what you need to change:

![Updating the cache](/screenshots/action_export-ref_py-6.png)


- - -

Finally, there is also the Caching function. All of the query scripts are querying a JSON cache of your Zotero database. This file is created and then updated with the keyword `z:cache`. 

![Updating the cache](/screenshots/zotquery_cache.png)

This function will find your Zotero sqlite database, read its contents, and create a JSON cache of the pertinent information. 
