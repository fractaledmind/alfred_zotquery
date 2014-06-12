on run argv
	
	--Load the script with the UI Helper Functions
	set ui to load script POSIX file (POSIX path of ((path to me as text) & "::") & "_ui-helpers.scpt")
	set wf to load script POSIX file (POSIX path of ((path to me as text) & "::") & "_wf-helpers.scpt")
	
	--- Set the path to the preferences file
	set path_ to (path to "cusr" as text) & "Library:Application Support:Alfred 2:Workflow Data:com.hackademic.zotquery:prefs.json" as text
	
	try
		set rec to wf's read_json(path_, true)
		
		try
			set format_pref to rec's _format
			set csl_pref to rec's _csl
			set client_pref to rec's _client
		on error
			set format_pref to "Markdown"
			set csl_pref to "chicago-author-date"
			set client_pref to "Standalone"
		end try
	on error
		set format_pref to "Markdown"
		set csl_pref to "chicago-author-date"
		set client_pref to "Standalone"
	end try
	
	--Export style
	ui's choose_from_list({z_list:{"chicago-author-date", "apa", "modern-language-association", "rtf-scan", "bibtex", "odt-scannable-cites"}, z_title:"ZotQuery Preferences", z_prompt:"Use which CSL style?", z_def:{csl_pref}})
	set csl_pref to item 1 of result
	
	-- Export format
	ui's choose_from_list({z_list:{"Markdown", "Rich Text"}, z_title:"ZotQuery Preferences", z_prompt:"Export citations and references in which text format?", z_def:{format_pref}})
	set format_pref to item 1 of result
	
	--Zotero client
	ui's choose_from_list({z_list:{"Standalone", "Firefox"}, z_title:"ZotQuery Preferences", z_prompt:"Which Zotero client should ZotQuery use?", z_def:{client_pref}})
	set client_pref to item 1 of result
	
	try
		wf's write_json({{"format", format_pref}, {"csl", csl_pref}, {"client", client_pref}}, path_)
		return "Export Settings Saved!"
	on error msg
		return msg
	end try
end run

on get_icon()
	set {tid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, "/"}
	set dir_ to text items 1 thru -2 of (POSIX path of (path to me)) as string
	set AppleScript's text item delimiters to tid
	set icon_ to (dir_ & "/icon.png")
	return icon_
end get_icon