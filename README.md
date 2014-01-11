# ZotQuery

### Search your Zotero data from the comfort of your keyboard. 

**ZotQuery** is an Alfred workflow that grants the user access to the data stored in their Zotero application. The Python scripts in this repo form all of the necessary components for this workflow. 

To **download**, simply open the `ZotQuery.alfredworkflow` file, and then click `View Raw`. The file will then automatically download. All you need to do is open it and Alfred will import the workflow.

	NOTE: You need the PowerPack for Alfred v.2 for this workflow.

v. 2.2: New Fallback Search. Bug fixes and more error logging.
v. 2.0: Add ability to open attachments.   
v. 1.2: Various bug fixes. New Notifications.   
v. 1.1: Added feature to export bibliography of Collections or Tags.  
v. 1.0: Added features to export formatted citations and references of items.  
v. 0.9: Added new script filters.  
v. 0.8: First public release of ZotQuery.  

### REQUIREMENTS ###

This workflow utilizes the Zotero API to export citations of chosen items. In order for the user to utilize these functions, you must have and set up a Zotero private key. To do so, the user must sign into their Zotero account at [zotero.org](www.zotero.org) and go to the "Feeds/API" tab. Here you will find something like so:

![The API tab](/screenshots/Zotero___Settings___Feeds_API.png)

