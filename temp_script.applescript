
    tell application "Music"
        set artData to data of artwork 1 of current track
    end tell
    set outputFile to (POSIX path of (path to home folder)) & "cover.jpg"
    set fileRef to open for access outputFile with write permission
    set eof fileRef to 0
    write artData to fileRef
    close access fileRef
    