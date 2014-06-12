on run argv
	set wf to load script POSIX file (POSIX path of ((path to me as text) & "::") & "_wf-helpers.scpt")
	
	--- set the path to the settings file
	set path_ to (path to "cusr" as text) & "Library:Application Support:Alfred 2:Workflow Data:com.hackademic.zotquery:settings.json" as text
	
	try
		set rec to wf's read_json(path_, true)
		
		try
			set id_ to rec's _user_id
			set key_ to rec's _api_key
		on error
			set id_ to ""
			set key_ to ""
		end try
	on error
		set id_ to ""
		set key_ to ""
	end try
	
	--- Get the user id
	try
		set check_id to true
		repeat while check_id
			set id_ to getID(id_) as string
			if id_ is not equal to "again" then
				set check_id to false
			end if
		end repeat
	on error msg
		return msg
	end try
	
	--- Get the api_key
	try
		set check_key to true
		repeat while check_key
			set key_ to getKey(key_)
			if key_ is not equal to "again" then
				set check_key to false
			end if
		end repeat
	on error msg
		return msg
	end try
	
	---Write the data to the settings file
	try
		wf's write_json({{"type", "user"}, {"user_id", id_}, {"api_key", key_}}, path_)
		return "Zotero API settings saved"
	on error msg
		return msg
	end try
end run

--- Function to get the user id
on getID(id_)
	--Load the script with the UI Helper Functions
	set ui to load script POSIX file (POSIX path of ((path to me as text) & "::") & "_ui-helpers.scpt")
	
	-- Prepare path to icon
	set {tid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, "/"}
	set dir_ to text items 1 thru -3 of (POSIX path of (path to me)) as string
	set AppleScript's text item delimiters to tid
	set icon_ to (dir_ & "/icon.png")
	
	set id_query to ui's display_dialog({z_text:"Please enter your User ID, a number with fewer than eight digits.", z_answer:id_, z_buttons:{"Cancel", "Where do I find my User ID?", "Set User ID"}, z_ok:3, z_cancel:1, z_title:"ZotQuery Configuration", z_icon:icon_})
	if button returned of the id_query is "Where do I find my User ID?" then
		open location "https://www.zotero.org/settings/keys"
		delay 2
		return "again"
	end if
	try
		set id_ to text returned of the id_query as number
		return id_
	on error
		set warn_ to ui's display_dialog({z_text:"The User ID is a number. Please enter a number.", z_buttons:{"Cancel", "Where do I find my User ID?", "Try Again"}, z_ok:3, z_cancel:1, z_title:"ZotQuery Configuration", z_icon:stop})
		if button returned of the warn_ is "Where do I find my User ID?" then
			open location "https://www.zotero.org/settings/keys"
			delay 2
			return "again"
		else if button returned of the warn_ is "Try Again" then
			return "again"
		end if
	end try
end getID

--- Function to get the user id
on getKey(key_)
	--Load the script with the UI Helper Functions
	set ui to load script POSIX file (POSIX path of ((path to me as text) & "::") & "_ui-helpers.scpt")
	
	-- Prepare path to icon
	set {tid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, "/"}
	set dir_ to text items 1 thru -3 of (POSIX path of (path to me)) as string
	set AppleScript's text item delimiters to tid
	set icon_ to (dir_ & "/icon.png")
	
	set api_query to ui's display_dialog({z_text:"Please enter your API key. It should be 24 characters.", z_answer:key_, z_buttons:{"Cancel", "Where do I find my key?", "Set Key"}, z_ok:3, z_cancel:1, z_title:"ZotQuery Configuration", z_icon:icon_})
	if button returned of the api_query is "Where do I find my key?" then
		open location "https://www.zotero.org/settings/keys"
		delay 2
		return "again"
	end if
	if (count of text items of text returned of the api_query) is not equal to 24 then
		set warn_ to ui's display_dialog({z_text:"The API Key is 24 characters, so please enter a 24-character string.", z_answer:key_, z_buttons:{"Cancel", "Where do I find my key?", "Try Again"}, z_ok:3, z_cancel:1, z_title:"ZotQuery Configuration", z_icon:stop})
		if button returned of the warn_ is "Where do I find my key?" then
			open location "https://www.zotero.org/settings/keys"
			delay 2
			return "again"
		else if button returned of the warn_ is "Try Again" then
			return "again"
		end if
	else
		return text returned of the api_query
	end if
end getKey