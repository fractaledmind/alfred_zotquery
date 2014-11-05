(* Prepare Dialog Skeleton *)
property scpt_front : "
	try
		tell application (path to frontmost application as text)
	"
property scpt_middle : "
		end tell
	on error errText number errNum
		if not (errNum is equal to -128) then
			tell application id \"sevs\"
	"
property scpt_end : "
			end tell
		else
			return missing value
		end if
	end try
	"


(* USER-INTERACTION HELPER FUNCTIONS *)

on display_dialog(rec)
	(* Displays a dialog containing a message, one to three buttons, and optionally an icon and a ﬁeld in which the user can enter text.
	Syntax: key || class || status
		z_text || text || required
		z_answer || text || optional
		z_hidden || boolean || optional
		z_buttons || list || optional
		z_ok || labelSpecifier || optional
		z_cancel || labelSpecifier || optional
		z_title || text || optional
		z_icon || resourceSpecifier || optional
		z_icon || iconTypeSpecifier || optional
		z_icon || fileSpecifier || optional
		z_wait || integer || optional	
	
	Result: A record containing the button clicked and text entered, if any. For example {text returned:"Cupertino", button returned:"OK"}. If the dialog does not allow text input, there is no text returned item in the returned record. If the user clicks the specified cancel button, the script fails silently. If the display dialog command specifies a giving up after value, and the dialog is dismissed due to timing out before the user clicks a button, it returns a record indicating that no button was returned and the command gave up: {button returned:"", gave up:true}.
	*)
	
	(* Build display dialog script, adding optional variables *)
	--The dialog text, which is displayed in emphasized system font.
	set scpt to "display dialog \"" & (z_text of rec) & "\""
	--The initial contents of an editable text field. This edit field is not present unless this parameter is present; to have the field present but blank, specify an empty string: default answer ""
	try
		set scpt to scpt & space & "default answer \"" & (z_answer of rec) & "\""
	end try
	--If true, any text in the edit field is obscured as in a password dialog: each character is displayed as a bullet.
	try
		set scpt to scpt & space & "hidden answer " & (z_hidden of rec)
	end try
	--A list of up to three button names.
	try
		set b to my stringify_list(z_buttons of rec)
		set scpt to scpt & space & "buttons " & b
	end try
	--The name or number of the default button. This button is highlighted, and will be pressed if the user presses the Return or Enter key.
	try
		if class of z_ok of rec = text then
			set scpt to scpt & space & "default button \"" & (z_ok of rec) & "\""
		else if class of z_ok of rec = integer then
			set scpt to scpt & space & "default button " & (z_ok of rec)
		end if
	end try
	--The name or number of the cancel button. This button will be pressed if the user presses the Escape key or Command-period.
	try
		if class of z_cancel of rec = text then
			set scpt to scpt & space & "cancel button \"" & (z_cancel of rec) & "\""
		else if class of z_cancel of rec = integer then
			set scpt to scpt & space & "cancel button " & (z_cancel of rec)
		end if
	end try
	--The dialog window title.
	try
		set scpt to scpt & space & "with title \"" & (z_title of rec) & "\""
	end try
	--The type of icon to show (either stop, note, or caution), or an alias or file specifier
	try
		if (z_icon of rec) contains "/" then
			set icon_ to "POSIX file \"" & (z_icon of rec) & "\" as alias"
			try
				run script icon_
				set scpt to scpt & space & "with icon " & (icon_)
			end try
		else if (z_icon of rec) contains ":" then
			set icon_ to "\"" & (z_icon of rec) & "\" as alias"
			try
				run script icon_
				set scpt to scpt & space & "with icon " & (icon_)
			end try
		else
			set icon_ to (z_icon of rec)
			try
				run script icon_
				set scpt to scpt & space & "with icon " & (icon_)
			end try
		end if
	end try
	--The number of seconds to wait before automatically dismissing the dialog.
	try
		set scpt to scpt & space & "giving up after " & (z_wait of rec)
	end try
	
	(* Run the compiled script *)
	run script scpt_front & scpt & scpt_middle & scpt & scpt_end
	--return scpt
end display_dialog


