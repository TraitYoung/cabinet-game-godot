param()
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'assets/bina-live2d/source-measured'
function Write-Utf8Lf([string]$path, [string]$content) {
    [IO.File]::WriteAllText($path, ($content -replace "`r`n", "`n").TrimEnd() + "`n", [Text.UTF8Encoding]::new($false))
}
$measurePath = Join-Path $root 'assets/bina-tpose/measurements/proportions.json'
$measure = Get-Content -LiteralPath $measurePath -Raw | ConvertFrom-Json
$front = $measure.views.'casual-front'
$actualHash = (Get-FileHash -Algorithm SHA256 (Join-Path $root $front.source)).Hash.ToLowerInvariant()
if ($actualHash -ne $front.sha256) { throw 'Reference changed: remeasure before packaging.' }
New-Item -ItemType Directory -Force (Join-Path $out 'parts') | Out-Null

# Cut transparent atlas cells; no painting or reconstruction is performed here.
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
public static class BinaAtlas {
    public static Bitmap Cut(Bitmap atlas, Rectangle cell, bool trim) {
        Bitmap part = atlas.Clone(cell, PixelFormat.Format32bppArgb);
        int x0=part.Width, y0=part.Height, x1=-1, y1=-1;
        for (int y=0; y<part.Height; y++) for (int x=0; x<part.Width; x++) {
            Color c=part.GetPixel(x,y); if (c.A<200) part.SetPixel(x,y,Color.Transparent);
            // Ignore faint alpha spill when finding the painted part bounds.
            if (c.A>=200) { x0=Math.Min(x0,x); y0=Math.Min(y0,y); x1=Math.Max(x1,x); y1=Math.Max(y1,y); }
        }
        if(x1<x0) throw new Exception("Empty atlas cell");
        if(!trim) return part;
        Bitmap result=part.Clone(Rectangle.FromLTRB(x0,y0,x1+1,y1+1),PixelFormat.Format32bppArgb);
        part.Dispose(); return result;
    }
}
'@
$atlas = [System.Drawing.Bitmap]::new((Join-Path $out 'parts-atlas.png'))
$master = [System.Drawing.Bitmap]::new((Join-Path $out 'master-generated.png'))
$preview = [System.Drawing.Bitmap]::new(1536,1024)
$graphics = [System.Drawing.Graphics]::FromImage($preview)
$graphics.Clear([System.Drawing.Color]::Transparent)
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
# Each source part is scaled uniformly. Left/right here mean image coordinates,
# matching the measurement document. Pivot coordinates come from that document.
# Pixel crop bounds manually checked on the generated 1254-square atlas.
# Body crops retain the master reference geometry at 1:1 scale.
$spec = @(
    @('back_hair',@(30,20,275,300),'atlas',763.5,7,'width',173,@('hair','back')),
    @('leg_left',@(652,532,113,478),'master',708.5,532,'native',1,@('leg','right')),
    @('leg_right',@(766,532,112,478),'master',822,532,'native',1,@('leg','left')),
    @('skirt',@(647,486,234,55),'master',764,486,'native',1,@('skirt')),
    @('torso',@(303,174,924,334),'master',765,174,'native',1,@('top')),
    @('face',@(373,63,198,234),'atlas',765,48,'height',124,@('face')),
    @('eyewhite_left',@(90,438,145,75),'atlas',739,111,'width',28,@('eye','white','right')),
    @('eyewhite_right',@(400,438,145,75),'atlas',791,111,'width',28,@('eye','white','left')),
    @('iris_left',@(735,422,98,100),'atlas',742,111,'height',12,@('eye','iris','right')),
    @('iris_right',@(1049,422,98,100),'atlas',789,111,'height',12,@('eye','iris','left')),
    @('eyelash_left',@(77,726,170,93),'atlas',739,110,'width',30,@('eye','lash','right')),
    @('eyelash_right',@(390,726,170,93),'atlas',791,110,'width',30,@('eye','lash','left')),
    @('brow_left',@(648,754,115,40),'atlas',741,98,'width',28,@('brow','right')),
    @('brow_right',@(805,754,115,40),'atlas',790,98,'width',28,@('brow','left')),
    @('nose',@(1080,703,39,44),'atlas',765,135,'height',6,@('nose')),
    @('mouth',@(1047,784,110,47),'atlas',765,148,'width',22,@('mouth')),
    @('front_hair',@(644,22,282,293),'atlas',763.5,7,'width',173,@('hair','front')),
    @('glasses',@(985,111,225,140),'atlas',764,31,'width',105,@('headwear'))
)
$layers = @()
try {
    foreach ($entry in $spec) {
        $name,$bounds,$source,$cx,$top,$axis,$size,$tags = $entry
        $bitmap = if ($source -eq 'master') { $master } else { $atlas }
        $part=[BinaAtlas]::Cut($bitmap,[System.Drawing.Rectangle]::new($bounds[0],$bounds[1],$bounds[2],$bounds[3]),($source -ne 'master'))
        try {
            $part.Save((Join-Path $out "parts/$name.png"),[System.Drawing.Imaging.ImageFormat]::Png)
            $scale = if ($axis -eq 'native') { 1 } elseif ($axis -eq 'width') { $size/$part.Width } else { $size/$part.Height }
            $w=$part.Width*$scale; $h=$part.Height*$scale; $x=$cx-$w/2
            if ($x -lt 0 -or $top -lt 0 -or ($x+$w) -gt 1536 -or ($top+$h) -gt 1024) { throw "Layer outside canvas: $name" }
            $rect=[ordered]@{left=$x;top=$top;width=$w;height=$h}
            $layers += [ordered]@{id=$name;name=$name;tags=$tags;image=@{path="parts/$name.png";width=$part.Width;height=$part.Height};rect=$rect}
            $graphics.DrawImage($part,[System.Drawing.RectangleF]::new($x,$top,$w,$h))
        } finally { $part.Dispose() }
    }
    $layout=[ordered]@{format='psd2live-layout';version=1;name='bina-measured';canvas=@{width=1536;height=1024};layers=$layers}
    Write-Utf8Lf (Join-Path $out 'bina.layout.json') ($layout | ConvertTo-Json -Depth 12)
    $preview.Save((Join-Path $out 'assembled-preview.png'),[System.Drawing.Imaging.ImageFormat]::Png)
    $encoded=[Convert]::ToBase64String([IO.File]::ReadAllBytes((Join-Path $out 'assembled-preview.png')))
    $svg=@('<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" viewBox="0 0 1536 1024">',
        '<rect width="1536" height="1024" fill="#e9edf2"/>',
        "<image width=`"1536`" height=`"1024`" href=`"data:image/png;base64,$encoded`"/>")
    foreach ($point in $front.landmarks_px.PSObject.Properties) {
        if ($null -ne $point.Value) {
            $px=$point.Value[0]; $py=$point.Value[1]
            $svg += "<circle cx=`"$px`" cy=`"$py`" r=`"2`" fill=`"#f02060`"><title>$($point.Name) ($px,$py): reference target</title></circle>"
        }
    }
    $svg += '</svg>'
    Write-Utf8Lf (Join-Path $out 'measurement-overlay.svg') ($svg -join "`n")
    $report=[ordered]@{
        reference=$front.source;reference_sha256=$actualHash
        measurement_file='assets/bina-tpose/measurements/proportions.json'
        reference_scale=1;canvas=@(1536,1024);target_landmarks=$front.landmarks_px;target_metrics=$front.metrics_px
        layer_count=$layers.Count
        validation=@{reference_hash='pass';layer_images='pass';canvas_bounds='pass';uniform_part_aspect='pass';visual_preview='rejected: face identity, shading continuity and layer edges do not match the reference'}
        generated_inputs=@{
            master_sha256=(Get-FileHash -Algorithm SHA256 (Join-Path $out 'master-generated.png')).Hash.ToLowerInvariant()
            atlas_sha256=(Get-FileHash -Algorithm SHA256 (Join-Path $out 'parts-atlas.png')).Hash.ToLowerInvariant()
        }
        packaging='Uniform scale per isolated part; no nonuniform image stretching. Layout is an initial placement, not a measured reconstruction pass.'
        status='rejected material candidate; do not use for rigging or runtime replacement'
        runtime_model_updated=$false
    }
    Write-Utf8Lf (Join-Path $out 'material-report.json') ($report | ConvertTo-Json -Depth 12)
} finally { $graphics.Dispose(); $preview.Dispose(); $atlas.Dispose(); $master.Dispose() }
Write-Output "Prepared $($layers.Count) candidate layers in $out"
