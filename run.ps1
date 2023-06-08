$Remove = 'C:\Python27\Scripts;'
$Path = ($env:Path.Split(';') | Where-Object -FilterScript {$_ -ne $Remove}) -join ';'
$Remove = 'C:\Python27\;'
$Path = ($Path.Split(';') | Where-Object -FilterScript {$_ -ne $Remove}) -join ';'

[Environment]::SetEnvironmentVariable('Path', $Path, 'User')