on choose_from_list(rec)
	(* Allows the user to choose items from a list.

	Syntax: key || class || status
		z_list || list || required
		z_title || text || optional
		z_prompt || text || optional
		z_def || list || optional
		z_ok || text || optional
		z_cancel || text || optional
		z_multiple || boolean || optional
		z_empty || boolean || optional
		
	Result: If the user clicks the OK button, returns a list of the chosen number and/or text items; if empty selection is allowed and nothing is selected, returns an empty list ({}). If the user clicks the Cancel button, returns false.
 	*)
	
	(* Build choose from list script, adding optional variables *)
	--A list of numbers and/or text objects for the user to choose from.
	set l to my stringify_list(z_list of rec)
	set scpt to "choose from list " & l
	--Title text for the dialog.
	try
		set scpt to scpt & space & "with title \"" & (z_title of rec) & "\""
	end try
	--The prompt to be displayed in the dialog.
	try
		set scpt to scpt & space & "with prompt \"" & (z_prompt of rec) & "\""
	end try
	--A list of numbers and/or text objects to be initially selected. The list cannot include multiple items unless you also specify multiple selections allowed true. If an item in the default items list is not in the list to choose from, it is ignored.
	try
		if class of z_def of rec = list then
			set l to my stringify_list(z_def of rec)
			set scpt to scpt & space & "default items " & l
		else if class of z_def of rec = text then
			set scpt to scpt & space & "default items {\"" & (z_def of rec) & "\"}"
		else if class of z_def of rec = integer then
			set scpt to scpt & space & "default items item " & (z_def of rec) & "of " & l
		end if
	end try
	--The name of the OK button.
	try
		set scpt to scpt & space & "OK button name \"" & (z_ok of rec) & "\""
	end try
	--The name of the Cancel button.
	try
		set scpt to scpt & space & "cancel button name \"" & (z_cancel of rec) & "\""
	end try
	--Allow multiple items to be selected?
	try
		set scpt to scpt & space & "multiple selections allowed " & (z_multiple of rec)
	end try
	--Allow the user to choose OK with no items selected? If false, the OK button will not be enabled unless at least one item is selected.
	try
		set scpt to scpt & space & "empty selection allowed " & (z_empty of rec)
	end try
	
	(* Run the compiled script *)
	run script scpt_front & scpt & scpt_middle & scpt & scpt_end
	--return scpt
end choose_from_list


on choose_file(rec)
	(* Allows the user to choose a file.

	Syntax: key || class || status
		z_prompt || text || optional
		z_types || list of text || optional
		z_def || alias || optional
		z_invisibles || boolean || optional
		z_multiple || boolean || optional
		z_package || boolean || optional
		
	Result: The selected file, as an alias. If multiple selections are allowed, returns a list containing one alias for each selected file, if any. If the user clicks the cancel button, the script fails silently.
	*)
	
	(* Build choose from list script, adding optional variables *)
	set scpt to "choose file"
	--The prompt to be displayed in the dialog.
	try
		set scpt to scpt & space & "with prompt \"" & (z_prompt of rec) & "\""
	end try
	--A list of Uniform Type Identifiers (UTIs); for example, {"public.html", "public.rtf"}. Only files of the specified types will be selectable. For a list of system-defined UTIs, see Uniform Type Identifiers Overview. To get the UTI for a particular file, use info for.
	try
		set l to my stringify_list(z_types of rec)
		set scpt to scpt & space & "of type " & l
	end try
	--The folder to begin browsing in.
	try
		if (z_def of rec) contains "/" then
			set def_ to "POSIX file \"" & (z_def of rec) & "\" as alias"
			try
				run script def_
				set scpt to scpt & space & "default location " & (def_)
			end try
		else if (z_def of rec) contains ":" then
			set def_ to "\"" & (z_def of rec) & "\" as alias"
			try
				run script def_
				set scpt to scpt & space & "default location " & (def_)
			end try
		else if (z_def of rec) is "" then
			
		else
			set def_ to (z_def of rec)
			try
				run script def_
				set scpt to scpt & space & "default location " & (def_)
			end try
		end if
	end try
	--Show invisible files and folders?
	try
		set scpt to scpt & space & "invisibles " & (z_invisibles of rec)
	end try
	--Allow multiple items to be selected? If true, the results will be returned in a list, even if there is exactly one item.
	try
		set scpt to scpt & space & "multiple selections allowed " & (z_multiple of rec)
	end try
	--Show the contents of packages? If true, packages are treated as folders, so that the user can choose a file inside a package (such as an application).
	try
		set scpt to scpt & space & "showing package contents " & (z_package of rec)
	end try
	
	(* Run the compiled script *)
	set res to (run script scpt_front & scpt & scpt_middle & scpt & scpt_end)
	try
		if (count of res) > 1 then
			set l to {}
			repeat with i from 1 to count of res
				copy (POSIX path of (item i of res)) to end of l
			end repeat
			return l
		else
			return POSIX path of res
		end if
	on error
		try
			return POSIX path of res
		on error
			return res
		end try
	end try
