# Split one coherent generated work-outfit master at its original coordinates.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$root = Split-Path $PSScriptRoot -Parent
$out = Join-Path $root 'assets/bina-live2d/source-work'
New-Item -ItemType Directory -Force (Join-Path $out 'parts') | Out-Null
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;

public sealed class WorkPart {
    public string name;
    public int left, top, width, height;
}
public static class BinaWorkLayers {
    public static WorkPart[] Build(string input, string output) {
        string[] names={"body","neck","face","back_hair","hair_left","hair_right","hair_front",
            "eye_left","eye_right","brow_left","brow_right","nose","mouth"};
        using(var source=new Bitmap(input)) using(var face=new GraphicsPath()) {
            if(source.Width!=1536 || source.Height!=1024) throw new Exception("Review landmarks for a changed master canvas.");
            face.AddPolygon(new PointF[]{new PointF(742,72),new PointF(752,74),new PointF(766,74),
                new PointF(782,71),new PointF(788,84),new PointF(794,104),new PointF(800,117),
                new PointF(794,139),new PointF(788,150),new PointF(779,164),new PointF(765,175),
                new PointF(747,164),new PointF(735,153),new PointF(727,140),new PointF(721,117),
                new PointF(725,99),new PointF(733,82)});
            var layers=new Dictionary<string,Bitmap>();
            var bounds=new Dictionary<string,Rectangle>();
            foreach(string name in names) { layers[name]=new Bitmap(source.Width,source.Height);bounds[name]=Rectangle.Empty; }
            try {
                for(int y=0;y<source.Height;y++) for(int x=0;x<source.Width;x++) {
                    Color color=source.GetPixel(x,y);if(color.A==0)continue;
                    string name="body";
                    if(y<192 && x>665 && x<865) {
                        if(y>=173 && x>=738 && x<=793) name="neck";
                        else if(face.IsVisible(x,y)) name="face";
                        else if(y>142 && color.R>color.B*1.25) name="back_hair";
                        else if(x<740 && y>64) name="hair_left";
                        else if(x>789 && y>64) name="hair_right";
                        else name="hair_front";
                        if(x>=723 && x<759 && y>=108 && y<130) name="eye_left";
                        if(x>=772 && x<810 && y>=108 && y<130) name="eye_right";
                        if(x>=724 && x<758 && y>=96 && y<107) name="brow_left";
                        if(x>=773 && x<807 && y>=96 && y<107) name="brow_right";
                        if(x>=759 && x<772 && y>=133 && y<146) name="nose";
                        if(x>=750 && x<781 && y>=147 && y<159) name="mouth";
                    }
                    layers[name].SetPixel(x,y,color);
                    var pixel=new Rectangle(x,y,1,1);
                    bounds[name]=bounds[name].IsEmpty?pixel:Rectangle.Union(bounds[name],pixel);
                }
                var result=new List<WorkPart>();
                foreach(string name in names) {
                    Rectangle rect=bounds[name];if(rect.IsEmpty)throw new Exception("Empty part: "+name);
                    using(var crop=layers[name].Clone(rect,PixelFormat.Format32bppArgb))
                        crop.Save(Path.Combine(output,name+".png"),ImageFormat.Png);
                    result.Add(new WorkPart{name=name,left=rect.Left,top=rect.Top,width=rect.Width,height=rect.Height});
                }
                return result.ToArray();
            } finally { foreach(var bitmap in layers.Values)bitmap.Dispose(); }
        }
    }
}
'@
$master = Join-Path $out 'standing-master-v1.png'
$parts = [BinaWorkLayers]::Build($master, (Join-Path $out 'parts'))
# The same character's hidden skin plate is reused behind the newly generated face.
Copy-Item (Join-Path $root 'assets/bina-live2d/source-registered/parts/skin_underpaint.png') (Join-Path $out 'parts/skin_underpaint.png') -Force
$tags = @{
    body=@('top'); neck=@('neck'); face=@('face'); back_hair=@('hair','back');
    hair_left=@('hair','right'); hair_right=@('hair','left'); hair_front=@('hair','front');
    eye_left=@('eye','white','right'); eye_right=@('eye','white','left');
    brow_left=@('brow','right'); brow_right=@('brow','left'); nose=@('nose'); mouth=@('face','detail')
}
$layers = @([ordered]@{
    id='skin_underpaint'; name='skin_underpaint'; tags=@('face','base')
    image=[ordered]@{path='parts/skin_underpaint.png';width=75;height=105}
    rect=[ordered]@{left=724;top=66;width=75;height=105}
})
foreach($part in $parts) {
    $layers += [ordered]@{
        id=$part.name; name=$part.name; tags=$tags[$part.name]
        image=[ordered]@{path="parts/$($part.name).png";width=$part.width;height=$part.height}
        rect=[ordered]@{left=$part.left;top=$part.top;width=$part.width;height=$part.height}
    }
}
$layout=[ordered]@{format='psd2live-layout';version=1;name='bina-work';canvas=@{width=1536;height=1024};layers=$layers}
$report=[ordered]@{
    source='standing-master-v1.png'; sha256=(Get-FileHash $master -Algorithm SHA256).Hash.ToLowerInvariant()
    method='Original-coordinate partition of one imagegen work-outfit master, with generated alpha retained.'
    layer_count=$layers.Count; body='Continuous standing body; independent arm gestures are not bound.'
    hidden_underpainting='Reused Bina skin plate, not visible replacement artwork.'
}
foreach($entry in @(@('bina.layout.json',$layout),@('material-report.json',$report))) {
    $json=$entry[1] | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText((Join-Path $out $entry[0]), ($json -replace "`r`n","`n")+"`n", [Text.UTF8Encoding]::new($false))
}
Write-Output "Prepared $($layers.Count) work-outfit layers from one coherent master."