This shows a user who has two API keys set up, one for personal use and one for the iOS app [PaperShip](http://www.papershipapp.com/ "PaperShip - Manage, Annotate, and Share your Papers On The Go ..."). If you do not have a Personal API key, you can easily set one up by clicking the "Create new private key" link. 

Once you have set up a personal API key, you will need this key and the userID (Library ID) to set-up the ZotQuery workflow. The necessary steps are as follows:

* Open the workflow folder by going into the Alfred preferences, selecting any of the script in the ZotQuery workflow and pressing this button:

![Open workflow folder](/screenshots/Alfred_Preferences-5.png)

* Find the `setting.json` file:

![Find settings](/screenshots/find-settings.png)

* Open that file and replace the "user_id" and "api_key" values with the appropriate data:

![Modify settings](/screenshots/settings_json.png)

The workflow reads this `settings.json` file whenever it attempts to connect to the Zotero API, so if you don't alter it properly, the Export Citation and Export Reference functions **will not work**.

**ALSO**, when you first download the workflow, you will need to run `z:cache` first to cache your Zotero data before you attempt any queries. All of the queries query the JSON cache and not your Zotero data directly (for speed reasons) and the cache auto-updates after every query, but the first time out of the box requires a manual caching. (Note also that you can always force update the cache with the `z:cache` command, which may be helpful if you've added items to Zotero since your last query.)

- - -  

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

* The **General** search is launched by the keyword `zot`. 

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

* The **Author** search is launched by `zot:a`. This search only queries the last names of the authors of your Zotero data. For example: `zot:a thomas` will return all the items that have an author (or editor, translator, etc.) with the last name "Thomas". 

![An author-specific search](/screenshots/zotquery_author_search.png)

* The **Title** search is launched by `zot:t`. 

![A title-specific search](/screenshots/zotquery_title_init.png)

This search only queries the title fields of your Zotero data. For example: `zot:t examle` will return all of the items whose title contains the word "example". 

![Results of a title-specific search](/screenshots/zotquery_title_search.png)


The final two searches (Tag and Collection) are two-step searches. In step-one, you search for a particular Tag or Collection; in step-two you search within that particular Tag or Collection for your query. 

* The **Tag** search is launched by `z:tag`. 

![A tag-specific search](/screenshots/zotquery_tag_init.png)

This allows you to search through all of your Zotero tags. 

![A tag-specific search](/screenshots/zotquery_tag_search.png)

Once you select a tag, Alfred will automatically initiate the `zot:tag` search, which will search within that tag for your query. The `zot:tag` query functions just like the general `zot` query, except that it is limited to those items with the previously chosen tag. 

![Searching within a tag](/screenshots/zotquery_in-tag_search.png)

* The **Collection** search is similar. It is launched by `z:col`, which begins a search for all of your Zotero collections. 

![A collection-specific search](/screenshots/zotquery_collection_search.png)

Once you choose a particular collection, Alfred will initiate the `zot:c` search, which will search within that particular collection. 

![Searching within a tag](/screenshots/zotquery_in-collection_search.png)

As above, the `zot:c` search functions just like the simple `zot` search. 

**TIP**: Both the Tag and Collection searches save the chosen tag or collection to a cached file which the next step reads and searches within. If you use either tags or collections to organize your writing projects, you can search for that tag or collection once, and then simply jump straight to the `zot:tag` or `zot:c` search to continue searching within that tag or collection. 

- - - 
Under `Export` there are (now) 3 options:

1. Export an Item.
2. Export a Set of items.
3. Open an Attachment

The last one is the newest feature of ZotQuery!

When you perform any of the queries, items with attachments will have in their Subtitle "Attachments: `n`.", with n representing the number of .pdf or .epub attachments for that item:

![An item w/ an Attachment](/screenshots/attachment.png)

In order to open this attachment, simply press `shift+return.` If the attachment is a .pdf, it will be opened in your default pdf viewer; likewise for .epubs. This feature should work both for attachments in Zotero itself as well as linked attachments. 

Once you select an **individual item** after a `zot` search of any kind (general, author, title, tag, collection), there are 4 options:

1. Open Zotero to that item.
2. Export an author-date reference to that item.
3. Export a Markdown citation of that item.
4. Append a Markdown citation to a temporary bibliography.

* If you merely hit `return` on your chosen item, option 1 will occur and Zotero will open to that item.   
* If you hit `option+return` when you choose your item, you will export an author-date reference.   
* If you hit `control+return`, you will export a full citation of the item in Markdown format.  
* If you hit `fn+return`, you will append a full citation of the item in Markdown format to a cached bibliography text file. Once you have filled your bibliography, you can use the command `z:bib` to export the entire bibliography to the clipboard. 

This last export will order the citations in alphabetical order and place a WORKS CITED header at the top. It will then wipe and restart the `bibliography.txt` file. This feature allows you to dynamically build bibliographies for your papers without all of the fuss.

After you select either a Collection or a Tag after a `z:tag` or `z:col`, you have 2 options:

1. You can search within that Tag or Collection.
2. You can export a Markdown-formatted bibliography of all the items within that Tag or Collection

* To simply search within that Tag or Collection for a particular item, hit `return`.
* To export a Bibliography, hit `control+return`. When you hold down `control`, the subtitle of the item will change, letting you know that you have a different option.

![Export bib](/screenshots/export_bib_screenshot.png)

The exported Bibliography will be formatted in Markdown, and like the appended bibliography, it will automatically be alphabetically ordered and have a WORKS CITED header. A notification will let you know when the bibliography has been copied to the clipboard:

![Notification](/screenshots/copy_screenshot.png)

**TIP**: This feature comes in handy if you use either Collections or Tags to organize citations for particular writing projects. Once you feel you have all of the citations for a particular paper stored within a Collection or Tag, ZotQuery can create you bibliography for you. Using this feature in tandem with the `Export Reference` feature, you can easily generate and insert individual references and whole bibliographies into your papers. 

For reference, here's what a Markdown bibliography in Chicago (author-date) style would look like:

![Sample bib](/screenshots/WORKS_CITED.png)

These final three options use Zotero’s web API, and so they require an internet connection. If you are not connected to the internet, both will fail gracefully. 

The workflow defaults to Chicago (author-date) style. If you wish to use another of Zotero's CSL styles, you need merely change `style` key for the zot.item call in the action_export-md-format.py and the action_export-ref.py scripts. Here's what the code will look like and what you need to change:

![The code](/screenshots/action_export-ref_py-6.png)

- - -

Finally, there is also the Caching function. All of the query scripts are querying a JSON cache of your Zotero database. This file is created and then updated with the keyword `z:cache`. 

![Updating the cache](/screenshots/zotquery_cache.png)

This function will find your Zotero sqlite database, read its contents, and create a JSON cache of the pertinent information. 

Note, however, that current versions of the workflow will automatically update after each use of the workflow. This means, if you do a general `zot` search and select an item, once you are done, the workflow will automatically check if the cache is up-to-date, and if not, it will then update. This means that you won't likely have to manually update the cache, but if you ever feel like you do, the `z:cache` function will remain in the workflow.

- - - 

So that's all there is to it. If you are interested in certain feature requests, leave a comment and I will see if it is feasible or possible. 

Enjoy! 