end choose_file


on display_notification(rec)
	(* 
	Posts a notification using the Notification Center, containing a title, subtitle, and explanation, and optionally playing a sound.

	Syntax: key || class || status
		z_notification || text || required
		z_title || text || optional
		z_subtitle || text || optional
		z_sound || text || optional
		
	Result: None.
	*)
	
	(* Build choose from list script, adding optional variables *)
	--The body text of the notification. At least one of this and the title must be specified.
	set scpt to "display notification \"" & (z_notification of rec) & "\""
	--The title of the notification. At least one of this and the body text must be specified.
	try
		set scpt to scpt & space & "with title \"" & (z_title of rec) & "\""
	end try
	--The subtitle of the notification.
	try
		set scpt to scpt & space & "subtitle \"" & (z_subtitle of rec) & "\""
	end try
	--The name of a sound to play when the notification appears. This may be the base name of any sound installed in Library/Sounds.
	try
		set scpt to scpt & space & "sound name \"" & (z_sound of rec) & "\""
	end try
	
	(* Run the compiled script *)
	run script scpt_front & scpt & scpt_middle & scpt & scpt_end
	--return scpt
end display_notification


on choose_folder(rec)
	(*  
	Allows the user to choose a directory, such as a folder or a disk.

	Syntax: key || class || status
		z_prompt || text || optional
		z_def || alias || optional
		z_invisibles || boolean || optional
		z_multiple || boolean || optional
		z_package || boolean || optional
		
	Result: The selected directory, as an alias. If multiple selections are allowed, returns a list containing one alias for each selected directory, if any. If the user clicks the cancel button, the script fails silently.
	*)
	
	(* Build choose from list script, adding optional variables *)
	set scpt to "choose folder"
	--The prompt to be displayed in the dialog.
	try
		set scpt to scpt & space & "with prompt \"" & (z_prompt of rec) & "\""
	end try
	--The folder to begin browsing in.
	try
		if (z_def of rec) contains "/" then
			set def_ to "POSIX file \"" & (z_def of rec) & "\" as alias"
			try
				run script def_
				set scpt to scpt & space & "default location " & (def_)
			end try
		else if (z_def of rec) contains ":" then
			set def_ to "\"" & (z_def of rec) & "\" as alias"
			try
				run script def_
				set scpt to scpt & space & "default location " & (def_)
			end try
		else if (z_def of rec) is "" then
			
		else
			set def_ to (z_def of rec)
			try
				run script def_
				set scpt to scpt & space & "default location " & (def_)
			end try
		end if
	end try
	--Show invisible files and folders?
	try
		set scpt to scpt & space & "invisibles " & (z_invisibles of rec)
	end try
	--Allow multiple items to be selected? If true, the results will be returned in a list, even if there is exactly one item.
	try
		set scpt to scpt & space & "multiple selections allowed " & (z_multiple of rec)
	end try
	--Show the contents of packages? If true, packages are treated as folders, so that the user can choose a file inside a package (such as an application).
	try
		set scpt to scpt & space & "showing package contents " & (z_package of rec)
	end try
	
	(* Run the compiled script *)
	set res to (run script scpt_front & scpt & scpt_middle & scpt & scpt_end)
	try
		if (count of res) > 1 then
			set l to {}
			repeat with i from 1 to count of res
				copy (POSIX path of (item i of res)) to end of l
			end repeat
			return l
		else
			return POSIX path of res
		end if
	on error
		try
			return POSIX path of res
		on error
			return res
		end try
	end try
end choose_folder


