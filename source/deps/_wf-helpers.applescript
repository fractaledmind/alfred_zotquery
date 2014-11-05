(*
Adapted Code from Ursan Razvan's qWorkflow libary ()

Along with some custom code for dealing with simple JSON settings files (no nesting)
*)

on get_path()
	set {tid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, "/"}
	set _path to (text items 1 thru -3 of (POSIX path of (path to me)) as string) & "/"
	set AppleScript's text item delimiters to tid
	
	if my q_is_empty(_path) then return missing value
	
	return _path
end get_path

on get_bundle()
	set _path to my get_path()
	set _infoPlist to _path & "info.plist"
	
	# if the 'info.plist' file exists, start reading it
	if my q_file_exists(_infoPlist) then
		tell application "System Events"
			tell property list file _infoPlist
				# initialize the bundle with the id from the 'info.plist' file
				set _bundle to value of property list item "bundleid" as text
				return _bundle
			end tell
		end tell
	else
		return missing value
	end if
end get_bundle


on init_paths()
	set _path to my get_path()
	set _home to POSIX path of (path to "cusr" as text)
	set _bundle to my get_bundle()
	
	# initialize the Cache and Data folders
	set _cache to (_home) & "Library/Caches/com.runningwithcrayons.Alfred-2/Workflow Data/" & (_bundle) & "/"
	set _storage to (_home) & "Library/Application Support/Alfred 2/Workflow Data/" & (_bundle) & "/"
	
	# create the Cache and Data folders if they don't exist
	if not my q_folder_exists(_cache) then
		do shell script "mkdir " & (quoted form of _cache)
	end if
	if not my q_folder_exists(_storage) then
		do shell script "mkdir " & (quoted form of _storage)
	end if
	return true
end init_paths


on get_cache()
	set _path to my get_path()
	set _home to POSIX path of (path to "cusr" as text)
	set _bundle to my get_bundle()
	set _cache to (_home) & "Library/Caches/com.runningwithcrayons.Alfred-2/Workflow Data/" & (_bundle) & "/"
	
	if my q_is_empty(_bundle) then return missing value
	if my q_is_empty(_cache) then return missing value
	
	return _cache
end get_cache


on get_storage()
	set _path to my get_path()
	set _home to POSIX path of (path to "cusr" as text)
	set _bundle to my get_bundle()
	set _storage to (_home) & "Library/Application Support/Alfred 2/Workflow Data/" & (_bundle) & "/"
	
	if my q_is_empty(_bundle) then return missing value
	if my q_is_empty(_storage) then return missing value
	
	return _storage
end get_storage


on get_home()
	set _home to POSIX path of (path to "cusr" as text)
	if my q_is_empty(_home) then return missing value
	
	return _home
end get_home


on mdfind(query)
	set output to do shell script "mdfind \"" & query & "\""
	return my q_split(output, return)
end mdfind


(* JSON *)

