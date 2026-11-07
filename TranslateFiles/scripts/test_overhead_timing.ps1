param([Parameter(Mandatory=$true)][string]$PatchedAssembly)
$ErrorActionPreference='Stop'
# Run only the new standalone arithmetic helper, never the game or its UI.
$assembly=[Reflection.Assembly]::LoadFile((Resolve-Path $PatchedAssembly).Path)
$method=$assembly.GetType('ZFY.OverheadTiming').GetMethod('GetDisplaySeconds')
$cases=@(
    @('Hello world.',0.4,0.4),
    @('',0.2,0.2),
    @('你好。',0.2,3.0),
    @(('中'*30),0.2,6.0),
    @(('中'*60),0.2,12.0),
    @('<color="中文颜色">Hello</color>',0.2,0.2),
    @(('<color="#ff0000">'+('中'*30)+'</color>'),0.2,6.0),
    @('你好 World',8.0,8.0),
    @('一锅兔肉炖菜在火坑上咕嘟作响，诱人的香味弥漫了整间长屋。',0.2,5.2)
)
$results=@()
foreach($case in $cases){
    $actual=$method.Invoke($null,@([single]$case[1],[string]$case[0]))
    if([Math]::Abs($actual-$case[2]) -gt 0.001){throw "Unexpected seconds $actual expected $($case[2])"}
    $results+=@{text=$case[0];original_seconds=$case[1];patched_seconds=$actual}
}
$results | ConvertTo-Json -Depth 5