on display_alert(rec)
	(*  
	Displays a standardized alert containing a message, explanation, and from one to three buttons.

	Syntax: key || class || status
		z_display || text || required
		z_message || text || optional
		z_as || alertType || optional
		z_buttons || list || optional
		z_ok || buttonSpecifier || optional
		z_cancel || buttonSpecifier || optional
		z_wait || integer	 || optional
		
	Result: If the user clicks a button that was not specified as the cancel button, display alert returns a record that identifies the button that was clicked—for example, {button returned: "OK"}. If the command specifies a giving up after value, the record will also contain a gave up:false item. If the display alert command specifies a giving up after value, and the dialog is dismissed due to timing out before the user clicks a button, the command returns a record indicating that no button was returned and the command gave up: {button returned:"", gave up:true} If the user clicks the specified cancel button, the script fails silently.
	*)
	
	(* Build choose from list script, adding optional variables *)
	--The alert text, which is displayed in emphasized system font.
	set scpt to "display alert \"" & (z_display of rec) & "\""
	--An explanatory message, which is displayed in small system font, below the alert text.
	try
		set scpt to scpt & space & "message \"" & (z_message of rec) & "\""
	end try
	--The type of alert to show. You can specify one of the following alert types:
	--informational: the standard alert dialog
	--warning: the alert dialog dialog is badged with a warning icon
	--critical: currently the same as the standard alert dialog
	try
		set scpt to scpt & space & "as " & (z_as of rec)
	end try
	--A list of up to three button names. If you supply one name, a button with that name serves as the default and is displayed on the right side of the alert dialog. If you supply two names, two buttons are displayed on the right, with the second serving as the default button. If you supply three names, the first is displayed on the left, and the next two on the right, as in the case with two buttons.
	try
		set l to my stringify_list(z_buttons of rec)
		set scpt to scpt & space & "buttons " & l
	end try
	--The name or number of the default button. This may be the same as the cancel button.
	try
		if class of z_ok of rec = text then
			set scpt to scpt & space & "default button \"" & (z_ok of rec) & "\""
		else if class of z_ok of rec = integer then
			set scpt to scpt & space & "default button " & (z_ok of rec)
		end if
	end try
	--The name or number of the cancel button. See “Result” below. This may be the same as the default button.
	try
		if class of z_cancel of rec = text then
			set scpt to scpt & space & "cancel button \"" & (z_cancel of rec) & "\""
		else if class of z_cancel of rec = integer then
			set scpt to scpt & space & "cancel button " & (z_cancel of rec)
		end if
	end try
	--The number of seconds to wait before automatically dismissing the alert.
	try
		set scpt to scpt & space & "giving up after " & (z_wait of rec)
	end try
	
	(* Run the compiled script *)
	run script scpt_front & scpt & scpt_middle & scpt & scpt_end
	--return scpt
end display_alert


on say_text(rec)
	(*  
	Speaks the specified text.

	Syntax:
		z_say || text || required
		z_display || text || optional
		z_use || text || optional
		z_waiting || boolean || optional
		z_save || fileSpecifier || optional
		
	Result: None.
	*)
	
	(* Build choose from list script, adding optional variables *)
	--The text to speak.
	set scpt to "say \"" & (z_say of rec) & "\""
	--The text to display in the feedback window, if different from the spoken text. This parameter is ignored unless Speech Recognition is turned on (in System Preferences).
	try
		set scpt to scpt & space & "displaying \"" & (z_display of rec) & "\""
	end try
	--The voice to speak with—for example: "Zarvox". You can use any of the voices from the System Voice pop-up on the Text to Speech tab in the Speech preferences pane.
	try
		set scpt to scpt & space & "using \"" & (z_use of rec) & "\""
	end try
	--Should the command wait for speech to complete before returning? This parameter is ignored unless Speech Recognition is turned on (in System Preferences).
	try
		set scpt to scpt & space & "waiting until completion " & (z_waiting of rec)
	end try
	--An alias or file specifier to an AIFF file (existing or not) to contain the sound output. You can only use an alias specifier if the file exists. If this parameter is specified, the sound is not played audibly, only saved to the file.
	try
		if (z_save of rec) contains "/" then
			set def_ to "POSIX file \"" & (z_save of rec) & "\" as alias"
		else if (z_save of rec) contains ":" then
			set def_ to "\"" & (z_save of rec) & "\" as alias"
		else
			set def_ to (z_save of rec)
		end if
		set scpt to scpt & space & "saving to " & (def_)
	end try
	
	(* Run the compiled script *)
	run script scpt_front & scpt & scpt_middle & scpt & scpt_end
	--return scpt
end say_text


(* HANDLERS *)

on stringify_list(l)
	repeat with i from 1 to count of l
		set item i of l to ("\"" & (item i of l) & "\"")
	end repeat
	set l to my implode(", ", l)
	set l to "{" & l & "}"
	return l
end stringify_list

(* SUB-ROUTINES *)

on implode(delimiter, pieces)
	local delimiter, pieces, ASTID
	set ASTID to AppleScript's text item delimiters
	try
		set AppleScript's text item delimiters to delimiter
		set pieces to "" & pieces
		set AppleScript's text item delimiters to ASTID
		return pieces --> text
	on error eMsg number eNum
		set AppleScript's text item delimiters to ASTID
		error "Can't implode: " & eMsg number eNum
	end try
end implode