on read_json(json_, path_)
	if path_ = true then
		set the file_ to open for access file json_
		set json_ to (read file_)
		close access file_
	end if
	
	-- simplify JSON
	set {astid, AppleScript's text item delimiters} to {AppleScript's text item delimiters, {return & linefeed, return, linefeed, tab, character id 8233, character id 8232, ":", "\"", ",", "{", "}"}}
	set json_l to text items of json_
	set AppleScript's text item delimiters to astid
	
	-- remove empty items
	set itemsToDelete to {"", " ", "    ", "  ", " ", "        ", "      ", "   "}
	set cleanList to {}
	repeat with i from 1 to count json_l
		if {json_l's item i} is not in itemsToDelete then set cleanList's end to json_l's item i
	end repeat
	
	-- JSON keys to AS record
	set rec to my list2record(cleanList, "string")
	return rec
end read_json

on list2record(_list, val_type)
	set split_list to my deinterlaceList(_list)
	set _keys to item 1 of split_list
	set _vals to item 2 of split_list
	
	if (count _keys) = (count _vals) then
		set rec to {}
		repeat with i from 1 to count of _keys
			set _key to item i of _keys
			set _val to item i of _vals
			
			if val_type = "string" or "text" then
				set r to "set rec to {_" & _key & ":\"" & _val & "\"}"
			else if val_type = "integer" or "number" then
				set r to "set rec to {_" & _key & ":" & _val & "}"
			end if
			set r to run script r
			set rec to rec & r
		end repeat
		return rec
	end if
end list2record

on write_json(k_v, path_)
	set json to ""
	repeat with i from 1 to count k_v
		set kv to (item i of k_v)
		if i = 1 then
			set l to "{" & return & tab & "\"" & (item 1 of kv) & "\": \"" & (item 2 of kv) & "\","
			set json to json & l
		else if i > 1 and i < (count k_v) then
			set l to return & tab & "\"" & (item 1 of kv) & "\": \"" & (item 2 of kv) & "\","
			set json to json & l
		else if i = (count k_v) then
			set l to return & tab & "\"" & (item 1 of kv) & "\": \"" & (item 2 of kv) & "\"" & return & "}"
			set json to json & l
		end if
	end repeat
	
	---Write the data to the settings file
	try
		set the file_ to open for access file path_ with write permission
		set eof of file_ to 0
		write json to file_
		close access the file_
		return true
	on error
		return false
	end try
end write_json



(* HANDLERS *)

on deinterlaceList(lst)
	local lst
	try
		if lst's class is not list then error "not a list." number -1704
		script k
			property l : lst
			property l1 : {}
			property l2 : {}
		end script
		if (count k's l) mod 2 is not 0 then error "list is not an even length."
		repeat with i from 1 to count of k's l by 2
			set k's l1's end to k's l's item i
			set k's l2's end to k's l's item (i + 1)
		end repeat
		return {k's l1, k's l2}
	on error eMsg number eNum
		error "Can't deinterlaceList: " & eMsg number eNum
	end try
end deinterlaceList

### join text
on q_join(l, delim)
	if class of l is not list or l is missing value then return ""
	
	repeat with i from 1 to length of l
		if item i of l is missing value then
			set item i of l to ""
		end if
	end repeat
	
	set oldDelims to AppleScript's text item delimiters
	set AppleScript's text item delimiters to delim
	set output to l as text
	set AppleScript's text item delimiters to oldDelims
	return output
end q_join

### split text
on q_split(s, delim)
	set oldDelims to AppleScript's text item delimiters
	set AppleScript's text item delimiters to delim
	set output to text items of s
	set AppleScript's text item delimiters to oldDelims
	return output
end q_split

### handler to check if a file exists
on q_file_exists(theFile)
	if my q_path_exists(theFile) then
		tell application "System Events"
			return (class of (disk item theFile) is file)
		end tell
	end if
	return false
end q_file_exists

### handler to check if a folder exists
on q_folder_exists(theFolder)
	if my q_path_exists(theFolder) then
		tell application "System Events"
			return (class of (disk item theFolder) is folder)
		end tell
	end if
	return false
end q_folder_exists

### handler to check if a path exists
on q_path_exists(thePath)
	if thePath is missing value or my q_is_empty(thePath) then return false
	
	try
		if class of thePath is alias then return true
		if thePath contains ":" then
			alias thePath
			return true
		else if thePath contains "/" then
			POSIX file thePath as alias
			return true
		else
			return false
		end if
	on error msg
		return false
	end try
end q_path_exists

### checks if a value is empty
on q_is_empty(str)
	if str is missing value then return true
	return length of (my q_trim(str)) is 0
end q_is_empty

### removes white space surrounding a string
on q_trim(str)
	if class of str is not text or class of str is not string or str is missing value then return str
	if str is "" then return str
	
	repeat while str begins with " "
		try
			set str to items 2 thru -1 of str as text
		on error msg
			return ""
		end try
	end repeat
	repeat while str ends with " "
		try
			set str to items 1 thru -2 of str as text
		on error
			return ""
		end try
	end repeat
	
	return str
end q_trim

### filters "missing value" from a list recursively
on q_clean_list(lst)
	if lst is missing value or class of lst is not list then return lst
	set l to {}
	repeat with lRef in lst
		set i to contents of lRef
		if i is not missing value then
			if class of i is not list then
				set end of l to i
			else if class of i is list then
				set end of l to my q_clean_list(i)
			end if
		end if
	end repeat
	return l
end q_clean_list

### encodes invalid XML characters
on q_encode(str)
	if class of str is not text or my q_is_empty(str) then return str
	set s to ""
	repeat with sRef in str
		set c to contents of sRef
		if c is in {"&", "'", "\"", "<", ">", tab} then
			if c is "&" then
				set s to s & "&amp;"
			else if c is "'" then
				set s to s & "&apos;"
			else if c is "\"" then
				set s to s & "&quot;"
			else if c is "<" then
				set s to s & "&lt;"
			else if c is ">" then
				set s to s & "&gt;"
			else if c is tab then
				set s to s & "&#009;"
			end if
		else
			set s to s & c
		end if
	end repeat
	return s
end q_encode

### encodes a native AppleScript date to Unix formatted date
on q_date_to_unixdate(theDate)
	set {day:d, year:y, time:t} to theDate
	
	copy theDate to b
	set b's month to January
	set m to (b - 2500000 - theDate) div -2500000
	
	tell (y * 10000 + m * 100 + d) as text
		set UnixDate to text 5 thru 6 & "/" & text 7 thru 8 & "/" & text 1 thru 4
	end tell
	
	set h24 to t div hours
	set h12 to (h24 + 11) mod 12 + 1
	if (h12 = h24) then
		set ampm to " AM"
	else
		set ampm to " PM"
	end if
	set min to t mod hours div minutes
	set s to t mod minutes
	
	tell (1000000 + h12 * 10000 + min * 100 + s) as text
		set UnixTime to text 2 thru 3 & ":" & text 4 thru 5 & ":" & text 6 thru 7 & ampm
	end tell
	
	return UnixDate & " " & UnixTime
end q_date_to_unixdate

### decodes a Unix date to a native AppleScript date
on q_unixdate_to_date(theUnixDate)
	return date theUnixDate
end q_unixdate_to_date

### decodes a Unix epoch timestamp to a native AppleScript date
on q_timestamp_to_date(timestamp)
	if length of timestamp = 13 then
		set timestamp to characters 1 thru -4 of timestamp as text
	end if
	
	set h to do shell script "date -r " & timestamp & " \"+%Y %m %d %H %M %S\""
	
	set mydate to current date
	set year of mydate to (word 1 of h as integer)
	set month of mydate to (word 2 of h as integer)
	set day of mydate to (word 3 of h as integer)
	set hours of mydate to (word 4 of h as integer)
	set minutes of mydate to (word 5 of h as integer)
	set seconds of mydate to (word 6 of h as integer)
	
	return mydate
end q_timestamp_to_date

### encodes a native AppleScript date to a Unix epoch timestamp
on q_date_to_timestamp(theDate)
	return ((current date) - (date ("1/1/1970")) - (time to GMT)) as miles as text
end q_date_to_timestamp

### handlers to show notifications in the Notification Center
on q_send_notification(theMessage, theDetails, theExtra)
	set _path to do shell script "pwd"
	#set _path to "/Users/woofy/Dropbox/work/Public Scripts/old/Alfred"
	if _path does not end with "/" then set _path to _path & "/"
	
	if theMessage is missing value then set theMessage to ""
	if theDetails is missing value then set theDetails to ""
	if theExtra is missing value then set theExtra to ""
	
	if my q_trim(theMessage) is "" and my q_trim(theExtra) is "" then set theMessage to "notification"
	
	try
		do shell script (quoted form of _path & "bin/q_notifier.helper com.runningwithcrayons.Alfred-2 " & quoted form of theMessage & " " & quoted form of theDetails & " " & quoted form of theExtra)
	end try
end q_send_notification
on q_notify()
	my q_send_notification("", "", "")
end q_notify

### encode a URL
on q_encode_url(str)
	local str
	try
		return (do shell script "/bin/echo " & quoted form of str & " | perl -MURI::Escape -lne 'print uri_escape($_)'")
	on error
		return missing value
	end try
end q_encode_url

### decode a URL
on q_decode_url(str)
	local str
	try
		return (do shell script "/bin/echo " & quoted form of str & " | perl -MURI::Escape -lne 'print uri_unescape($_)'")
	on error
		return missing value
	end try
end q_decode_url