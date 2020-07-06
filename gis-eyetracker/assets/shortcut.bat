!macro FileWriteHexBytes h b
push ${h}
push ${b}
call FileWriteHexBytes
!macroend
Function FileWriteHexBytes
exch $9
exch
exch $0
push $1
push $2
loop:
    StrCpy $2 $9 2
    StrLen $1 $2
    IntCmp $1 2 0 end
    FileWriteByte $0 "0x$2"
    StrCpy $9 $9 "" 2
    goto loop
end:
pop $2
pop $1
pop $0
pop $9
FunctionEnd


Function CreateRelativeLnk
exch $9
exch
exch $0
push $1
FileOpen $0 "$0" w
StrCmp $0 "" clean
!insertmacro FileWriteHexBytes $0 "4C0000000114020000000000C000000000000046"
!insertmacro FileWriteHexBytes $0 48010400 ;flags
!insertmacro FileWriteHexBytes $0 00000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000

StrLen $1 $9 ;must be < 255!
FileWriteByte $0 $1
FileWriteByte $0 0
FileWrite $0 "$9" ;relative target path

!if 0
;The icon is problematic, does not seem like it works with relative paths (but you can use system icons...)
StrCpy $9 "explorer.exe"
StrLen $1 $9
FileWriteByte $0 $1
FileWriteByte $0 0
FileWrite $0 "$9"
!else
!insertmacro FileWriteHexBytes $0 05003e2e657865 ;fake default .exe icon
!endif

clean:
FileClose $0
pop $1
pop $0
pop $9
FunctionEnd