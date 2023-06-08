$Remove = 'C:\Python27\Scripts;'
$env:Path = ($env:Path.Split(';') | Where-Object -FilterScript {$_ -ne $Remove}) -join ';'
$Remove = 'C:\Python27\;'
$env:Path = ($env:Path.Split(';') | Where-Object -FilterScript {$_ -ne $Remove}) -join ';'
